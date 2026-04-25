from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from app.Schemas.common import SuggestionSource


class SuggestionSeverity(str, Enum):
  calm = "calm"
  focus = "focus"
  risk = "risk"


class SuggestionRequestTrigger(str, Enum):
  manual = "manual"
  batch = "batch"
  auto = "auto"


class DraftParagraphRequest(BaseModel):
  chapter_id: str
  paragraph: str
  perspective_id: str | None = None
  trigger: SuggestionRequestTrigger = SuggestionRequestTrigger.manual


class SuggestionCard(BaseModel):
  id: str
  perspective_id: str
  perspective_name: str
  title: str
  body: str
  detail: str | None = None
  severity: SuggestionSeverity
  source: SuggestionSource = "local"
  model: str | None = None
