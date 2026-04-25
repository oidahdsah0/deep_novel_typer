from __future__ import annotations

from datetime import UTC, datetime

from app.Schemas.common import PromptRequestType
from app.Schemas.prompt_preview import PromptPreviewProfileOverride
from app.Schemas.prompt_profiles import (
  PromptProfile,
  PromptProfileLibrary,
  PromptProfileVersion,
  PromptProfileVersionDetail,
  RestorePromptProfileVersionResponse,
  UpdatePromptProfileRequest,
)
from app.Services.chapter_service import ChapterService
from app.Services.document_service import DocumentService
from app.Services.project_service import ProjectService
from app.Services.api_configs.repository import APIConfigRepository
from app.Services.prompt_profiles.config import (
  REQUEST_API_CONFIG_ID_KEY,
  api_config_id_from_config,
  include_chapter_synopsis_from_config,
  normalize_temperature_in_config,
  temperature_from_config,
)
from app.Services.prompt_profiles.contracts import (
  normalize_output_contract,
  normalize_prompt_template,
  output_contract,
)
from app.Services.prompt_profiles.context_builder import PromptContextBuilder
from app.Services.prompt_profiles.context_formatting import (
  render_agent_blocks,
  render_context_pack,
  render_material_blocks,
)
from app.Services.prompt_profiles.defaults import DEFAULT_PROFILES, REQUEST_TYPES
from app.Services.prompt_profiles.materials import PromptMaterialRenderer, material_limits
from app.Services.prompt_profiles.rendering import (
  PromptProfileBuildResult,
  apply_profile_override,
  clean_id_list,
  format_runtime_value,
  render_template,
)
from app.Services.prompt_profiles.repository import PromptProfileRepository
from app.Services.prompt_profiles.versions import (
  profile_from_default,
  profile_from_row,
  profile_from_snapshot,
)
from app.Utils.db import AsyncDatabase
from app.Utils.errors import DomainError, EntityNotFoundError
from app.Utils.llm import LLMMessage
from app.Utils.locks import AsyncLockRegistry


class PromptProfileService:
  def __init__(
    self,
    db: AsyncDatabase,
    locks: AsyncLockRegistry,
    project_service: ProjectService,
    chapter_service: ChapterService,
    document_service: DocumentService,
  ) -> None:
    self._locks = locks
    self._project_service = project_service
    self._repository = PromptProfileRepository(db)
    self._api_configs = APIConfigRepository(db)
    self._materials = PromptMaterialRenderer(chapter_service, document_service)
    self._context_builder = PromptContextBuilder(project_service)

  async def list_profiles(self, project_id: str) -> PromptProfileLibrary:
    await self._project_service.get_manifest(project_id)
    rows = await self._repository.list_profile_rows(project_id)
    overrides = {str(row["request_type"]): row for row in rows}
    return PromptProfileLibrary(
      profiles=[
        profile_from_row(overrides[request_type])
        if request_type in overrides
        else profile_from_default(DEFAULT_PROFILES[request_type])
        for request_type in REQUEST_TYPES
      ]
    )

  async def get_profile(
    self, project_id: str, request_type: PromptRequestType
  ) -> PromptProfile:
    await self._project_service.get_manifest(project_id)
    row = await self._repository.fetch_profile_row(project_id, request_type)
    if row is not None:
      return profile_from_row(row)
    default = DEFAULT_PROFILES.get(request_type)
    if default is None:
      raise EntityNotFoundError(f"Prompt profile not found: {request_type}")
    return profile_from_default(default)

  async def request_api_config_id(
    self, project_id: str, request_type: PromptRequestType
  ) -> str | None:
    profile = await self.get_profile(project_id, request_type)
    return api_config_id_from_config(profile.config)

  async def request_temperature(
    self, project_id: str, request_type: PromptRequestType
  ) -> float | None:
    profile = await self.get_profile(project_id, request_type)
    return temperature_from_config(profile.config)

  async def update_profile(
    self,
    project_id: str,
    request_type: PromptRequestType,
    request: UpdatePromptProfileRequest,
  ) -> PromptProfile:
    await self._project_service.get_manifest(project_id)
    current = await self.get_profile(project_id, request_type)
    next_config = (
      await self._normalize_config(request.config)
      if request.config is not None
      else current.config
    )
    now = _now()
    next_profile = PromptProfile(
      request_type=request_type,
      name=request.name if request.name is not None else current.name,
      system_template=normalize_prompt_template(
        request_type,
        request.system_template
        if request.system_template is not None
        else current.system_template,
      ),
      user_template=normalize_prompt_template(
        request_type,
        request.user_template if request.user_template is not None else current.user_template,
      ),
      output_contract=(
        normalize_output_contract(
          request_type,
          request.output_contract
          if request.output_contract is not None
          else current.output_contract or output_contract(request_type),
        )
      ),
      chapter_ids=(
        clean_id_list(request.chapter_ids)
        if request.chapter_ids is not None
        else current.chapter_ids
      ),
      document_ids=(
        clean_id_list(request.document_ids)
        if request.document_ids is not None
        else current.document_ids
      ),
      config=next_config,
      is_system=False,
      created_at=current.created_at or now,
      updated_at=now,
    )

    async with self._locks.get(f"{project_id}:prompt-profiles"):
      async with self._repository.transaction() as conn:
        if not await self._repository.has_versions(conn, project_id, request_type):
          await self._repository.create_version(
            conn,
            project_id,
            current,
            "initial",
            label="初始配置",
            note="首次保存前的有效请求配置。",
            created_at=_now(),
          )
        await self._repository.save_profile(conn, project_id, next_profile, now=now)
        await self._repository.create_version(
          conn,
          project_id,
          next_profile,
          "manual",
          label=next_profile.name,
          note="用户保存请求配置。",
          created_at=_now(),
        )
    return await self.get_profile(project_id, request_type)

  async def _normalize_config(self, config: dict[str, object]) -> dict[str, object]:
    try:
      normalized = normalize_temperature_in_config(config)
    except ValueError as exc:
      raise DomainError("Temperature must be a number between 0 and 2.") from exc
    return await self._normalize_config_api_reference(normalized)

  async def _normalize_config_api_reference(self, config: dict[str, object]) -> dict[str, object]:
    normalized = dict(config)
    if REQUEST_API_CONFIG_ID_KEY not in normalized:
      return normalized
    config_id = api_config_id_from_config(normalized)
    if config_id is None:
      normalized.pop(REQUEST_API_CONFIG_ID_KEY, None)
      return normalized
    if await self._api_configs.fetch_config_row(config_id, "llm") is None:
      raise EntityNotFoundError(f"LLM API config not found: {config_id}")
    normalized[REQUEST_API_CONFIG_ID_KEY] = config_id
    return normalized

  async def list_versions(
    self, project_id: str, request_type: PromptRequestType
  ) -> list[PromptProfileVersion]:
    await self._project_service.get_manifest(project_id)
    return await self._repository.list_versions(project_id, request_type)

  async def get_version(
    self,
    project_id: str,
    request_type: PromptRequestType,
    version_id: str,
  ) -> PromptProfileVersionDetail:
    await self._project_service.get_manifest(project_id)
    return await self._repository.get_version(project_id, request_type, version_id)

  async def restore_version(
    self,
    project_id: str,
    request_type: PromptRequestType,
    version_id: str,
  ) -> RestorePromptProfileVersionResponse:
    version = await self.get_version(project_id, request_type, version_id)
    current = await self.get_profile(project_id, request_type)
    now = _now()
    restored_profile = profile_from_snapshot(
      request_type,
      version.snapshot,
      created_at=current.created_at or now,
      updated_at=now,
    )

    async with self._locks.get(f"{project_id}:prompt-profiles"):
      async with self._repository.transaction() as conn:
        await self._repository.create_version(
          conn,
          project_id,
          current,
          "pre_restore",
          label="恢复前备份",
          note=f"恢复到版本 {version.id} 前自动保存。",
          created_at=_now(),
        )
        await self._repository.save_profile(conn, project_id, restored_profile, now=now)

    return RestorePromptProfileVersionResponse(
      profile=await self.get_profile(project_id, request_type),
      version=version,
    )

  async def build_messages(
    self,
    project_id: str,
    request_type: PromptRequestType,
    runtime_input: dict[str, object],
  ) -> list[LLMMessage]:
    return (
      await self.build_preview(
        project_id,
        request_type,
        runtime_input,
      )
    ).messages

  async def build_preview(
    self,
    project_id: str,
    request_type: PromptRequestType,
    runtime_input: dict[str, object],
    profile_override: PromptPreviewProfileOverride | None = None,
  ) -> PromptProfileBuildResult:
    profile = await self.get_profile(project_id, request_type)
    if profile_override is not None:
      profile = apply_profile_override(profile, profile_override)
    max_item_chars, max_total_chars = material_limits(profile.config)
    effective_runtime_input = _runtime_input_for_profile(profile.config, runtime_input)
    input_values = {
      key: format_runtime_value(value)
      for key, value in effective_runtime_input.items()
      if key not in {"chapters", "textures"}
    }
    chapter_refs = await self._materials.resolve_chapter_refs(
      project_id, profile, effective_runtime_input
    )
    chapter_result = await self._materials.render_chapters(
      project_id,
      chapter_refs,
      max_item_chars=max_item_chars,
      max_total_chars=max_total_chars,
    )
    document_result = await self._materials.render_documents(
      project_id,
      profile.document_ids,
      max_item_chars=max_item_chars,
      max_total_chars=max_total_chars,
    )
    context_pack = await self._context_builder.build(
      project_id=project_id,
      request_type=request_type,
      runtime_input=effective_runtime_input,
      materials=[*chapter_result.blocks, *document_result.blocks],
    )
    input_values["chapters"] = chapter_result.text
    input_values["textures"] = document_result.text
    input_values["documents"] = document_result.text
    input_values["materials"] = render_material_blocks(context_pack.materials)
    input_values["context_pack"] = render_context_pack(context_pack)
    input_values["agents"] = render_agent_blocks(context_pack.agents)
    input_values["project"] = format_runtime_value(context_pack.project)
    messages = [
      LLMMessage(
        role="system",
        content="\n\n".join(
          part
          for part in [
            render_template(profile.system_template, input_values).strip(),
            render_template(
              profile.output_contract or output_contract(request_type), input_values
            ).strip(),
          ]
          if part
        ).strip(),
      ),
      LLMMessage(
        role="user",
        content=render_template(profile.user_template, input_values).strip(),
      ),
    ]
    return PromptProfileBuildResult(
      messages=messages,
      chapters=chapter_result.preview,
      documents=document_result.preview,
      context_pack=context_pack,
    )


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()


def _runtime_input_for_profile(
  config: dict[str, object],
  runtime_input: dict[str, object],
) -> dict[str, object]:
  effective = dict(runtime_input)
  if not include_chapter_synopsis_from_config(config):
    effective.pop("chapter_synopsis", None)
  return effective
