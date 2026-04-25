from __future__ import annotations

from pydantic import BaseModel, Field

from app.Schemas.chapters import ChapterSummary
from app.Schemas.common import ProjectStatus
from app.Schemas.documents import WorkspaceDocument


class ProjectSummary(BaseModel):
  id: str
  title: str
  subtitle: str = ""
  description: str = ""
  genre: str = ""
  status: ProjectStatus = "drafting"
  created_at: str
  updated_at: str
  last_opened_at: str | None = None
  deleted_at: str | None = None
  chapter_count: int = 0
  word_count: int = 0


class ProjectDetail(ProjectSummary):
  chapters: list[ChapterSummary] = Field(default_factory=list)
  documents: list[WorkspaceDocument] = Field(default_factory=list)


ProjectManifest = ProjectDetail


class CreateProjectRequest(BaseModel):
  title: str = Field(min_length=1, max_length=120)
  subtitle: str = Field(default="", max_length=180)
  description: str = Field(default="", max_length=1200)
  genre: str = Field(default="", max_length=80)
  status: ProjectStatus = "drafting"


class UpdateProjectRequest(BaseModel):
  title: str | None = Field(default=None, min_length=1, max_length=120)
  subtitle: str | None = Field(default=None, max_length=180)
  description: str | None = Field(default=None, max_length=1200)
  genre: str | None = Field(default=None, max_length=80)
  status: ProjectStatus | None = None
