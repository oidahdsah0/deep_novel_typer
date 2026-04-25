from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.Schemas.common import PromptProfileVersionType, PromptRequestType


class PromptProfile(BaseModel):
  request_type: PromptRequestType
  name: str
  system_template: str
  user_template: str
  output_contract: str = ""
  chapter_ids: list[str] = Field(default_factory=list)
  document_ids: list[str] = Field(default_factory=list)
  config: dict[str, object] = Field(default_factory=dict)
  is_system: bool = False
  created_at: str | None = None
  updated_at: str | None = None


class PromptProfileLibrary(BaseModel):
  profiles: list[PromptProfile] = Field(default_factory=list)


class PromptProfileSnapshot(BaseModel):
  name: str
  system_template: str
  user_template: str
  output_contract: str = ""
  chapter_ids: list[str] = Field(default_factory=list)
  document_ids: list[str] = Field(default_factory=list)
  config: dict[str, object] = Field(default_factory=dict)


class PromptProfileVersion(BaseModel):
  id: str
  project_id: str
  request_type: PromptRequestType
  version_type: PromptProfileVersionType
  label: str | None = None
  note: str = ""
  system_chars: int = 0
  user_chars: int = 0
  chapter_count: int = 0
  document_count: int = 0
  created_at: str


class PromptProfileVersionDetail(PromptProfileVersion):
  snapshot: PromptProfileSnapshot


class RestorePromptProfileVersionResponse(BaseModel):
  profile: PromptProfile
  version: PromptProfileVersionDetail


class UpdatePromptProfileRequest(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=80)
  system_template: str | None = Field(default=None, max_length=60000)
  user_template: str | None = Field(default=None, max_length=120000)
  output_contract: str | None = Field(default=None, max_length=60000)
  chapter_ids: list[str] | None = None
  document_ids: list[str] | None = None
  config: dict[str, object] | None = None

  @field_validator("name", mode="before")
  @classmethod
  def strip_name(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip()
    return value
