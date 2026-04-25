from __future__ import annotations

from pydantic import BaseModel, Field

from app.Schemas.projects import ProjectSummary


class ProjectExportOptions(BaseModel):
  include_debug_logs: bool = False
  include_token_usage: bool = False
  include_api_config_summary: bool = True


class ProjectTransferCounts(BaseModel):
  chapters: int = 0
  documents: int = 0
  chapter_nodes: int = 0
  document_nodes: int = 0
  perspectives: int = 0
  generation_presets: int = 0
  prompt_profiles: int = 0
  prompt_profile_versions: int = 0
  resource_versions: int = 0
  debug_logs: int = 0
  token_usage_rows: int = 0


class ProjectExportManifest(BaseModel):
  format: str = "deep-novel-typer.project-export"
  format_version: int = 2
  exported_at: str
  source_project_id: str
  source_project_title: str
  app_version: str = "0.1.0"
  options: ProjectExportOptions = Field(default_factory=ProjectExportOptions)
  counts: ProjectTransferCounts = Field(default_factory=ProjectTransferCounts)


class ProjectImportResponse(BaseModel):
  project: ProjectSummary
  source_project_id: str
  imported_project_id: str
  warnings: list[str] = Field(default_factory=list)
  counts: ProjectTransferCounts = Field(default_factory=ProjectTransferCounts)
