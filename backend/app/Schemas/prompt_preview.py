from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.Schemas.common import APIConfigKind, PromptRequestType
from app.Schemas.prompt_context import PromptContextPack


class PromptPreviewProfileOverride(BaseModel):
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


class PromptPreviewRequest(BaseModel):
  request_type: PromptRequestType
  chapter_id: str | None = Field(default=None, max_length=120)
  document_id: str | None = Field(default=None, max_length=120)
  paragraph: str = Field(default="", max_length=8000)
  selected_text: str = Field(default="", max_length=20000)
  cursor_index: int | None = Field(default=None, ge=0)
  previous_paragraph: str = Field(default="", max_length=12000)
  next_paragraph: str = Field(default="", max_length=12000)
  writing_prompt: str = Field(default="", max_length=20000)
  quick_prompt: str = Field(default="", max_length=20000)
  blueprint_prompt: str = Field(default="", max_length=20000)
  author_persona_id: str = Field(default="", max_length=120)
  author_persona_name: str = Field(default="", max_length=200)
  author_persona: str = Field(default="", max_length=20000)
  polish_prompt: str = Field(default="", max_length=20000)
  generation_prompt: str = Field(default="", max_length=20000)
  editor_persona_id: str = Field(default="", max_length=120)
  editor_persona_name: str = Field(default="", max_length=200)
  editor_persona: str = Field(default="", max_length=20000)
  profile_override: PromptPreviewProfileOverride | None = None

  @field_validator("chapter_id", "document_id", mode="before")
  @classmethod
  def normalize_empty_ids(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip() or None
    return value


class PromptPreviewMessage(BaseModel):
  role: str
  content: str


class PromptPreviewMaterial(BaseModel):
  id: str
  title: str
  source: str
  chars: int
  truncated: bool = False
  kind: str = "material"
  format: str = "plain"
  content_mode: str = "full"
  token_estimate: int = 0


class PromptPreviewAPIConfig(BaseModel):
  id: str | None = None
  name: str = "未设置"
  provider: str = ""
  kind: APIConfigKind = "llm"
  base_url: str = ""
  model: str = ""
  api_key_required: bool = True
  api_key_configured: bool = False
  configured: bool = False
  is_default: bool = False
  context_window_tokens: int | None = None


class PromptPreviewTokenEstimate(BaseModel):
  input_tokens: int = 0
  system_tokens: int = 0
  user_tokens: int = 0
  output_token_budget: int | None = None
  total_with_output_budget: int | None = None
  context_window_tokens: int | None = None
  context_usage_ratio: float | None = None
  context_window_exceeded: bool = False
  estimator: str = "rough_mixed_text"


class PromptPreviewItem(BaseModel):
  label: str
  api_config: PromptPreviewAPIConfig | None = None
  request_options: dict[str, Any] = Field(default_factory=dict)
  token_estimate: PromptPreviewTokenEstimate = Field(
    default_factory=PromptPreviewTokenEstimate
  )
  context_pack: PromptContextPack | None = None
  messages: list[PromptPreviewMessage] = Field(default_factory=list)
  chapters: list[PromptPreviewMaterial] = Field(default_factory=list)
  documents: list[PromptPreviewMaterial] = Field(default_factory=list)
  warnings: list[str] = Field(default_factory=list)


class PromptPreviewResponse(BaseModel):
  request_type: PromptRequestType
  items: list[PromptPreviewItem] = Field(default_factory=list)
  warnings: list[str] = Field(default_factory=list)
