from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.Schemas.suggestions import SuggestionSeverity


@dataclass(frozen=True)
class SuggestionDraft:
  perspective_id: str
  title: str
  body: str
  detail: str | None
  severity: SuggestionSeverity


def parse_suggestion_payload(
  payload: dict[str, Any], valid_perspective_ids: set[str]
) -> list[SuggestionDraft]:
  cards = payload.get("cards")
  if not isinstance(cards, list):
    return []

  drafts: list[SuggestionDraft] = []
  seen_ids: set[str] = set()
  for item in cards:
    if not isinstance(item, dict):
      continue
    perspective_id = _clean_inline_text(item.get("perspective_id"), 80)
    if (
      not perspective_id
      or perspective_id not in valid_perspective_ids
      or perspective_id in seen_ids
    ):
      continue

    title = _clean_inline_text(item.get("title"), 48)
    body = _clean_inline_text(item.get("body"), 360)
    detail = _clean_multiline_text(item.get("detail"), 1200)
    if not title or not body:
      continue

    severity_value = _clean_inline_text(item.get("severity"), 16)
    severity = (
      SuggestionSeverity(severity_value)
      if severity_value in {item.value for item in SuggestionSeverity}
      else SuggestionSeverity.focus
    )
    drafts.append(
      SuggestionDraft(
        perspective_id=perspective_id,
        title=title,
        body=body,
        detail=detail,
        severity=severity,
      )
    )
    seen_ids.add(perspective_id)

  return drafts


def _clean_inline_text(value: object, max_length: int) -> str:
  if not isinstance(value, str):
    return ""
  return " ".join(value.strip().split())[:max_length]


def _clean_multiline_text(value: object, max_length: int) -> str | None:
  if not isinstance(value, str):
    return None
  lines = [" ".join(line.strip().split()) for line in value.strip().splitlines()]
  normalized = "\n".join(line for line in lines if line)
  if not normalized:
    return None
  return normalized[:max_length]
