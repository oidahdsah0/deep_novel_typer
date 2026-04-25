from __future__ import annotations

from app.Schemas.prompt_preview import (
  PromptPreviewItem,
  PromptPreviewMessage,
  PromptPreviewRequest,
)
from app.Services.api_configs import EffectiveAPIConfig
from app.Services.llm_context_budget import (
  context_budget_warning,
  estimate_context_budget,
  int_option,
)
from app.Services.prompt_profiles import PromptProfileService
from app.Utils.llm import LLMMessage

from .request_inputs import PreviewInput
from .request_options import (
  PromptPreviewConfigResolver,
  api_config_summary,
  api_config_warnings,
  request_options,
)
from .token_estimate import token_estimate


class PromptPreviewItemBuilder:
  def __init__(
    self,
    prompt_profile_service: PromptProfileService,
    config_resolver: PromptPreviewConfigResolver,
  ) -> None:
    self._prompt_profile_service = prompt_profile_service
    self._config_resolver = config_resolver

  async def build_item(
    self,
    *,
    project_id: str,
    preview_input: PreviewInput,
    effective_config: EffectiveAPIConfig | None,
    request: PromptPreviewRequest,
  ) -> PromptPreviewItem:
    build_result = await self._prompt_profile_service.build_preview(
      project_id,
      preview_input.request_type,
      preview_input.runtime_input,
      request.profile_override,
    )
    item_warnings = [*preview_input.warnings]
    item_warnings.extend(api_config_warnings(effective_config))
    options = request_options(
      effective_config,
      preview_input.request_type,
      await self._config_resolver.request_temperature(
        project_id,
        preview_input.request_type,
        request,
      ),
    )
    context_window_tokens = (
      effective_config.config.context_window_tokens if effective_config else None
    )
    estimate = token_estimate(build_result.messages, options, context_window_tokens)
    warning = context_budget_warning(
      preview_input.label,
      estimate_context_budget(
        build_result.messages,
        output_token_budget=int_option(options.get("max_tokens")),
        context_window_tokens=context_window_tokens,
      ),
    )
    if warning:
      item_warnings.append(warning)
    return PromptPreviewItem(
      label=preview_input.label,
      api_config=api_config_summary(effective_config),
      request_options=options,
      token_estimate=estimate,
      context_pack=build_result.context_pack,
      messages=[_preview_message(message) for message in build_result.messages],
      chapters=build_result.chapters,
      documents=build_result.documents,
      warnings=item_warnings,
    )


def _preview_message(message: LLMMessage) -> PromptPreviewMessage:
  return PromptPreviewMessage(role=message.role, content=message.content)
