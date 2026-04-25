from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.Schemas.common import GenerationPresetKind
from app.Schemas.generation import (
  CreateGenerationPresetRequest,
  GenerationPreset,
  GenerationPresetLibrary,
  UpdateGenerationPresetRequest,
)
from app.Services.project_service import ProjectService
from app.Utils.config import GenerationPresetDefault
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityNotFoundError
from app.Utils.ids import slugify
from app.Utils.locks import AsyncLockRegistry


@dataclass(frozen=True)
class _PresetKey:
  kind: GenerationPresetKind
  preset_id: str


class GenerationPresetResolver:
  def __init__(
    self,
    db: AsyncDatabase,
    locks: AsyncLockRegistry,
    project_service: ProjectService,
    defaults: tuple[GenerationPresetDefault, ...],
  ) -> None:
    self._db = db
    self._locks = locks
    self._project_service = project_service
    self._defaults = defaults

  async def list_presets(self, project_id: str) -> GenerationPresetLibrary:
    await self._project_service.get_manifest(project_id)
    rows = await self._db.fetch_all(
      """
      SELECT project_id, kind, preset_id, name, content, is_system, is_hidden, created_at, updated_at
      FROM generation_presets
      WHERE project_id = ?
      ORDER BY kind ASC, is_system DESC, updated_at ASC, name ASC
      """,
      (project_id,),
    )
    overrides = {
      _PresetKey(kind=row["kind"], preset_id=str(row["preset_id"])): row  # type: ignore[arg-type]
      for row in rows
    }

    presets: list[GenerationPreset] = []
    for default in self._defaults:
      key = _PresetKey(kind=default.kind, preset_id=default.preset_id)  # type: ignore[arg-type]
      row = overrides.pop(key, None)
      if row is not None and bool(row["is_hidden"]):
        continue
      presets.append(_preset_from_default(default, row))

    for row in overrides.values():
      if bool(row["is_hidden"]):
        continue
      presets.append(_preset_from_row(row))

    return _library_from_presets(presets)

  async def create_preset(
    self, project_id: str, request: CreateGenerationPresetRequest
  ) -> GenerationPreset:
    await self._project_service.get_manifest(project_id)
    now = _now()
    async with self._locks.get(f"{project_id}:generation-presets"):
      preset_id = await self._next_preset_id(project_id, request.kind, request.name)
      await self._db.execute(
        """
        INSERT INTO generation_presets (
          project_id, kind, preset_id, name, content, is_system, is_hidden, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)
        """,
        (
          project_id,
          request.kind,
          preset_id,
          request.name,
          normalize_preset_content(request.kind, request.content),
          now,
          now,
        ),
      )
    return await self.require_preset(project_id, request.kind, preset_id)

  async def update_preset(
    self,
    project_id: str,
    kind: GenerationPresetKind,
    preset_id: str,
    request: UpdateGenerationPresetRequest,
  ) -> GenerationPreset:
    await self._project_service.get_manifest(project_id)
    now = _now()
    async with self._locks.get(f"{project_id}:generation-presets"):
      row = await self._fetch_preset_row(project_id, kind, preset_id)
      default = self._default_for(kind, preset_id)
      if row is None and default is None:
        raise EntityNotFoundError(f"Generation preset not found: {preset_id}")

      current_name = str(row["name"]) if row else default.name
      current_content = str(row["content"]) if row else default.content
      next_name = request.name if request.name is not None else current_name
      next_content = normalize_preset_content(
        kind, request.content if request.content is not None else current_content
      )
      is_system = bool(row["is_system"]) if row else default is not None
      created_at = str(row["created_at"]) if row else now

      await self._db.execute(
        """
        INSERT INTO generation_presets (
          project_id, kind, preset_id, name, content, is_system, is_hidden, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
        ON CONFLICT(project_id, kind, preset_id) DO UPDATE SET
          name = excluded.name,
          content = excluded.content,
          is_hidden = 0,
          updated_at = excluded.updated_at
        """,
        (
          project_id,
          kind,
          preset_id,
          next_name,
          next_content,
          int(is_system),
          created_at,
          now,
        ),
      )
    return await self.require_preset(project_id, kind, preset_id)

  async def delete_preset(
    self, project_id: str, kind: GenerationPresetKind, preset_id: str
  ) -> None:
    await self._project_service.get_manifest(project_id)
    now = _now()
    async with self._locks.get(f"{project_id}:generation-presets"):
      row = await self._fetch_preset_row(project_id, kind, preset_id)
      default = self._default_for(kind, preset_id)
      if row is None and default is None:
        raise EntityNotFoundError(f"Generation preset not found: {preset_id}")
      if default is not None:
        name = str(row["name"]) if row else default.name
        content = str(row["content"]) if row else default.content
        created_at = str(row["created_at"]) if row else now
        await self._db.execute(
          """
          INSERT INTO generation_presets (
            project_id, kind, preset_id, name, content, is_system, is_hidden, created_at, updated_at
          )
          VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)
          ON CONFLICT(project_id, kind, preset_id) DO UPDATE SET
            is_hidden = 1,
            updated_at = excluded.updated_at
          """,
          (project_id, kind, preset_id, name, content, created_at, now),
        )
      else:
        await self._db.execute(
          "DELETE FROM generation_presets WHERE project_id = ? AND kind = ? AND preset_id = ?",
          (project_id, kind, preset_id),
        )

  async def require_preset(
    self, project_id: str, kind: GenerationPresetKind, preset_id: str
  ) -> GenerationPreset:
    row = await self._fetch_preset_row(project_id, kind, preset_id)
    default = self._default_for(kind, preset_id)
    if row is None and default is None:
      raise EntityNotFoundError(f"Generation preset not found: {preset_id}")
    if row is not None:
      return _preset_from_row(row)
    assert default is not None
    return _preset_from_default(default)

  async def _next_preset_id(
    self, project_id: str, kind: GenerationPresetKind, name: str
  ) -> str:
    base_id = slugify(name, fallback_prefix="preset")
    existing = {
      str(row["preset_id"])
      for row in await self._db.fetch_all(
        "SELECT preset_id FROM generation_presets WHERE project_id = ? AND kind = ?",
        (project_id, kind),
      )
    }
    existing.update(
      default.preset_id for default in self._defaults if default.kind == kind
    )
    if base_id not in existing:
      return base_id
    index = 2
    while f"{base_id}-{index}" in existing:
      index += 1
    return f"{base_id}-{index}"

  async def _fetch_preset_row(
    self, project_id: str, kind: GenerationPresetKind, preset_id: str
  ) -> dict[str, object] | None:
    return await self._db.fetch_one(
      """
      SELECT project_id, kind, preset_id, name, content, is_system, is_hidden, created_at, updated_at
      FROM generation_presets
      WHERE project_id = ? AND kind = ? AND preset_id = ?
      """,
      (project_id, kind, preset_id),
    )

  def _default_for(
    self, kind: GenerationPresetKind, preset_id: str
  ) -> GenerationPresetDefault | None:
    return next(
      (
        default
        for default in self._defaults
        if default.kind == kind and default.preset_id == preset_id
      ),
      None,
    )


def _library_from_presets(presets: list[GenerationPreset]) -> GenerationPresetLibrary:
  return GenerationPresetLibrary(
    writing_modes=[preset for preset in presets if preset.kind == "writing_mode"],
    quick_generation_modes=[
      preset for preset in presets if preset.kind == "quick_generation_mode"
    ],
    chapter_blueprint_modes=[
      preset for preset in presets if preset.kind == "chapter_blueprint_mode"
    ],
    author_personas=[preset for preset in presets if preset.kind == "author_persona"],
    polish_modes=[preset for preset in presets if preset.kind == "polish_mode"],
    document_polish_modes=[
      preset for preset in presets if preset.kind == "document_polish_mode"
    ],
    document_generation_modes=[
      preset for preset in presets if preset.kind == "document_generation_mode"
    ],
    editor_personas=[preset for preset in presets if preset.kind == "editor_persona"],
  )


def _preset_from_default(
  default: GenerationPresetDefault, row: dict[str, object] | None = None
) -> GenerationPreset:
  kind = default.kind  # type: ignore[assignment]
  return GenerationPreset(
    id=default.preset_id,
    kind=kind,  # type: ignore[arg-type]
    name=str(row["name"]) if row else default.name,
    content=normalize_preset_content(kind, str(row["content"]) if row else default.content),
    is_system=True,
    is_hidden=bool(row["is_hidden"]) if row else False,
    created_at=str(row["created_at"]) if row else None,
    updated_at=str(row["updated_at"]) if row else None,
  )


def _preset_from_row(row: dict[str, object]) -> GenerationPreset:
  kind = row["kind"]  # type: ignore[assignment]
  return GenerationPreset(
    id=str(row["preset_id"]),
    kind=kind,  # type: ignore[arg-type]
    name=str(row["name"]),
    content=normalize_preset_content(kind, str(row["content"])),
    is_system=bool(row["is_system"]),
    is_hidden=bool(row["is_hidden"]),
    created_at=str(row["created_at"]),
    updated_at=str(row["updated_at"]),
  )


def normalize_preset_content(kind: GenerationPresetKind, content: str) -> str:
  if kind == "polish_mode":
    return (
      content.replace(
        "不要解释修改理由，只输出润色后的文本。",
        "不要解释修改理由；最终 JSON 的 text 字段只包含润色后的文本。",
      )
      .replace("只输出润色后的文本。", "最终 JSON 的 text 字段只包含润色后的文本。")
      .replace("只输出润色后的文本", "最终 JSON 的 text 字段只包含润色后的文本")
    )
  if kind == "author_persona":
    return content.replace(
      "不输出分析、不输出标题、不解释创作意图。",
      "最终 JSON 的 text 字段里不包含分析、标题或创作意图解释。",
    )
  if kind == "editor_persona":
    return content.replace(
      "不输出分析、不输出标题、不解释创作意图。",
      "最终 JSON 的 text 字段里不包含分析、标题或创作意图解释。",
    )
  return content


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()
