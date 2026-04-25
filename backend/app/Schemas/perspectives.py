from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Perspective(BaseModel):
  id: str
  name: str
  description: str
  instructions: str
  api_config_id: str | None = None
  is_enabled: bool = False
  created_at: str | None = None
  updated_at: str | None = None


class CreatePerspectiveRequest(BaseModel):
  name: str = Field(min_length=1, max_length=80)
  description: str = Field(default="", max_length=240)
  instructions: str = Field(min_length=1, max_length=2000)
  api_config_id: str | None = Field(default=None, max_length=80)

  @field_validator("api_config_id", mode="before")
  @classmethod
  def normalize_empty_api_config_id(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip() or None
    return value


class UpdatePerspectiveRequest(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=80)
  description: str | None = Field(default=None, max_length=240)
  instructions: str | None = Field(default=None, min_length=1, max_length=2000)
  api_config_id: str | None = Field(default=None, max_length=80)
  is_enabled: bool | None = None

  @field_validator("api_config_id", mode="before")
  @classmethod
  def normalize_empty_api_config_id(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip() or None
    return value
