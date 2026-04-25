from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from app.Schemas.common import PromptRequestType
from app.Utils.errors import LLMResponseFormatError
from app.Services.structured_outputs.schemas import (
  ChapterBlueprintOutput,
  PerspectiveSuggestionOutput,
  TextOutput,
)

_TEXT_REQUEST_TYPES: set[PromptRequestType] = {
  "polish_selection",
  "quick_generate_next_paragraph",
  "generate_next_paragraph",
  "generate_next_section",
  "polish_document_selection",
  "generate_document_continuation",
}


@dataclass(frozen=True)
class StructuredOutputContext:
  valid_perspective_ids: frozenset[str] = field(default_factory=frozenset)


def validate_structured_output(
  request_type: PromptRequestType,
  payload: dict[str, Any],
  context: StructuredOutputContext | None = None,
) -> dict[str, Any]:
  if request_type == "perspective_suggestion":
    return _validate_perspective_suggestions(request_type, payload, context)
  if request_type == "generate_chapter_blueprint":
    return _validate_chapter_blueprint(request_type, payload)
  if request_type in _TEXT_REQUEST_TYPES:
    return _validate_text_output(request_type, payload)
  raise LLMResponseFormatError(
    f"LLM response schema validation failed for {request_type}: unsupported request type"
  )


def _validate_text_output(
  request_type: PromptRequestType, payload: dict[str, Any]
) -> dict[str, Any]:
  try:
    return TextOutput.model_validate(payload).model_dump(mode="json")
  except ValidationError as exc:
    raise LLMResponseFormatError(_schema_error(request_type, exc)) from exc


def _validate_chapter_blueprint(
  request_type: PromptRequestType, payload: dict[str, Any]
) -> dict[str, Any]:
  try:
    return ChapterBlueprintOutput.model_validate(payload).model_dump(mode="json")
  except ValidationError as exc:
    raise LLMResponseFormatError(_schema_error(request_type, exc)) from exc


def _validate_perspective_suggestions(
  request_type: PromptRequestType,
  payload: dict[str, Any],
  context: StructuredOutputContext | None,
) -> dict[str, Any]:
  valid_ids = context.valid_perspective_ids if context else frozenset()
  if not valid_ids:
    raise LLMResponseFormatError(
      f"LLM response schema validation failed for {request_type}: "
      "valid perspective ids are required"
    )
  try:
    parsed = PerspectiveSuggestionOutput.model_validate(payload)
  except ValidationError as exc:
    raise LLMResponseFormatError(_schema_error(request_type, exc)) from exc

  seen_ids: set[str] = set()
  for index, card in enumerate(parsed.cards):
    if card.perspective_id not in valid_ids:
      raise LLMResponseFormatError(
        f"LLM response schema validation failed for {request_type}: "
        f"cards[{index}].perspective_id must be one of current perspectives"
      )
    if card.perspective_id in seen_ids:
      raise LLMResponseFormatError(
        f"LLM response schema validation failed for {request_type}: "
        f"cards[{index}].perspective_id is duplicated"
      )
    seen_ids.add(card.perspective_id)

  return parsed.model_dump(mode="json", exclude_none=True)


def _schema_error(request_type: PromptRequestType, exc: ValidationError) -> str:
  parts: list[str] = []
  for error in exc.errors():
    loc = ".".join(str(item) for item in error.get("loc", ())) or "root"
    message = str(error.get("msg", "invalid value"))
    parts.append(f"{loc}: {message}")
  detail = "; ".join(parts) if parts else "invalid structured output"
  return f"LLM response schema validation failed for {request_type}: {detail}"
