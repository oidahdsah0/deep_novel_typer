from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from app.Utils.llm_options import _OPENAI_CHAT_COMPLETION_OPTIONS, _merge_request_options
from app.Utils.llm_parsing import (
  _content_from_non_stream_response,
  _dump_model,
  _finish_reason_from_non_stream_response,
  _get_field,
  _json_safe,
  _stream_event_from_chunk,
  _usage_from_non_stream_response,
)
from app.Utils.llm_schemas import (
  LLMMessage,
  LLMRequestOverrides,
  LLMResponse,
  LLMStreamEvent,
)


class OpenAIChatClient:
  def __init__(
    self,
    *,
    api_key: str,
    api_key_required: bool,
    enabled: bool,
    base_url: str,
    headers: dict[str, str],
    mode: str,
    model: str,
    non_stream_request_options: dict[str, Any],
    timeout_seconds: float,
    client: AsyncOpenAI | None = None,
    close_client_on_shutdown: bool = True,
  ) -> None:
    self._api_key = api_key
    self._api_key_required = api_key_required
    self._enabled = enabled
    self._base_url = base_url
    self._headers = headers
    self._mode = mode
    self._model = model
    self._non_stream_request_options = non_stream_request_options
    self._timeout_seconds = timeout_seconds
    self._client = client or AsyncOpenAI(
      api_key=api_key or "unused",
      base_url=base_url,
      default_headers=headers,
      timeout=timeout_seconds,
    )
    self._close_client_on_shutdown = close_client_on_shutdown

  @property
  def is_configured(self) -> bool:
    return self.is_configured_for()

  def is_configured_for(self, overrides: LLMRequestOverrides | None = None) -> bool:
    api_key = (
      overrides.api_key
      if overrides is not None and overrides.api_key is not None
      else self._api_key
    )
    base_url = (
      overrides.base_url
      if overrides is not None and overrides.base_url is not None
      else self._base_url
    )
    model = overrides.model if overrides and overrides.model else self._model
    api_key_required = (
      overrides.api_key_required
      if overrides is not None and overrides.api_key_required is not None
      else self._api_key_required
    )
    has_auth = bool(api_key) or not api_key_required
    return self._enabled and has_auth and bool(base_url and model)

  @property
  def model(self) -> str:
    return self._model

  async def complete(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> LLMResponse:
    return await self.complete_non_stream(messages, overrides)

  async def complete_non_stream(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> LLMResponse:
    if not self.is_configured_for(overrides):
      raise RuntimeError("LLM client is not configured")

    request_body = self._build_create_kwargs(messages, stream=False, overrides=overrides)
    response = await self._client_for(overrides).chat.completions.create(**request_body)
    content = _content_from_non_stream_response(response)
    finish_reason = _finish_reason_from_non_stream_response(response)
    response_body = _dump_model(response) or {}
    prompt_tokens, completion_tokens, total_tokens = _usage_from_non_stream_response(response)
    model = str(
      _get_field(response, "model")
      or (overrides.model if overrides else None)
      or self._model
    )
    return LLMResponse(
      content=str(content),
      model=model,
      finish_reason=finish_reason,
      request_body=_json_safe(request_body),
      response_body=_json_safe(response_body),
      prompt_tokens=prompt_tokens,
      completion_tokens=completion_tokens,
      total_tokens=total_tokens,
    )

  async def complete_stream_aggregated(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> LLMResponse:
    raise RuntimeError("Streaming LLM requests are disabled; use non-stream JSON requests")

  async def complete_stream(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> AsyncIterator[LLMStreamEvent]:
    if not self.is_configured_for(overrides):
      raise RuntimeError("LLM client is not configured")

    request_body = self._build_stream_kwargs(messages, overrides=overrides)
    stream = await self._client_for(overrides).chat.completions.create(**request_body)
    async for chunk in stream:
      event = _stream_event_from_chunk(chunk)
      if (
        event.content_delta
        or event.reasoning_delta
        or event.finish_reason
        or event.prompt_tokens is not None
        or event.completion_tokens is not None
        or event.total_tokens is not None
      ):
        yield event

  async def shutdown(self) -> None:
    if self._close_client_on_shutdown:
      await self._client.close()

  def _build_create_kwargs(
    self,
    messages: list[LLMMessage],
    *,
    stream: bool,
    overrides: LLMRequestOverrides | None = None,
  ) -> dict[str, Any]:
    base_options = self._non_stream_request_options
    options = _merge_request_options(base_options, overrides.request_options if overrides else None)
    options["response_format"] = {"type": "json_object"}
    create_kwargs: dict[str, Any] = {
      "model": overrides.model if overrides and overrides.model else self._model,
      "messages": [message.__dict__ for message in messages],
      "stream": False,
    }
    extra_body = dict(options.get("extra_body") or {})

    for key, value in options.items():
      if key in {"extra_body", "stream"} or value is None:
        continue
      if key in _OPENAI_CHAT_COMPLETION_OPTIONS:
        create_kwargs[key] = value
      else:
        extra_body[key] = value

    if extra_body:
      create_kwargs["extra_body"] = extra_body
    return create_kwargs

  def _build_stream_kwargs(
    self,
    messages: list[LLMMessage],
    overrides: LLMRequestOverrides | None = None,
  ) -> dict[str, Any]:
    kwargs = self._build_create_kwargs(messages, stream=True, overrides=overrides)
    kwargs["stream"] = True
    kwargs["stream_options"] = {"include_usage": True}
    kwargs.pop("response_format", None)
    return kwargs

  def _client_for(self, overrides: LLMRequestOverrides | None = None) -> AsyncOpenAI:
    if not overrides:
      return self._client
    override_api_key = overrides.api_key if overrides.api_key is not None else self._api_key
    override_base_url = (
      overrides.base_url if overrides.base_url is not None else self._base_url
    )
    if override_api_key == self._api_key and override_base_url == self._base_url:
      return self._client
    return self._client.with_options(
      api_key=(
        overrides.api_key
        if overrides.api_key
        else self._api_key or "unused"
      ),
      base_url=(
        overrides.base_url
        if overrides.base_url is not None
        else self._base_url
      ),
    )
