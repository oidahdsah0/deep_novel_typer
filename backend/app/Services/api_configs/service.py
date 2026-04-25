from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from app.Schemas.api_configs import (
  API_CONFIG_DEFAULT_CONTEXT_WINDOW_TOKENS,
  APIConfig,
  APIConfigHealthCheckResult,
  APIConfigTemplate,
  CreateAPIConfigRequest,
  UpdateAPIConfigRequest,
)
from app.Schemas.common import APIConfigKind
from app.Services.api_configs.health import (
  APIConfigHealthChecker,
  OpenAIAPIConfigHealthChecker,
  health_result,
  is_configured,
)
from app.Services.api_configs.repository import APIConfigRepository, config_from_row
from app.Services.api_configs.runtime import EffectiveAPIConfig
from app.Services.api_configs.templates import API_CONFIG_TEMPLATES
from app.Services.prompt_profiles.repository import PromptProfileRepository
from app.Utils.config import LLMSettings
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityConflictError
from app.Utils.ids import slugify
from app.Utils.locks import AsyncLockRegistry


class APIConfigService:
  def __init__(
    self,
    db: AsyncDatabase,
    locks: AsyncLockRegistry,
    defaults: LLMSettings,
    health_checker: APIConfigHealthChecker | None = None,
  ) -> None:
    self._db = db
    self._locks = locks
    self._defaults = defaults
    self._repository = APIConfigRepository(db)
    self._prompt_profiles = PromptProfileRepository(db)
    self._health_checker = health_checker or OpenAIAPIConfigHealthChecker(
      headers=defaults.headers,
      timeout_seconds=defaults.timeout_seconds,
    )

  async def ensure_default_config(self) -> None:
    if await self._repository.count_by_kind("llm") > 0:
      return

    default_config = _request_from_defaults(self._defaults)
    async with self._locks.get("api-configs"):
      if await self._repository.count_by_kind("llm") > 0:
        return
      await self._repository.insert_config(
        "default-api",
        default_config,
        api_key=None,
        is_default=True,
        now=_now(),
      )

  def list_templates(self) -> list[APIConfigTemplate]:
    return list(API_CONFIG_TEMPLATES)

  async def list_configs(self, kind: APIConfigKind | None = None) -> list[APIConfig]:
    return await self._repository.list_configs(kind)

  async def get_effective_config(
    self, config_id: str | None, kind: APIConfigKind = "llm"
  ) -> EffectiveAPIConfig | None:
    row = await self._repository.fetch_config_row(config_id, kind)
    if row is None:
      return None
    return EffectiveAPIConfig(config=config_from_row(row), api_key=str(row["api_key"] or ""))

  async def health_check(self, config_id: str) -> APIConfigHealthCheckResult:
    row = await self._repository.require_config_row(config_id)
    effective_config = EffectiveAPIConfig(
      config=config_from_row(row),
      api_key=str(row["api_key"] or ""),
    )
    if not is_configured(effective_config):
      return health_result(
        effective_config,
        ok=False,
        error_code="missing_required_config",
        error_message="该配置缺少必需的 API Key、Endpoint 或模型名。",
      )
    if effective_config.config.kind == "embedding":
      return await self._health_checker.check_embedding(effective_config)
    return await self._health_checker.check_llm(effective_config)

  async def shutdown(self) -> None:
    shutdown = getattr(self._health_checker, "shutdown", None)
    if callable(shutdown):
      await shutdown()

  async def create_config(self, request: CreateAPIConfigRequest) -> APIConfig:
    config_id = slugify(request.name, fallback_prefix="api-config")
    async with self._locks.get("api-configs"):
      if await self._repository.config_exists(config_id):
        raise EntityConflictError(f"API config already exists: {config_id}")
      is_default = request.is_default or not await self._repository.has_configs(request.kind)
      await self._repository.insert_config(
        config_id,
        request,
        api_key=_api_key_from_request(request.api_key),
        is_default=is_default,
        now=_now(),
      )
    return config_from_row(await self._repository.require_config_row(config_id))

  async def update_config(self, config_id: str, request: UpdateAPIConfigRequest) -> APIConfig:
    async with self._locks.get("api-configs"):
      current = await self._repository.require_config_row(config_id)
      current_kind = cast(APIConfigKind, current["kind"])
      if request.kind != current_kind:
        raise EntityConflictError("API config kind cannot be changed after creation")
      await self._ensure_update_keeps_perspective_links_valid(config_id, request)
      await self._repository.update_config(
        config_id,
        request,
        api_key=_next_api_key(current, request),
        is_default=request.is_default or bool(current["is_default"]),
        now=_now(),
      )
    return config_from_row(await self._repository.require_config_row(config_id))

  async def delete_config(self, config_id: str) -> None:
    async with self._locks.get("api-configs"):
      current = await self._repository.require_config_row(config_id)
      current_kind = cast(APIConfigKind, current["kind"])
      if await self._repository.perspective_link_count(config_id) > 0:
        raise EntityConflictError("API config is still used by perspectives")

      if await self._repository.count_by_kind(current_kind) <= 1:
        raise EntityConflictError("Cannot delete the last API config of this type")

      now = _now()
      async with self._db.transaction() as conn:
        await self._prompt_profiles.clear_api_config_references(conn, config_id, now=now)
        await self._repository.delete_config_with_connection(
          conn,
          config_id,
          kind=current_kind,
          was_default=bool(current["is_default"]),
          now=now,
        )

  async def set_default(self, config_id: str) -> APIConfig:
    async with self._locks.get("api-configs"):
      current = await self._repository.require_config_row(config_id)
      await self._repository.set_default(
        config_id,
        kind=current["kind"],  # type: ignore[arg-type]
        now=_now(),
      )
    return config_from_row(await self._repository.require_config_row(config_id))

  async def _ensure_update_keeps_perspective_links_valid(
    self, config_id: str, request: UpdateAPIConfigRequest
  ) -> None:
    if request.kind == "llm":
      return
    if await self._repository.perspective_link_count(config_id) > 0:
      raise EntityConflictError("API config is still used by perspectives")


def _request_from_defaults(defaults: LLMSettings) -> CreateAPIConfigRequest:
  options = defaults.request_options
  thinking = options.get("thinking")
  thinking_enabled = (
    isinstance(thinking, dict) and str(thinking.get("type") or "").lower() == "enabled"
  )
  reasoning_effort = str(options.get("reasoning_effort") or "high")
  if reasoning_effort not in {"high", "max"}:
    reasoning_effort = "high"

  max_tokens = int(options.get("max_tokens") or 4096)
  temperature = options.get("temperature")
  top_p = options.get("top_p")
  top_k = options.get("top_k")
  return CreateAPIConfigRequest(
    name="默认 API 配置",
    provider="deepseek",
    kind="llm",
    protocol="openai_compatible",
    api_key_required=True,
    base_url=defaults.base_url,
    mode="non_stream",
    model=defaults.model,
    thinking_enabled=thinking_enabled,
    reasoning_effort=reasoning_effort,  # type: ignore[arg-type]
    max_tokens=max_tokens,
    context_window_tokens=API_CONFIG_DEFAULT_CONTEXT_WINDOW_TOKENS,
    temperature=float(temperature) if temperature is not None else None,
    top_p=float(top_p) if top_p is not None else None,
    top_k=int(top_k) if top_k is not None else None,
    is_default=True,
  )


def _api_key_from_request(value: str | None) -> str | None:
  api_key = (value or "").strip()
  return api_key or None


def _next_api_key(
  current: dict[str, object], request: UpdateAPIConfigRequest
) -> str | None:
  if request.clear_api_key:
    return None
  next_api_key = _api_key_from_request(request.api_key)
  if next_api_key:
    return next_api_key
  current_api_key = current.get("api_key")
  return str(current_api_key) if current_api_key else None


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()
