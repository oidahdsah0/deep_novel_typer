from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.Schemas.common import ChapterNodeType


class ChapterSummary(BaseModel):
  id: str
  title: str
  order: int
  word_count: int = 0


class ChapterDetail(ChapterSummary):
  content: str
  writing_synopsis: str = ""
  writing_synopsis_updated_at: str
  updated_at: str


class ChapterNode(BaseModel):
  id: str
  parent_id: str | None = None
  type: ChapterNodeType
  title: str
  chapter_id: str | None = None
  word_count: int = 0
  updated_at: str
  children: list["ChapterNode"] = Field(default_factory=list)


class ChapterSearchMatch(BaseModel):
  field: Literal["title", "content"]
  snippet: str


class ChapterSearchResult(BaseModel):
  chapter_id: str
  node_id: str
  title: str
  path: list[str] = Field(default_factory=list)
  word_count: int = 0
  score: float = 0
  matches: list[ChapterSearchMatch] = Field(default_factory=list)


class ChapterSearchResponse(BaseModel):
  query: str
  results: list[ChapterSearchResult] = Field(default_factory=list)


class ExportChaptersDocxRequest(BaseModel):
  chapter_ids: list[str] = Field(min_length=1, max_length=200)

  @field_validator("chapter_ids")
  @classmethod
  def normalize_chapter_ids(cls, value: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for chapter_id in value:
      stripped = chapter_id.strip()
      if not stripped or stripped in seen:
        continue
      seen.add(stripped)
      normalized.append(stripped)
    if not normalized:
      raise ValueError("chapter_ids cannot be empty")
    return normalized


class UpdateChapterRequest(BaseModel):
  content: str
  base_updated_at: str | None = Field(
    default=None,
    description="Exact updated_at value returned by the last detail/save response.",
  )


class UpdateChapterWritingSynopsisRequest(BaseModel):
  writing_synopsis: str = Field(default="", max_length=60000)
  base_updated_at: str | None = Field(
    default=None,
    description=(
      "Exact writing_synopsis_updated_at value returned by the last detail/save response."
    ),
  )


class CreateChapterRequest(BaseModel):
  title: str = Field(min_length=1, max_length=120)
  content: str = ""
  parent_id: str | None = Field(default=None, max_length=120)

  @field_validator("title", "parent_id", mode="before")
  @classmethod
  def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
      stripped = value.strip()
      return stripped or None
    return value


class CreateChapterNodeRequest(BaseModel):
  type: ChapterNodeType
  title: str = Field(min_length=1, max_length=120)
  parent_id: str | None = Field(default=None, max_length=120)
  content: str = Field(default="", max_length=500000)

  @field_validator("title", "parent_id", mode="before")
  @classmethod
  def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
      stripped = value.strip()
      return stripped or None
    return value


class UpdateChapterNodeRequest(BaseModel):
  title: str | None = Field(default=None, min_length=1, max_length=120)

  @field_validator("title", mode="before")
  @classmethod
  def strip_title(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip()
    return value


class MoveChapterNodeRequest(BaseModel):
  parent_id: str | None = Field(default=None, max_length=120)
  before_node_id: str | None = Field(default=None, max_length=120)

  @field_validator("parent_id", "before_node_id", mode="before")
  @classmethod
  def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
      stripped = value.strip()
      return stripped or None
    return value


class MoveChapterNodeResponse(BaseModel):
  chapter_tree: list[ChapterNode] = Field(default_factory=list)
  chapters: list[ChapterSummary] = Field(default_factory=list)
