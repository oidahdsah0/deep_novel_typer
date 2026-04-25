from __future__ import annotations

from pydantic import BaseModel, Field

from app.Schemas.api_configs import APIConfig, APIConfigTemplate
from app.Schemas.chapters import ChapterNode, ChapterSummary
from app.Schemas.documents import DocumentNode, WorkspaceDocument
from app.Schemas.generation import GenerationPresetLibrary
from app.Schemas.perspectives import Perspective
from app.Schemas.projects import ProjectSummary
from app.Schemas.prompt_profiles import PromptProfileLibrary
from app.Schemas.suggestions import SuggestionCard
from app.Schemas.typewriter_layout import TypewriterLayoutSettings
from app.Schemas.versions import VersionSettings


class ActiveChapter(BaseModel):
  id: str
  title: str
  content: str
  word_count: int
  writing_synopsis: str = ""
  writing_synopsis_updated_at: str
  updated_at: str


class WorkspaceSnapshot(BaseModel):
  project: ProjectSummary
  active_chapter: ActiveChapter
  chapters: list[ChapterSummary]
  chapter_tree: list[ChapterNode] = Field(default_factory=list)
  documents: list[WorkspaceDocument]
  document_tree: list[DocumentNode] = Field(default_factory=list)
  perspectives: list[Perspective]
  suggestions: list[SuggestionCard]
  api_configs: list[APIConfig] = Field(default_factory=list)
  generation_presets: GenerationPresetLibrary = Field(default_factory=GenerationPresetLibrary)
  prompt_profiles: PromptProfileLibrary = Field(default_factory=PromptProfileLibrary)
  typewriter_layout_settings: TypewriterLayoutSettings = Field(
    default_factory=TypewriterLayoutSettings
  )


class LibraryStats(BaseModel):
  active_count: int
  trash_count: int
  total_words: int


class LibrarySnapshot(BaseModel):
  projects: list[ProjectSummary]
  recent_projects: list[ProjectSummary]
  stats: LibraryStats
  api_configs: list[APIConfig] = Field(default_factory=list)
  api_config_templates: list[APIConfigTemplate] = Field(default_factory=list)
  version_settings: VersionSettings = Field(default_factory=VersionSettings)
