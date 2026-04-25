from __future__ import annotations

from dataclasses import dataclass

from app.Services.prompt_profiles.context_formatting import estimate_text_tokens
from app.Utils.errors import LLMContextWindowExceededError
from app.Utils.llm import LLMMessage


@dataclass(frozen=True)
class LLMContextBudget:
  input_tokens: int
  output_token_budget: int | None
  total_with_output_budget: int | None
  context_window_tokens: int | None
  usage_ratio: float | None
  exceeded: bool


def estimate_context_budget(
  messages: list[LLMMessage],
  *,
  output_token_budget: int | None,
  context_window_tokens: int | None,
) -> LLMContextBudget:
  input_tokens = (
    sum(estimate_text_tokens(message.content) for message in messages)
    + message_overhead(messages)
  )
  total_with_output_budget = (
    input_tokens + output_token_budget if output_token_budget is not None else None
  )
  usage_ratio = (
    total_with_output_budget / context_window_tokens
    if total_with_output_budget is not None and context_window_tokens
    else None
  )
  return LLMContextBudget(
    input_tokens=input_tokens,
    output_token_budget=output_token_budget,
    total_with_output_budget=total_with_output_budget,
    context_window_tokens=context_window_tokens,
    usage_ratio=usage_ratio,
    exceeded=usage_ratio is not None and usage_ratio > 1,
  )


def ensure_context_budget(
  messages: list[LLMMessage],
  *,
  output_token_budget: int | None,
  context_window_tokens: int | None,
  request_label: str,
) -> LLMContextBudget:
  budget = estimate_context_budget(
    messages,
    output_token_budget=output_token_budget,
    context_window_tokens=context_window_tokens,
  )
  if budget.exceeded:
    raise LLMContextWindowExceededError(
      _error_message(request_label=request_label, budget=budget)
    )
  return budget


def context_budget_warning(request_label: str, budget: LLMContextBudget) -> str | None:
  if budget.context_window_tokens is None or budget.total_with_output_budget is None:
    return None
  if budget.exceeded:
    return _error_message(request_label=request_label, budget=budget)
  if budget.usage_ratio is not None and budget.usage_ratio >= 0.9:
    return (
      f"{request_label} 预计占用上下文窗口 "
      f"{budget.total_with_output_budget:,} / {budget.context_window_tokens:,} tokens，"
      "已接近上限。"
    )
  return None


def message_overhead(messages: list[LLMMessage]) -> int:
  return len(messages) * 4 + 2


def int_option(value: object) -> int | None:
  return value if isinstance(value, int) and not isinstance(value, bool) else None


def _error_message(*, request_label: str, budget: LLMContextBudget) -> str:
  return (
    f"{request_label} 上下文超出：预计输入 {budget.input_tokens:,} tokens，"
    f"输出预算 {budget.output_token_budget or 0:,} tokens，"
    f"合计 {budget.total_with_output_budget or budget.input_tokens:,} tokens，"
    f"超过当前模型配置的上下文窗口 {budget.context_window_tokens or 0:,} tokens。"
    "请减少固定章节、最近章节、资料文档或聊天历史，或降低最大输出 tokens。"
  )
