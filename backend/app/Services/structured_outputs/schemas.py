from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.Schemas.suggestions import SuggestionSeverity


class TextOutput(BaseModel):
  model_config = ConfigDict(extra="forbid")

  text: str = Field(min_length=1)

  @field_validator("text")
  @classmethod
  def strip_non_empty_text(cls, value: str) -> str:
    stripped = value.strip()
    if not stripped:
      raise ValueError("text must be a non-empty string")
    return stripped


class ChapterBlueprintOutput(BaseModel):
  model_config = ConfigDict(extra="forbid")

  points: list[str] = Field(min_length=1, max_length=12)

  @field_validator("points")
  @classmethod
  def normalize_points(cls, value: list[str]) -> list[str]:
    normalized: list[str] = []
    for item in value:
      if not isinstance(item, str):
        raise ValueError("each point must be a string")
      point = " ".join(item.strip().split())
      if not point:
        continue
      normalized.append(point)
    if not normalized:
      raise ValueError("points must contain at least one non-empty item")
    return normalized[:12]


class PerspectiveSuggestionCardOutput(BaseModel):
  model_config = ConfigDict(extra="forbid")

  perspective_id: str = Field(min_length=1)
  title: str = Field(min_length=1)
  body: str = Field(min_length=1)
  detail: str | None = None
  severity: SuggestionSeverity

  @field_validator("perspective_id", "title", "body", mode="before")
  @classmethod
  def normalize_required_text(cls, value: Any) -> Any:
    if isinstance(value, str):
      return " ".join(value.strip().split())
    return value

  @field_validator("detail", mode="before")
  @classmethod
  def normalize_detail(cls, value: Any) -> Any:
    if not isinstance(value, str):
      return value
    lines = [" ".join(line.strip().split()) for line in value.strip().splitlines()]
    normalized = "\n".join(line for line in lines if line)
    return normalized or None


class PerspectiveSuggestionOutput(BaseModel):
  model_config = ConfigDict(extra="forbid")

  cards: list[PerspectiveSuggestionCardOutput]
