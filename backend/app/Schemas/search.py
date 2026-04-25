from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ProjectSearchScope = Literal["all", "chapters", "documents", "prompts", "presets", "versions"]
ProjectSearchResourceType = Literal[
  "chapter",
  "document",
  "prompt_profile",
  "prompt_profile_version",
  "generation_preset",
  "resource_version",
]
ProjectSearchMatchField = Literal["title", "path", "content"]


class ProjectSearchMatch(BaseModel):
  field: ProjectSearchMatchField
  snippet: str


class ProjectSearchResult(BaseModel):
  resource_type: ProjectSearchResourceType
  resource_id: str
  resource_subtype: str = ""
  title: str
  path: list[str] = Field(default_factory=list)
  updated_at: str
  score: float = 0
  matches: list[ProjectSearchMatch] = Field(default_factory=list)
  metadata: dict[str, object] = Field(default_factory=dict)


class ProjectSearchResponse(BaseModel):
  query: str
  scope: ProjectSearchScope
  results: list[ProjectSearchResult] = Field(default_factory=list)
