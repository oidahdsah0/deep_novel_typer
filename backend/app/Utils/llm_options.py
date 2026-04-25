from __future__ import annotations

from typing import Any

from app.Utils.llm_parsing import _json_safe
from app.Utils.llm_schemas import LLMMessage, LLMRequestOverrides

_OPENAI_CHAT_COMPLETION_OPTIONS = {
  "audio",
  "frequency_penalty",
  "function_call",
  "functions",
  "logit_bias",
  "logprobs",
  "max_completion_tokens",
  "max_tokens",
  "metadata",
  "modalities",
  "n",
  "parallel_tool_calls",
  "prediction",
  "presence_penalty",
  "reasoning_effort",
  "response_format",
  "seed",
  "service_tier",
  "stop",
  "store",
  "stream_options",
  "temperature",
  "tool_choice",
  "tools",
  "top_logprobs",
  "top_p",
  "user",
  "verbosity",
  "web_search_options",
}



def _merge_request_options(
  base_options: dict[str, Any], override_options: dict[str, Any] | None
) -> dict[str, Any]:
  merged = dict(base_options)
  if not override_options:
    return merged

  for key, value in override_options.items():
    if value is None:
      merged.pop(key, None)
    elif isinstance(value, dict) and isinstance(merged.get(key), dict):
      merged[key] = _merge_request_options(merged[key], value)
    else:
      merged[key] = value
  return merged


def build_chat_completion_request_snapshot(
  messages: list[LLMMessage],
  overrides: LLMRequestOverrides | None = None,
  *,
  stream: bool = False,
) -> dict[str, Any]:
  options = dict(overrides.request_options or {}) if overrides else {}
  if stream:
    options.pop("response_format", None)
    options["stream_options"] = {"include_usage": True}
  else:
    options["response_format"] = {"type": "json_object"}
  snapshot: dict[str, Any] = {
    "model": overrides.model if overrides and overrides.model else "",
    "messages": [message.__dict__ for message in messages],
    "stream": stream,
  }
  extra_body = dict(options.get("extra_body") or {})
  for key, value in options.items():
    if key in {"extra_body", "stream"} or value is None:
      continue
    if key in _OPENAI_CHAT_COMPLETION_OPTIONS:
      snapshot[key] = value
    else:
      extra_body[key] = value
  if extra_body:
    snapshot["extra_body"] = extra_body
  return _json_safe(snapshot)
