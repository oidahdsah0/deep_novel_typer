from __future__ import annotations

import json
from typing import Any

from app.Schemas.debug import DebugReadableMessage, DebugReadableView
from app.Schemas.prompt_context import PromptContextPack

_REQUEST_OPTION_EXCLUDED_KEYS = {"messages"}
_SECRET_KEY_FRAGMENTS = ("api_key", "authorization", "bearer", "secret", "token", "password")
_SCHEMA_ERROR_HINTS = (
  "json",
  "schema",
  "format",
  "truncated",
  "empty content",
  "must contain",
  "valid",
)


def build_debug_readable_view(
  *,
  request_body: dict[str, Any],
  response_body: dict[str, Any],
  context_pack: dict[str, Any] | None = None,
  error_message: str | None = None,
  request_type: str | None = None,
  model_kind: str = "llm",
) -> DebugReadableView:
  if model_kind == "embedding":
    return _embedding_readable_view(
      request_body=request_body,
      response_body=response_body,
      error_message=error_message,
    )

  messages = _messages_from_request(request_body)
  raw_content = _raw_content_from_response(response_body)
  parsed_payload = _parse_json_object(raw_content) if raw_content else None
  parsed_context_pack = _context_pack(context_pack)
  return DebugReadableView(
    system_messages=[message for message in messages if message.role == "system"],
    user_messages=[message for message in messages if message.role == "user"],
    request_options=_request_options_from_body(request_body),
    context_pack=parsed_context_pack,
    context_budget=(
      parsed_context_pack.budget.model_dump(mode="json") if parsed_context_pack else None
    ),
    context_materials=(
      [item.model_dump(mode="json") for item in parsed_context_pack.materials]
      if parsed_context_pack
      else []
    ),
    raw_content=raw_content,
    parsed_payload=parsed_payload,
    schema_error=_schema_error(error_message, raw_content, parsed_payload, request_type),
  )


def _embedding_readable_view(
  *,
  request_body: dict[str, Any],
  response_body: dict[str, Any],
  error_message: str | None,
) -> DebugReadableView:
  summary_keys = (
    "tool_type",
    "resource_type",
    "resource_id",
    "run_id",
    "batch_label",
    "segmentation_mode",
    "algorithm",
    "input_count",
    "cache",
    "model_signature_hash",
    "input_hashes",
  )
  response_keys = (
    "embedding_count",
    "embedding_dimensions",
    "usage",
    "duration_ms",
    "error_type",
  )
  summary = {
    key: _sanitize(request_body[key])
    for key in summary_keys
    if key in request_body
  }
  summary.update(
    {
      key: _sanitize(response_body[key])
      for key in response_keys
      if key in response_body
    }
  )
  if error_message:
    summary["error_message"] = error_message
  return DebugReadableView(
    request_options=_request_options_from_body(request_body),
    embedding_summary=summary,
  )


def _messages_from_request(request_body: dict[str, Any]) -> list[DebugReadableMessage]:
  raw_messages = request_body.get("messages")
  if not isinstance(raw_messages, list):
    return []

  messages: list[DebugReadableMessage] = []
  for item in raw_messages:
    if not isinstance(item, dict):
      continue
    role = str(item.get("role") or "unknown")
    content = _message_content(item.get("content"))
    messages.append(DebugReadableMessage(role=role, content=content))
  return messages


def _context_pack(value: dict[str, Any] | None) -> PromptContextPack | None:
  if not value:
    return None
  try:
    return PromptContextPack.model_validate(value)
  except Exception:
    return None


def _message_content(value: Any) -> str:
  if value is None:
    return ""
  if isinstance(value, str):
    return value
  if isinstance(value, list):
    return "".join(_message_content(_content_part_text(item)) for item in value)
  return json.dumps(_sanitize(value), ensure_ascii=False, indent=2)


def _content_part_text(value: Any) -> Any:
  if isinstance(value, dict):
    return value.get("text") or value.get("content") or value
  return value


def _request_options_from_body(request_body: dict[str, Any]) -> dict[str, Any]:
  return {
    str(key): "[redacted]" if _is_secret_key(str(key)) else _sanitize(value)
    for key, value in request_body.items()
    if str(key) not in _REQUEST_OPTION_EXCLUDED_KEYS
  }


def _raw_content_from_response(response_body: dict[str, Any]) -> str | None:
  direct = response_body.get("content")
  if isinstance(direct, str):
    return direct

  choices = response_body.get("choices")
  if isinstance(choices, list):
    for choice in choices:
      if not isinstance(choice, dict):
        continue
      message = choice.get("message")
      if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
          return content
      text = choice.get("text")
      if isinstance(text, str):
        return text

  output_text = response_body.get("output_text")
  if isinstance(output_text, str):
    return output_text
  return None


def _parse_json_object(content: str) -> dict[str, Any] | None:
  stripped = content.strip()
  if not stripped:
    return None

  candidates = [stripped]
  fenced = _strip_fenced_code(stripped)
  if fenced != stripped:
    candidates.append(fenced)

  start = stripped.find("{")
  end = stripped.rfind("}")
  if 0 <= start < end:
    candidates.append(stripped[start : end + 1])

  for candidate in candidates:
    try:
      payload = json.loads(candidate)
    except json.JSONDecodeError:
      continue
    if isinstance(payload, dict):
      return payload
  return None


def _strip_fenced_code(value: str) -> str:
  if not value.startswith("```"):
    return value
  lines = value.splitlines()
  if len(lines) < 3 or not lines[-1].strip().startswith("```"):
    return value
  first = lines[0].strip().lower()
  if first not in {"```", "```json"}:
    return value
  return "\n".join(lines[1:-1]).strip()


def _schema_error(
  error_message: str | None,
  raw_content: str | None,
  parsed_payload: dict[str, Any] | None,
  request_type: str | None = None,
) -> str | None:
  if error_message and _looks_like_schema_error(error_message):
    return error_message
  if request_type == "chat_about_work":
    return None
  if raw_content and parsed_payload is None:
    return "模型返回内容无法解析为 JSON object。"
  return None


def _looks_like_schema_error(value: str) -> bool:
  lowered = value.lower()
  return any(hint in lowered for hint in _SCHEMA_ERROR_HINTS)


def _sanitize(value: Any) -> Any:
  if isinstance(value, dict):
    sanitized: dict[str, Any] = {}
    for key, item in value.items():
      key_text = str(key)
      sanitized[key_text] = "[redacted]" if _is_secret_key(key_text) else _sanitize(item)
    return sanitized
  if isinstance(value, list):
    return [_sanitize(item) for item in value]
  return value


def _is_secret_key(key: str) -> bool:
  normalized = key.lower().replace("-", "_")
  return any(fragment in normalized for fragment in _SECRET_KEY_FRAGMENTS)
