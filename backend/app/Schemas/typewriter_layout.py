from __future__ import annotations

import math

from pydantic import BaseModel, Field, field_validator


class TypewriterLayoutSettings(BaseModel):
  first_line_indent_chars: float = Field(default=0, ge=0, le=8)
  font_size_px: int = Field(default=20, ge=12, le=32)
  paragraph_gap_lines: float = Field(default=0, ge=0, le=5)
  line_height_multiplier: float = Field(default=2.9, ge=1, le=4)
  updated_at: str | None = None

  @field_validator(
    "first_line_indent_chars",
    "paragraph_gap_lines",
    "line_height_multiplier",
    mode="after",
  )
  @classmethod
  def round_to_tenth(cls, value: float) -> float:
    return round(value * 10) / 10

  @field_validator("font_size_px", mode="before")
  @classmethod
  def round_font_size(cls, value: object) -> object:
    try:
      numeric_value = float(value)
    except (TypeError, ValueError):
      return value
    if not math.isfinite(numeric_value):
      return value
    return int(math.floor(numeric_value + 0.5))


class UpdateTypewriterLayoutSettingsRequest(BaseModel):
  first_line_indent_chars: float = Field(default=0, ge=0, le=8)
  font_size_px: int = Field(default=20, ge=12, le=32)
  paragraph_gap_lines: float = Field(default=0, ge=0, le=5)
  line_height_multiplier: float = Field(default=2.9, ge=1, le=4)

  @field_validator(
    "first_line_indent_chars",
    "paragraph_gap_lines",
    "line_height_multiplier",
    mode="after",
  )
  @classmethod
  def round_to_tenth(cls, value: float) -> float:
    return round(value * 10) / 10

  @field_validator("font_size_px", mode="before")
  @classmethod
  def round_font_size(cls, value: object) -> object:
    try:
      numeric_value = float(value)
    except (TypeError, ValueError):
      return value
    if not math.isfinite(numeric_value):
      return value
    return int(math.floor(numeric_value + 0.5))
