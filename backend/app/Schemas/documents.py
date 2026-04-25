from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.Schemas.common import DocumentKind, DocumentNodeType


class WorkspaceDocument(BaseModel):
  kind: DocumentKind
  title: str
  updated_at: str


class DocumentDetail(WorkspaceDocument):
  content: str


class DocumentNode(BaseModel):
  id: str
  parent_id: str | None = None
  type: DocumentNodeType
  title: str
  updated_at: str
  children: list["DocumentNode"] = Field(default_factory=list)


class MarkdownDocumentDetail(BaseModel):
  id: str
  parent_id: str | None = None
  type: DocumentNodeType = "markdown"
  title: str
  updated_at: str
  content: str


class UpdateDocumentRequest(BaseModel):
  content: str
  base_updated_at: str | None = Field(
    default=None,
    description="Exact updated_at value returned by the last detail/save response.",
  )


class CreateDocumentNodeRequest(BaseModel):
  type: DocumentNodeType
  title: str = Field(min_length=1, max_length=120)
  parent_id: str | None = Field(default=None, max_length=120)
  content: str = Field(default="", max_length=200000)

  @field_validator("title", "parent_id", mode="before")
  @classmethod
  def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
      stripped = value.strip()
      return stripped or None
    return value


class UpdateDocumentNodeRequest(BaseModel):
  title: str | None = Field(default=None, min_length=1, max_length=120)

  @field_validator("title", mode="before")
  @classmethod
  def strip_title(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip()
    return value


class MoveDocumentNodeRequest(BaseModel):
  parent_id: str | None = Field(default=None, max_length=120)
  before_node_id: str | None = Field(default=None, max_length=120)

  @field_validator("parent_id", "before_node_id", mode="before")
  @classmethod
  def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
      stripped = value.strip()
      return stripped or None
    return value


class MoveDocumentNodeResponse(BaseModel):
  document_tree: list[DocumentNode] = Field(default_factory=list)
