from __future__ import annotations

from app.Schemas.chapters import ChapterDetail
from app.Schemas.documents import MarkdownDocumentDetail
from app.Schemas.generation import (
  GenerateChapterBlueprintRequest,
  GenerateDocumentContinuationRequest,
  GenerateDraftRequest,
  GenerateQuickDraftRequest,
  GenerationPreset,
  PolishDocumentSelectionRequest,
  PolishSelectionRequest,
)
from app.Schemas.projects import ProjectManifest
from app.Services.context_limits import CHAPTER_CONTEXT_CHARS, DOCUMENT_CONTEXT_CHARS
from app.Utils.text import extract_last_paragraph, tail_text


def draft_request_type(request: GenerateDraftRequest) -> str:
  if request.action == "next_paragraph":
    return "generate_next_paragraph"
  return "generate_next_section"


def previous_paragraph_for(
  chapter_content: str, previous_paragraph: str, cursor_index: int | None
) -> str:
  if not previous_paragraph.strip() and cursor_index is None:
    return extract_last_paragraph(chapter_content)
  return previous_paragraph


def draft_runtime_input(
  project: ProjectManifest,
  chapter: ChapterDetail,
  request: GenerateDraftRequest,
  author_preset: GenerationPreset,
  previous_paragraph: str,
) -> dict[str, object]:
  return {
    "project_title": project.title,
    "current_chapter_id": request.chapter_id,
    "chapter_title": chapter.title,
    "chapter_synopsis": chapter.writing_synopsis,
    "current_chapter": tail_text(chapter.content, CHAPTER_CONTEXT_CHARS),
    "cursor_index": request.cursor_index,
    "previous_paragraph": previous_paragraph,
    "next_paragraph": request.next_paragraph,
    "writing_prompt": request.writing_prompt or "无",
    "author_persona_id": author_preset.id,
    "author_persona_name": author_preset.name,
    "author_persona": request.author_skill or "无",
  }


def quick_runtime_input(
  project: ProjectManifest,
  chapter: ChapterDetail,
  request: GenerateQuickDraftRequest,
  author_preset: GenerationPreset,
  previous_paragraph: str,
) -> dict[str, object]:
  return {
    "project_title": project.title,
    "current_chapter_id": request.chapter_id,
    "chapter_title": chapter.title,
    "chapter_synopsis": chapter.writing_synopsis,
    "current_chapter": tail_text(chapter.content, CHAPTER_CONTEXT_CHARS),
    "cursor_index": request.cursor_index,
    "previous_paragraph": previous_paragraph,
    "next_paragraph": request.next_paragraph,
    "quick_prompt": "",
    "author_persona_id": author_preset.id,
    "author_persona_name": author_preset.name,
    "author_persona": request.author_skill or "无",
  }


def blueprint_runtime_input(
  project: ProjectManifest,
  chapter: ChapterDetail,
  request: GenerateChapterBlueprintRequest,
  author_preset: GenerationPreset,
  previous_paragraph: str,
) -> dict[str, object]:
  return {
    "project_title": project.title,
    "current_chapter_id": request.chapter_id,
    "chapter_title": chapter.title,
    "chapter_synopsis": chapter.writing_synopsis,
    "current_chapter": tail_text(chapter.content, CHAPTER_CONTEXT_CHARS),
    "cursor_index": request.cursor_index,
    "previous_paragraph": previous_paragraph,
    "next_paragraph": request.next_paragraph,
    "blueprint_prompt": request.blueprint_prompt or "无",
    "author_persona_id": author_preset.id,
    "author_persona_name": author_preset.name,
    "author_persona": request.author_skill or "无",
  }


def polish_runtime_input(
  project: ProjectManifest,
  chapter: ChapterDetail,
  request: PolishSelectionRequest,
) -> dict[str, object]:
  return {
    "project_title": project.title,
    "current_chapter_id": request.chapter_id,
    "chapter_title": chapter.title,
    "chapter_synopsis": chapter.writing_synopsis,
    "current_chapter": tail_text(chapter.content, CHAPTER_CONTEXT_CHARS),
    "selected_text": request.selected_text,
    "polish_prompt": request.polish_prompt or "无",
  }


def document_polish_runtime_input(
  project: ProjectManifest,
  document: MarkdownDocumentDetail,
  request: PolishDocumentSelectionRequest,
  editor_preset: GenerationPreset,
  chapter: ChapterDetail | None = None,
) -> dict[str, object]:
  payload: dict[str, object] = {
    "project_title": project.title,
    "document_id": request.document_id,
    "document_title": document.title,
    "current_document": tail_text(document.content, DOCUMENT_CONTEXT_CHARS),
    "selected_text": request.selected_text,
    "polish_prompt": request.polish_prompt or "无",
    "editor_persona_id": editor_preset.id,
    "editor_persona_name": editor_preset.name,
    "editor_persona": request.editor_skill or "无",
  }
  if chapter is not None:
    payload.update(
      {
        "current_chapter_id": chapter.id,
        "chapter_title": chapter.title,
        "chapter_synopsis": chapter.writing_synopsis,
      }
    )
  return payload


def document_continuation_runtime_input(
  project: ProjectManifest,
  document: MarkdownDocumentDetail,
  request: GenerateDocumentContinuationRequest,
  editor_preset: GenerationPreset,
  chapter: ChapterDetail | None = None,
) -> dict[str, object]:
  payload: dict[str, object] = {
    "project_title": project.title,
    "document_id": request.document_id,
    "document_title": document.title,
    "current_document": tail_text(document.content, DOCUMENT_CONTEXT_CHARS),
    "generation_prompt": request.generation_prompt or "无",
    "editor_persona_id": editor_preset.id,
    "editor_persona_name": editor_preset.name,
    "editor_persona": request.editor_skill or "无",
  }
  if chapter is not None:
    payload.update(
      {
        "current_chapter_id": chapter.id,
        "chapter_title": chapter.title,
        "chapter_synopsis": chapter.writing_synopsis,
      }
    )
  return payload
