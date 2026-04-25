import pytest

from app.Services.llm_context_budget import ensure_context_budget, estimate_context_budget
from app.Utils.errors import LLMContextWindowExceededError
from app.Utils.llm import LLMMessage


def test_context_budget_counts_all_messages() -> None:
  messages = [
    LLMMessage(role="system", content="系统提示"),
    LLMMessage(role="user", content="用户问题"),
    LLMMessage(role="assistant", content="历史回答" * 20),
  ]

  budget = estimate_context_budget(
    messages,
    output_token_budget=256,
    context_window_tokens=2_000,
  )
  without_history = estimate_context_budget(
    messages[:2],
    output_token_budget=256,
    context_window_tokens=2_000,
  )

  assert budget.input_tokens > without_history.input_tokens
  assert budget.total_with_output_budget == budget.input_tokens + 256
  assert budget.exceeded is False


def test_context_budget_rejects_over_window() -> None:
  messages = [LLMMessage(role="user", content="长文本" * 200)]

  with pytest.raises(LLMContextWindowExceededError):
    ensure_context_budget(
      messages,
      output_token_budget=512,
      context_window_tokens=600,
      request_label="test_request",
    )
