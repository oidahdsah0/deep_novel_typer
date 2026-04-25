from __future__ import annotations

import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from app.Schemas.prompt_context import PromptContextPack
from app.Services.debug_log_service import DebugLogService, LLMDebugContext
from app.Services.llm_context_budget import ensure_context_budget, int_option
from app.Services.model_request_queue_service import model_request_label
from app.Services.structured_outputs import (
  StructuredOutputContext,
  validate_structured_output,
)
from app.Utils.errors import LLMRequestError, LLMResponseFormatError
from app.Utils.llm import (
  CompletionClient,
  LLMMessage,
  LLMRequestOverrides,
  LLMResponse,
  build_chat_completion_request_snapshot,
)
from app.Schemas.common import PromptRequestType


@dataclass(frozen=True)
class StructuredLLMResponse:
  payload: dict[str, Any]
  model: str


async def complete_json(
  client: CompletionClient,
  request_type: PromptRequestType,
  messages: list[LLMMessage],
  overrides: LLMRequestOverrides,
  debug_service: DebugLogService | None = None,
  debug_context: LLMDebugContext | None = None,
  validation_context: StructuredOutputContext | None = None,
  context_pack: PromptContextPack | None = None,
  context_window_tokens: int | None = None,
) -> StructuredLLMResponse:
  ensure_context_budget(
    messages,
    output_token_budget=int_option((overrides.request_options or {}).get("max_tokens")),
    context_window_tokens=context_window_tokens,
    request_label=str(request_type),
  )
  started_at = perf_counter()
  try:
    with model_request_label(request_type):
      response = await client.complete(messages, overrides=overrides)
  except Exception as exc:
    error_message = f"LLM request for {request_type} failed: {exc}"
    await _record_debug_log(
      debug_service,
      debug_context,
      messages=messages,
      overrides=overrides,
      duration_ms=_duration_ms(started_at),
      status="error",
      error_message=error_message,
      response_body={"error": {"type": exc.__class__.__name__, "message": str(exc)}},
      context_pack=context_pack,
    )
    raise LLMRequestError(error_message) from exc

  if response.finish_reason == "length":
    error_message = f"LLM response for {request_type} was truncated before valid JSON completed"
    await _record_debug_log(
      debug_service,
      debug_context,
      messages=messages,
      overrides=overrides,
      response=response,
      duration_ms=_duration_ms(started_at),
      status="error",
      error_message=error_message,
      context_pack=context_pack,
    )
    raise LLMResponseFormatError(
      error_message
    )
  try:
    payload = parse_json_object(response.content, request_type=request_type)
    payload = validate_structured_output(request_type, payload, validation_context)
  except LLMResponseFormatError as exc:
    await _record_debug_log(
      debug_service,
      debug_context,
      messages=messages,
      overrides=overrides,
      response=response,
      duration_ms=_duration_ms(started_at),
      status="error",
      error_message=str(exc),
      context_pack=context_pack,
    )
    raise

  await _record_debug_log(
    debug_service,
    debug_context,
    messages=messages,
    overrides=overrides,
    response=response,
    duration_ms=_duration_ms(started_at),
    status="success",
    context_pack=context_pack,
  )
  return StructuredLLMResponse(
    payload=payload,
    model=response.model,
  )


def parse_json_object(content: str, *, request_type: PromptRequestType) -> dict[str, Any]:
  stripped = content.strip()
  if not stripped:
    raise LLMResponseFormatError(f"LLM response for {request_type} returned empty content")

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

  raise LLMResponseFormatError(f"LLM response for {request_type} was not a valid JSON object")


def require_text_payload(payload: dict[str, Any], *, request_type: PromptRequestType) -> str:
  value = payload.get("text")
  if not isinstance(value, str) or not value.strip():
    raise LLMResponseFormatError(f"LLM response for {request_type} must contain non-empty text")
  return value.strip()


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


async def _record_debug_log(
  debug_service: DebugLogService | None,
  debug_context: LLMDebugContext | None,
  *,
  messages: list[LLMMessage],
  overrides: LLMRequestOverrides,
  duration_ms: int,
  status: str,
  response: LLMResponse | None = None,
  response_body: dict[str, Any] | None = None,
  error_message: str | None = None,
  context_pack: PromptContextPack | None = None,
) -> None:
  if debug_service is None or debug_context is None:
    return
  try:
    await debug_service.record_llm_request(
      context=LLMDebugContext(
        project_id=debug_context.project_id,
        request_type=debug_context.request_type,
        api_config_id=debug_context.api_config_id,
        provider=debug_context.provider,
        model=(response.model if response else None) or debug_context.model,
      ),
      request_body=(
        response.request_body
        if response and response.request_body is not None
        else build_chat_completion_request_snapshot(messages, overrides)
      ),
      response_body=(
        response.response_body
        if response and response.response_body is not None
        else response_body
        or {}
      ),
      status=status,
      error_message=error_message,
      prompt_tokens=response.prompt_tokens if response else None,
      completion_tokens=response.completion_tokens if response else None,
      total_tokens=response.total_tokens if response else None,
      duration_ms=duration_ms,
      context_pack=context_pack,
    )
  except Exception:
    return


def _duration_ms(started_at: float) -> int:
  return max(0, round((perf_counter() - started_at) * 1000))
