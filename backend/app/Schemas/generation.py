from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.Schemas.common import DraftGenerationAction, GenerationPresetKind, SuggestionSource


class GenerationPreset(BaseModel):
  id: str
  kind: GenerationPresetKind
  name: str
  content: str
  is_system: bool = False
  is_hidden: bool = False
  created_at: str | None = None
  updated_at: str | None = None


class GenerationPresetLibrary(BaseModel):
  writing_modes: list[GenerationPreset] = Field(default_factory=list)
  quick_generation_modes: list[GenerationPreset] = Field(default_factory=list)
  chapter_blueprint_modes: list[GenerationPreset] = Field(default_factory=list)
  author_personas: list[GenerationPreset] = Field(default_factory=list)
  polish_modes: list[GenerationPreset] = Field(default_factory=list)
  document_polish_modes: list[GenerationPreset] = Field(default_factory=list)
  document_generation_modes: list[GenerationPreset] = Field(default_factory=list)
  editor_personas: list[GenerationPreset] = Field(default_factory=list)


class CreateGenerationPresetRequest(BaseModel):
  kind: GenerationPresetKind
  name: str = Field(min_length=1, max_length=80)
  content: str = Field(default="", max_length=20000)

  @field_validator("name", mode="before")
  @classmethod
  def strip_name(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip()
    return value


class UpdateGenerationPresetRequest(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=80)
  content: str | None = Field(default=None, max_length=20000)

  @field_validator("name", mode="before")
  @classmethod
  def strip_name(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip()
    return value


class GenerateDraftRequest(BaseModel):
  chapter_id: str
  action: DraftGenerationAction
  cursor_index: int | None = Field(default=None, ge=0)
  previous_paragraph: str = Field(default="", max_length=12000)
  next_paragraph: str = Field(default="", max_length=12000)
  writing_preset_id: str = Field(min_length=1, max_length=80)
  writing_prompt: str = Field(default="", max_length=20000)
  author_preset_id: str = Field(min_length=1, max_length=80)
  author_skill: str = Field(default="", max_length=20000)


class GenerateChapterBlueprintRequest(BaseModel):
  chapter_id: str
  cursor_index: int | None = Field(default=None, ge=0)
  previous_paragraph: str = Field(default="", max_length=12000)
  next_paragraph: str = Field(default="", max_length=12000)
  blueprint_preset_id: str = Field(min_length=1, max_length=80)
  blueprint_prompt: str = Field(default="", max_length=20000)
  author_preset_id: str = Field(min_length=1, max_length=80)
  author_skill: str = Field(default="", max_length=20000)


class GenerateQuickDraftRequest(BaseModel):
  chapter_id: str
  cursor_index: int | None = Field(default=None, ge=0)
  previous_paragraph: str = Field(default="", max_length=12000)
  next_paragraph: str = Field(default="", max_length=12000)
  quick_preset_id: str = Field(min_length=1, max_length=80)
  quick_prompt: str = Field(default="", max_length=20000)
  author_preset_id: str = Field(min_length=1, max_length=80)
  author_skill: str = Field(default="", max_length=20000)


class PolishSelectionRequest(BaseModel):
  chapter_id: str
  selected_text: str = Field(min_length=1, max_length=12000)
  polish_preset_id: str = Field(min_length=1, max_length=80)
  polish_prompt: str = Field(default="", max_length=20000)


class PolishDocumentSelectionRequest(BaseModel):
  document_id: str
  chapter_id: str | None = Field(default=None, max_length=120)
  selected_text: str = Field(min_length=1, max_length=20000)
  polish_preset_id: str = Field(min_length=1, max_length=80)
  polish_prompt: str = Field(default="", max_length=20000)
  editor_preset_id: str = Field(min_length=1, max_length=80)
  editor_skill: str = Field(default="", max_length=20000)


class GenerateDocumentContinuationRequest(BaseModel):
  document_id: str
  chapter_id: str | None = Field(default=None, max_length=120)
  generation_preset_id: str = Field(min_length=1, max_length=80)
  generation_prompt: str = Field(default="", max_length=20000)
  editor_preset_id: str = Field(min_length=1, max_length=80)
  editor_skill: str = Field(default="", max_length=20000)


class GeneratedDraft(BaseModel):
  text: str
  source: SuggestionSource = "local"
  model: str | None = None


class GeneratedChapterBlueprint(BaseModel):
  points: list[str]
  source: SuggestionSource = "local"
  model: str | None = None
