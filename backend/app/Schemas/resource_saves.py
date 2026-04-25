from __future__ import annotations

from app.Schemas.chapters import ChapterDetail
from app.Schemas.documents import MarkdownDocumentDetail
from app.Schemas.projects import ProjectSummary


class ChapterSaveResponse(ChapterDetail):
  project: ProjectSummary


class ChapterWritingSynopsisSaveResponse(ChapterDetail):
  project: ProjectSummary


class DocumentSaveResponse(MarkdownDocumentDetail):
  project: ProjectSummary
