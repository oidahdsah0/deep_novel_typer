from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMMessage:
  role: str
  content: str


@dataclass(frozen=True)
class LLMResponse:
  content: str
  model: str
  finish_reason: str | None = None
  request_body: dict[str, Any] | None = None
  response_body: dict[str, Any] | None = None
  prompt_tokens: int | None = None
  completion_tokens: int | None = None
  total_tokens: int | None = None


@dataclass(frozen=True)
class LLMStreamEvent:
  content_delta: str = ""
  reasoning_delta: str = ""
  finish_reason: str | None = None
  model: str | None = None
  raw: dict[str, Any] | None = None
  prompt_tokens: int | None = None
  completion_tokens: int | None = None
  total_tokens: int | None = None


@dataclass(frozen=True)
class LLMRequestOverrides:
  api_key: str | None = None
  api_key_required: bool | None = None
  base_url: str | None = None
  mode: str | None = None
  model: str | None = None
  request_options: dict[str, Any] | None = None


class CompletionClient(Protocol):
  model: str

  @property
  def is_configured(self) -> bool:
    ...

  def is_configured_for(self, overrides: LLMRequestOverrides | None = None) -> bool:
    ...

  async def complete(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> LLMResponse:
    ...

  async def complete_non_stream(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> LLMResponse:
    ...

  def complete_stream(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> AsyncIterator[LLMStreamEvent]:
    ...
