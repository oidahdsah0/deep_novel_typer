from __future__ import annotations

from typing import Any

from app.Utils.llm_schemas import LLMStreamEvent


def _content_from_non_stream_response(response: Any) -> str:
  choices = _get_field(response, "choices") or []
  if not choices:
    return ""
  choice = choices[0]
  message = _get_field(choice, "message") or {}
  return _string_content(_get_field(message, "content"))


def _finish_reason_from_non_stream_response(response: Any) -> str | None:
  choices = _get_field(response, "choices") or []
  if not choices:
    return None
  finish_reason = _get_field(choices[0], "finish_reason")
  return str(finish_reason) if finish_reason is not None else None


def _usage_from_non_stream_response(response: Any) -> tuple[int | None, int | None, int | None]:
  usage = _get_field(response, "usage")
  if usage is None:
    return None, None, None
  prompt_tokens = _int_field(usage, "prompt_tokens")
  completion_tokens = _int_field(usage, "completion_tokens")
  total_tokens = _int_field(usage, "total_tokens")
  if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
    total_tokens = prompt_tokens + completion_tokens
  return prompt_tokens, completion_tokens, total_tokens


def _stream_event_from_chunk(chunk: Any) -> LLMStreamEvent:
  data = _dump_model(chunk) or {}
  choices = _get_field(chunk, "choices") or []
  choice = choices[0] if choices else {}
  delta = _get_field(choice, "delta") or {}
  prompt_tokens, completion_tokens, total_tokens = _usage_from_non_stream_response(chunk)
  return LLMStreamEvent(
    content_delta=_string_content(_get_field(delta, "content")),
    reasoning_delta=_string_content(_get_extra_field(delta, "reasoning_content")),
    finish_reason=_get_field(choice, "finish_reason"),
    model=_get_field(chunk, "model"),
    raw=data,
    prompt_tokens=prompt_tokens,
    completion_tokens=completion_tokens,
    total_tokens=total_tokens,
  )


def _get_extra_field(value: Any, key: str) -> Any:
  direct_value = _get_field(value, key)
  if direct_value is not None:
    return direct_value
  extra = getattr(value, "model_extra", None)
  if isinstance(extra, dict):
    return extra.get(key)
  return None


def _get_field(value: Any, key: str) -> Any:
  if isinstance(value, dict):
    return value.get(key)
  return getattr(value, key, None)


def _dump_model(value: Any) -> dict[str, Any] | None:
  if isinstance(value, dict):
    return value
  model_dump = getattr(value, "model_dump", None)
  if callable(model_dump):
    try:
      dumped = model_dump(mode="json")
    except TypeError:
      dumped = model_dump()
    return dumped if isinstance(dumped, dict) else None
  return None


def _int_field(value: Any, key: str) -> int | None:
  raw_value = _get_field(value, key)
  if raw_value is None:
    return None
  try:
    return int(raw_value)
  except (TypeError, ValueError):
    return None


def _json_safe(value: Any) -> Any:
  if value is None or isinstance(value, (str, int, float, bool)):
    return value
  if isinstance(value, dict):
    return {str(key): _json_safe(item) for key, item in value.items()}
  if isinstance(value, list):
    return [_json_safe(item) for item in value]
  return str(value)


def _string_content(value: Any) -> str:
  if value is None:
    return ""
  if isinstance(value, str):
    return value
  if isinstance(value, list):
    return "".join(_string_content(_get_field(item, "text") or item) for item in value)
  return str(value)
