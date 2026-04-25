from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.Schemas.common import VersionType, VersionedResourceType


class VersionSettings(BaseModel):
  auto_enabled: bool = True
  auto_interval_minutes: int = Field(default=10, ge=1, le=240)
  auto_min_chars_changed: int = Field(default=300, ge=1, le=10000)
  auto_min_change_ratio: float = Field(default=0.15, ge=0, le=1)
  updated_at: str | None = None


class UpdateVersionSettingsRequest(BaseModel):
  auto_enabled: bool | None = None
  auto_interval_minutes: int | None = Field(default=None, ge=1, le=240)
  auto_min_chars_changed: int | None = Field(default=None, ge=1, le=10000)
  auto_min_change_ratio: float | None = Field(default=None, ge=0, le=1)


class ResourceVersion(BaseModel):
  id: str
  project_id: str
  resource_type: VersionedResourceType
  resource_id: str
  resource_title: str
  version_type: VersionType
  label: str | None = None
  note: str = ""
  word_count: int = 0
  char_count: int = 0
  created_at: str


class ResourceVersionDetail(ResourceVersion):
  content: str


class CreateResourceVersionRequest(BaseModel):
  resource_type: VersionedResourceType
  resource_id: str = Field(min_length=1, max_length=120)
  version_type: VersionType = "manual"
  label: str | None = Field(default=None, max_length=120)
  note: str = Field(default="", max_length=1000)

  @field_validator("resource_id", "label", "note", mode="before")
  @classmethod
  def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip()
    return value

  @field_validator("label", mode="after")
  @classmethod
  def normalize_empty_label(cls, value: str | None) -> str | None:
    return value or None


class RestoreResourceVersionResponse(BaseModel):
  resource_type: VersionedResourceType
  resource_id: str
  title: str
  content: str
  word_count: int = 0
  updated_at: str
