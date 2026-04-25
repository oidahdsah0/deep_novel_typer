from __future__ import annotations

from app.Services.api_configs import APIConfigService, EffectiveAPIConfig, build_llm_overrides
from app.Services.debug_log_service import DebugLogService, LLMDebugContext
from app.Services.prompt_profiles import PromptProfileService
from app.Services.structured_llm_service import StructuredLLMResponse, complete_json
from app.Utils.llm import CompletionClient
from app.Schemas.common import PromptRequestType


class GenerationRuntime:
  def __init__(
    self,
    prompt_profile_service: PromptProfileService,
    api_config_service: APIConfigService,
    llm_client: CompletionClient,
    debug_log_service: DebugLogService | None,
  ) -> None:
    self._prompt_profile_service = prompt_profile_service
    self._api_config_service = api_config_service
    self._llm_client = llm_client
    self._debug_log_service = debug_log_service

  async def effective_config_for_request(
    self, project_id: str, request_type: PromptRequestType
  ) -> EffectiveAPIConfig | None:
    config_id = await self._prompt_profile_service.request_api_config_id(
      project_id, request_type
    )
    return await self._api_config_service.get_effective_config(config_id, kind="llm")

  def can_call_llm(self, effective_config: EffectiveAPIConfig | None) -> bool:
    if effective_config is None:
      return False
    return self._llm_client.is_configured_for(build_llm_overrides(effective_config))

  async def build_prompt(
    self,
    project_id: str,
    request_type: PromptRequestType,
    runtime_input: dict[str, object],
  ):
    return await self._prompt_profile_service.build_preview(
      project_id,
      request_type,
      runtime_input,
    )

  async def complete(
    self,
    project_id: str,
    request_type: PromptRequestType,
    effective_config: EffectiveAPIConfig,
    prompt_build,
    temperature_override: float | None = None,
  ) -> StructuredLLMResponse:
    request_temperature = await self._prompt_profile_service.request_temperature(
      project_id, request_type
    )
    return await complete_json(
      self._llm_client,
      request_type,
      prompt_build.messages,
      build_llm_overrides(
        effective_config,
        temperature_override=temperature_override
        if temperature_override is not None
        else request_temperature,
      ),
      self._debug_log_service,
      _debug_context(project_id, request_type, effective_config),
      context_pack=prompt_build.context_pack,
      context_window_tokens=effective_config.config.context_window_tokens,
    )


def _debug_context(
  project_id: str, request_type: str, effective_config: EffectiveAPIConfig
) -> LLMDebugContext:
  settings = effective_config.config
  return LLMDebugContext(
    project_id=project_id,
    request_type=request_type,
    api_config_id=settings.id,
    provider=settings.provider,
    model=settings.model,
  )
