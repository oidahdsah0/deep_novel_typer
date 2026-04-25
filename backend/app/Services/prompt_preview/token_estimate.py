from __future__ import annotations

from app.Schemas.prompt_preview import PromptPreviewTokenEstimate
from app.Services.prompt_profiles.context_formatting import estimate_text_tokens
from app.Services.llm_context_budget import (
  estimate_context_budget,
  int_option,
)
from app.Utils.llm import LLMMessage


def token_estimate(
  messages: list[LLMMessage],
  request_options: dict[str, object],
  context_window_tokens: int | None,
) -> PromptPreviewTokenEstimate:
  system_tokens = sum(
    estimate_text_tokens(message.content)
    for message in messages
    if message.role == "system"
  )
  user_tokens = sum(
    estimate_text_tokens(message.content)
    for message in messages
    if message.role == "user"
  )
  output_token_budget = int_option(request_options.get("max_tokens"))
  budget = estimate_context_budget(
    messages,
    output_token_budget=output_token_budget,
    context_window_tokens=context_window_tokens,
  )
  return PromptPreviewTokenEstimate(
    input_tokens=budget.input_tokens,
    system_tokens=system_tokens,
    user_tokens=user_tokens,
    output_token_budget=output_token_budget,
    total_with_output_budget=budget.total_with_output_budget,
    context_window_tokens=context_window_tokens,
    context_usage_ratio=budget.usage_ratio,
    context_window_exceeded=budget.exceeded,
  )
