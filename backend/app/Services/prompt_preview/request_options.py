from __future__ import annotations

from app.Schemas.common import PromptRequestType
from app.Schemas.perspectives import Perspective
from app.Schemas.prompt_preview import (
  PromptPreviewAPIConfig,
  PromptPreviewRequest,
)
from app.Services.api_configs import APIConfigService, EffectiveAPIConfig, build_llm_overrides
from app.Services.prompt_profiles import PromptProfileService
from app.Services.prompt_profiles.config import api_config_id_from_config, temperature_from_config
from app.Utils.config import LLM_MODE_NON_STREAM
from app.Utils.errors import EntityNotFoundError


class PromptPreviewConfigResolver:
  def __init__(
    self,
    prompt_profile_service: PromptProfileService,
    api_config_service: APIConfigService,
  ) -> None:
    self._prompt_profile_service = prompt_profile_service
    self._api_config_service = api_config_service

  async def effective_config_for_perspective(
    self,
    project_id: str,
    perspective: Perspective,
    request: PromptPreviewRequest,
  ) -> EffectiveAPIConfig | None:
    config_id = perspective.api_config_id or await self._request_api_config_id(
      project_id,
      "perspective_suggestion",
      request,
    )
    try:
      return await self._api_config_service.get_effective_config(config_id, kind="llm")
    except EntityNotFoundError:
      return None

  async def effective_config_for_request(
    self,
    project_id: str,
    request_type: PromptRequestType,
    request: PromptPreviewRequest,
  ) -> EffectiveAPIConfig | None:
    config_id = await self._request_api_config_id(project_id, request_type, request)
    return await self._api_config_service.get_effective_config(config_id, kind="llm")

  async def _request_api_config_id(
    self,
    project_id: str,
    request_type: PromptRequestType,
    request: PromptPreviewRequest,
  ) -> str | None:
    if request.profile_override and request.profile_override.config is not None:
      return api_config_id_from_config(request.profile_override.config)
    return await self._prompt_profile_service.request_api_config_id(
      project_id, request_type
    )

  async def request_temperature(
    self,
    project_id: str,
    request_type: PromptRequestType,
    request: PromptPreviewRequest,
  ) -> float | None:
    if request.profile_override and request.profile_override.config is not None:
      return temperature_from_config(request.profile_override.config)
    return await self._prompt_profile_service.request_temperature(project_id, request_type)


def api_config_summary(
  effective_config: EffectiveAPIConfig | None,
) -> PromptPreviewAPIConfig | None:
  if effective_config is None:
    return None
  config = effective_config.config
  return PromptPreviewAPIConfig(
    id=config.id,
    name=config.name,
    provider=config.provider,
    kind=config.kind,
    base_url=config.base_url,
    model=config.model,
    api_key_required=config.api_key_required,
    api_key_configured=bool(effective_config.api_key),
    configured=is_configured(effective_config),
    is_default=config.is_default,
    context_window_tokens=config.context_window_tokens,
  )


def api_config_warnings(effective_config: EffectiveAPIConfig | None) -> list[str]:
  if effective_config is None:
    return ["没有可用的默认 LLM API 配置，真实请求会走本地兜底或失败。"]
  if not is_configured(effective_config):
    return [
      "当前 LLM API 配置需要 API Key，但尚未保存 Key，"
      "真实请求会走本地兜底或失败。"
    ]
  return []


def is_configured(effective_config: EffectiveAPIConfig) -> bool:
  config = effective_config.config
  return (not config.api_key_required) or bool(effective_config.api_key)


def request_options(
  effective_config: EffectiveAPIConfig | None,
  request_type: PromptRequestType,
  temperature_override: float | None = None,
) -> dict[str, object]:
  if effective_config is None:
    return {}
  overrides = build_llm_overrides(
    effective_config,
    temperature_override=temperature_override,
  )
  options = dict(overrides.request_options or {})
  if request_type == "chat_about_work":
    options.pop("response_format", None)
    options["stream"] = True
    options["stream_options"] = {"include_usage": True}
  else:
    options["stream"] = False
  options["mode"] = overrides.mode or LLM_MODE_NON_STREAM
  return options
