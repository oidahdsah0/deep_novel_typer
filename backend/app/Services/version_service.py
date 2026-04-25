from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from app.Services.chapter_service import ChapterService
from app.Services.document_service import DocumentService
from app.Services.project_service import ProjectService
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityNotFoundError
from app.Utils.locks import AsyncLockRegistry
from app.Schemas.common import VersionType, VersionedResourceType
from app.Schemas.versions import (
  ResourceVersion,
  ResourceVersionDetail,
  RestoreResourceVersionResponse,
  UpdateVersionSettingsRequest,
  VersionSettings,
)
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Utils.text import count_words


class VersionService:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
    locks: AsyncLockRegistry,
    project_service: ProjectService,
    chapter_service: ChapterService,
    document_service: DocumentService,
  ) -> None:
    self._db = db
    self._store = store
    self._paths = paths
    self._locks = locks
    self._project_service = project_service
    self._chapter_service = chapter_service
    self._document_service = document_service

  async def get_settings(self) -> VersionSettings:
    row = await self._db.fetch_one(
      """
      SELECT auto_enabled, auto_interval_minutes, auto_min_chars_changed,
             auto_min_change_ratio, updated_at
      FROM version_settings
      WHERE id = 1
      """
    )
    if row is None:
      now = _now()
      await self._db.execute(
        """
        INSERT INTO version_settings (
          id, auto_enabled, auto_interval_minutes, auto_min_chars_changed,
          auto_min_change_ratio, updated_at
        )
        VALUES (1, 1, 10, 300, 0.15, ?)
        """,
        (now,),
      )
      return VersionSettings(updated_at=now)
    return _settings_from_row(row)

  async def update_settings(self, request: UpdateVersionSettingsRequest) -> VersionSettings:
    current = await self.get_settings()
    updated = current.model_copy(
      update={
        key: value
        for key, value in request.model_dump(exclude_unset=True).items()
        if value is not None
      }
    )
    now = _now()
    await self._db.execute(
      """
      INSERT INTO version_settings (
        id, auto_enabled, auto_interval_minutes, auto_min_chars_changed,
        auto_min_change_ratio, updated_at
      )
      VALUES (1, ?, ?, ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET
        auto_enabled = excluded.auto_enabled,
        auto_interval_minutes = excluded.auto_interval_minutes,
        auto_min_chars_changed = excluded.auto_min_chars_changed,
        auto_min_change_ratio = excluded.auto_min_change_ratio,
        updated_at = excluded.updated_at
      """,
      (
        int(updated.auto_enabled),
        updated.auto_interval_minutes,
        updated.auto_min_chars_changed,
        updated.auto_min_change_ratio,
        now,
      ),
    )
    return updated.model_copy(update={"updated_at": now})

  async def list_versions(
    self,
    project_id: str,
    resource_type: VersionedResourceType,
    resource_id: str,
  ) -> list[ResourceVersion]:
    await self._project_service.get_manifest(project_id)
    rows = await self._db.fetch_all(
      """
      SELECT id, project_id, resource_type, resource_id, resource_title,
             version_type, label, note, word_count, char_count, created_at
      FROM resource_versions
      WHERE project_id = ? AND resource_type = ? AND resource_id = ?
      ORDER BY created_at DESC
      """,
      (project_id, resource_type, resource_id),
    )
    return [_version_from_row(row) for row in rows]

  async def get_version(self, project_id: str, version_id: str) -> ResourceVersionDetail:
    row = await self._version_row(project_id, version_id)
    path = self._paths.project(project_id).root / str(row["file_path"])
    if not await self._store.exists(path):
      raise EntityNotFoundError(f"Version file not found: {version_id}")
    return ResourceVersionDetail(
      **_version_from_row(row).model_dump(mode="json"),
      content=await self._store.read_text(path),
    )

  async def create_current_version(
    self,
    project_id: str,
    resource_type: VersionedResourceType,
    resource_id: str,
    version_type: VersionType = "manual",
    label: str | None = None,
    note: str = "",
  ) -> ResourceVersion:
    title, content, _updated_at = await self._current_resource(
      project_id, resource_type, resource_id
    )
    async with self._locks.get(f"{project_id}:versions:{resource_type}:{resource_id}"):
      return await self._write_version(
        project_id=project_id,
        resource_type=resource_type,
        resource_id=resource_id,
        title=title,
        content=content,
        version_type=version_type,
        label=label,
        note=note,
      )

  async def maybe_create_auto_version(
    self,
    project_id: str,
    resource_type: VersionedResourceType,
    resource_id: str,
    title: str,
    content: str,
  ) -> ResourceVersion | None:
    settings = await self.get_settings()
    if not settings.auto_enabled:
      return None

    async with self._locks.get(f"{project_id}:versions:{resource_type}:{resource_id}"):
      latest = await self._latest_version_row(project_id, resource_type, resource_id)
      content_hash = _content_hash(content)
      if latest is not None:
        if latest["content_hash"] == content_hash:
          return None
        created_at = _parse_datetime(str(latest["created_at"]))
        minutes_since_last = (_datetime_now() - created_at).total_seconds() / 60
        if minutes_since_last < settings.auto_interval_minutes:
          return None

        previous_path = self._paths.project(project_id).root / str(latest["file_path"])
        previous_content = (
          await self._store.read_text(previous_path)
          if await self._store.exists(previous_path)
          else ""
        )
        changed_chars = _changed_chars(previous_content, content)
        change_ratio = changed_chars / max(len(previous_content), len(content), 1)
        if (
          changed_chars < settings.auto_min_chars_changed
          and change_ratio < settings.auto_min_change_ratio
        ):
          return None

      return await self._write_version(
        project_id=project_id,
        resource_type=resource_type,
        resource_id=resource_id,
        title=title,
        content=content,
        version_type="auto",
        label="自动版本",
        note="",
      )

  async def restore_version(
    self, project_id: str, version_id: str
  ) -> RestoreResourceVersionResponse:
    version = await self.get_version(project_id, version_id)
    await self.create_current_version(
      project_id,
      version.resource_type,
      version.resource_id,
      version_type="pre_restore",
      label="恢复前备份",
      note=f"恢复版本 {version.id} 前自动保存。",
    )
    if version.resource_type == "chapter":
      restored = await self._chapter_service.update_chapter(
        project_id, version.resource_id, version.content
      )
      return RestoreResourceVersionResponse(
        resource_type="chapter",
        resource_id=restored.id,
        title=restored.title,
        content=restored.content,
        word_count=restored.word_count,
        updated_at=restored.updated_at,
      )

    restored_document = await self._document_service.update_document(
      project_id, version.resource_id, version.content
    )
    return RestoreResourceVersionResponse(
      resource_type="document",
      resource_id=restored_document.id,
      title=restored_document.title,
      content=restored_document.content,
      word_count=count_words(restored_document.content),
      updated_at=restored_document.updated_at,
    )

  async def _current_resource(
    self,
    project_id: str,
    resource_type: VersionedResourceType,
    resource_id: str,
  ) -> tuple[str, str, str]:
    if resource_type == "chapter":
      chapter = await self._chapter_service.get_chapter(project_id, resource_id)
      return chapter.title, chapter.content, chapter.updated_at

    document = await self._document_service.get_document(project_id, resource_id)
    return document.title, document.content, document.updated_at

  async def _write_version(
    self,
    *,
    project_id: str,
    resource_type: VersionedResourceType,
    resource_id: str,
    title: str,
    content: str,
    version_type: VersionType,
    label: str | None,
    note: str,
  ) -> ResourceVersion:
    await self._project_service.get_manifest(project_id)
    now = _now()
    version_id = _version_id(resource_type, now)
    file_path = _version_file_path(resource_type, resource_id, version_id)
    await self._store.write_text(self._paths.project(project_id).root / file_path, content)
    version = ResourceVersion(
      id=version_id,
      project_id=project_id,
      resource_type=resource_type,
      resource_id=resource_id,
      resource_title=title,
      version_type=version_type,
      label=label,
      note=note,
      word_count=count_words(content),
      char_count=len(content),
      created_at=now,
    )
    await self._db.execute(
      """
      INSERT INTO resource_versions (
        id, project_id, resource_type, resource_id, resource_title,
        version_type, label, note, file_path, content_hash,
        word_count, char_count, created_at
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """,
      (
        version.id,
        version.project_id,
        version.resource_type,
        version.resource_id,
        version.resource_title,
        version.version_type,
        version.label,
        version.note,
        file_path,
        _content_hash(content),
        version.word_count,
        version.char_count,
        version.created_at,
      ),
    )
    return version

  async def _latest_version_row(
    self,
    project_id: str,
    resource_type: VersionedResourceType,
    resource_id: str,
  ) -> dict[str, object] | None:
    return await self._db.fetch_one(
      """
      SELECT id, file_path, content_hash, created_at
      FROM resource_versions
      WHERE project_id = ? AND resource_type = ? AND resource_id = ?
      ORDER BY created_at DESC
      LIMIT 1
      """,
      (project_id, resource_type, resource_id),
    )

  async def _version_row(self, project_id: str, version_id: str) -> dict[str, object]:
    row = await self._db.fetch_one(
      """
      SELECT id, project_id, resource_type, resource_id, resource_title,
             version_type, label, note, file_path, content_hash,
             word_count, char_count, created_at
      FROM resource_versions
      WHERE project_id = ? AND id = ?
      """,
      (project_id, version_id),
    )
    if row is None:
      raise EntityNotFoundError(f"Version not found: {version_id}")
    return row


def _settings_from_row(row: dict[str, object]) -> VersionSettings:
  return VersionSettings(
    auto_enabled=bool(row["auto_enabled"]),
    auto_interval_minutes=int(row["auto_interval_minutes"]),
    auto_min_chars_changed=int(row["auto_min_chars_changed"]),
    auto_min_change_ratio=float(row["auto_min_change_ratio"]),
    updated_at=str(row["updated_at"]),
  )


def _version_from_row(row: dict[str, object]) -> ResourceVersion:
  return ResourceVersion(
    id=str(row["id"]),
    project_id=str(row["project_id"]),
    resource_type=row["resource_type"],  # type: ignore[arg-type]
    resource_id=str(row["resource_id"]),
    resource_title=str(row["resource_title"]),
    version_type=row["version_type"],  # type: ignore[arg-type]
    label=row["label"],  # type: ignore[arg-type]
    note=str(row["note"] or ""),
    word_count=int(row["word_count"] or 0),
    char_count=int(row["char_count"] or 0),
    created_at=str(row["created_at"]),
  )


def _version_id(resource_type: VersionedResourceType, now: str) -> str:
  prefix = "chv" if resource_type == "chapter" else "docv"
  return f"{prefix}-{_safe_timestamp(now)}-{uuid4().hex[:8]}"


def _version_file_path(
  resource_type: VersionedResourceType, resource_id: str, version_id: str
) -> str:
  folder = "chapters" if resource_type == "chapter" else "documents"
  return f"versions/{folder}/{resource_id}/{version_id}.md"


def _content_hash(content: str) -> str:
  return sha256(content.encode("utf-8")).hexdigest()


def _changed_chars(previous: str, current: str) -> int:
  prefix = 0
  max_prefix = min(len(previous), len(current))
  while prefix < max_prefix and previous[prefix] == current[prefix]:
    prefix += 1

  suffix = 0
  max_suffix = max_prefix - prefix
  while (
    suffix < max_suffix
    and previous[len(previous) - suffix - 1] == current[len(current) - suffix - 1]
  ):
    suffix += 1

  return max(len(previous) - prefix - suffix, len(current) - prefix - suffix)


def _parse_datetime(value: str) -> datetime:
  return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _datetime_now() -> datetime:
  return datetime.now(tz=UTC)


def _now() -> str:
  return _datetime_now().isoformat()


def _safe_timestamp(value: str) -> str:
  return value.replace(":", "").replace(".", "").replace("+", "-")
