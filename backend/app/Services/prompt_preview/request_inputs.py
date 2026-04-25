from __future__ import annotations

from dataclasses import dataclass

from app.Schemas.common import PromptRequestType
from app.Schemas.perspectives import Perspective
from app.Schemas.prompt_preview import PromptPreviewRequest
from app.Services.chapter_service import ChapterService
from app.Services.context_limits import (
  CHAPTER_CONTEXT_CHARS,
  DOCUMENT_CONTEXT_CHARS,
  SUGGESTION_CONTEXT_CHARS,
)
from app.Services.document_service import DocumentService
from app.Services.perspective_service import PerspectiveService
from app.Services.project_service import ProjectService
from app.Utils.text import extract_last_paragraph, tail_text


@dataclass(frozen=True)
class PreviewInput:
  request_type: PromptRequestType
  label: str
  runtime_input: dict[str, object]
  warnings: list[str]
  perspective: Perspective | None = None


class PromptPreviewInputBuilder:
  def __init__(
    self,
    project_service: ProjectService,
    chapter_service: ChapterService,
    document_service: DocumentService,
    perspective_service: PerspectiveService,
  ) -> None:
    self._project_service = project_service
    self._chapter_service = chapter_service
    self._document_service = document_service
    self._perspective_service = perspective_service

  async def perspective_inputs(
    self, project_id: str, request: PromptPreviewRequest
  ) -> tuple[list[PreviewInput], list[str]]:
    project = await self._project_service.get_manifest(project_id)
    chapter = (
      await self._chapter_service.get_chapter(project_id, request.chapter_id)
      if request.chapter_id
      else None
    )
    paragraph = request.paragraph.strip() or extract_last_paragraph(
      chapter.content if chapter else ""
    )
    perspectives = [
      item
      for item in await self._perspective_service.list_perspectives(project_id)
      if item.is_enabled
    ]
    response_warnings: list[str] = []
    if not perspectives:
      response_warnings.append("当前项目没有启用的视角，真实请求不会调用 LLM。")
      return [
        PreviewInput(
          request_type="perspective_suggestion",
          label="视角建议预览",
          runtime_input={
            "project": _project_input(project),
            "current_chapter_id": request.chapter_id or "",
            "chapter_title": chapter.title if chapter else "",
            "current_chapter": tail_text(chapter.content, SUGGESTION_CONTEXT_CHARS)
            if chapter
            else "",
            "current_paragraph": paragraph,
            "perspectives": [],
          },
          warnings=response_warnings,
        )
      ], response_warnings

    inputs: list[PreviewInput] = []
    for perspective in perspectives:
      warnings: list[str] = []
      if not request.chapter_id:
        warnings.append("未提供当前章节，章节上下文为空。")
      if not paragraph:
        warnings.append("未提供当前段落，视角建议的当前段落为空。")
      inputs.append(
        PreviewInput(
          request_type="perspective_suggestion",
          label=f"视角：{perspective.name}",
          runtime_input={
            "project": _project_input(project),
            "current_chapter_id": request.chapter_id or "",
            "chapter_title": chapter.title if chapter else "",
            "current_chapter": tail_text(chapter.content, SUGGESTION_CONTEXT_CHARS)
            if chapter
            else "",
            "current_paragraph": paragraph,
            "perspectives": [
              {
                "id": perspective.id,
                "name": perspective.name,
                "description": perspective.description,
                "instructions": perspective.instructions,
              }
            ],
          },
          warnings=warnings,
          perspective=perspective,
        )
      )
    return inputs, response_warnings

  async def single_request_input(
    self, project_id: str, request: PromptPreviewRequest
  ) -> PreviewInput:
    project = await self._project_service.get_manifest(project_id)
    warnings: list[str] = []
    request_type = request.request_type

    if request_type in _CHAPTER_REQUEST_TYPES:
      chapter = (
        await self._chapter_service.get_chapter(project_id, request.chapter_id)
        if request.chapter_id
        else None
      )
      if chapter is None:
        warnings.append("未提供当前章节，章节上下文为空。")
      previous_paragraph = request.previous_paragraph
      if (
        request_type in _CONTINUATION_REQUEST_TYPES
        and not previous_paragraph.strip()
        and request.cursor_index is None
      ):
        previous_paragraph = extract_last_paragraph(chapter.content if chapter else "")
      runtime_input = {
        "project_title": project.title,
        "current_chapter_id": request.chapter_id or "",
        "chapter_title": chapter.title if chapter else "",
        "chapter_synopsis": chapter.writing_synopsis if chapter else "",
        "current_chapter": tail_text(chapter.content, CHAPTER_CONTEXT_CHARS)
        if chapter
        else "",
        "cursor_index": request.cursor_index,
        "previous_paragraph": previous_paragraph,
        "next_paragraph": request.next_paragraph,
        "selected_text": request.selected_text,
        "polish_prompt": request.polish_prompt or "无",
        "quick_prompt": "",
        "writing_prompt": request.writing_prompt or "无",
        "blueprint_prompt": request.blueprint_prompt or "无",
        "author_persona_id": request.author_persona_id,
        "author_persona_name": request.author_persona_name,
        "author_persona": request.author_persona or "无",
      }
      if request_type == "polish_selection" and not request.selected_text.strip():
        warnings.append("未提供选中文本，真实润色请求无法生成。")
      return PreviewInput(
        request_type=request_type,
        label=request_label(request_type),
        runtime_input=runtime_input,
        warnings=warnings,
      )

    if request_type in {"polish_document_selection", "generate_document_continuation"}:
      document = (
        await self._document_service.get_document(project_id, request.document_id)
        if request.document_id
        else None
      )
      chapter = (
        await self._chapter_service.get_chapter(project_id, request.chapter_id)
        if request.chapter_id
        else None
      )
      if document is None:
        warnings.append("未提供当前资料，资料上下文为空。")
      runtime_input = {
        "project_title": project.title,
        "document_id": request.document_id or "",
        "document_title": document.title if document else "",
        "current_document": tail_text(document.content, DOCUMENT_CONTEXT_CHARS)
        if document
        else "",
        "selected_text": request.selected_text,
        "polish_prompt": request.polish_prompt or "无",
        "generation_prompt": request.generation_prompt or "无",
        "editor_persona_id": request.editor_persona_id,
        "editor_persona_name": request.editor_persona_name,
        "editor_persona": request.editor_persona or "无",
      }
      if chapter is not None:
        runtime_input.update(
          {
            "current_chapter_id": request.chapter_id or "",
            "chapter_title": chapter.title,
            "chapter_synopsis": chapter.writing_synopsis,
          }
        )
      if request_type == "polish_document_selection" and not request.selected_text.strip():
        warnings.append("未提供资料选中文本，真实润色请求无法生成。")
      return PreviewInput(
        request_type=request_type,
        label=request_label(request_type),
        runtime_input=runtime_input,
        warnings=warnings,
      )

    if request_type == "chat_about_work":
      chapter = (
        await self._chapter_service.get_chapter(project_id, request.chapter_id)
        if request.chapter_id
        else None
      )
      if chapter is None:
        warnings.append("未提供当前章节，聊天上下文不会包含当前章节摘录。")
      return PreviewInput(
        request_type=request_type,
        label=request_label(request_type),
        runtime_input={
          "project_title": project.title,
          "current_chapter_id": request.chapter_id or "",
          "chapter_title": chapter.title if chapter else "",
          "current_chapter": tail_text(chapter.content, CHAPTER_CONTEXT_CHARS)
          if chapter
          else "",
          "chat_messages": "user: 请帮我分析当前章节可以怎样继续推进。",
        },
        warnings=warnings,
      )

    return PreviewInput(
      request_type=request_type,
      label=request_label(request_type),
      runtime_input={"project_title": project.title},
      warnings=[f"未知预览请求类型：{request_type}"],
    )


def request_label(request_type: PromptRequestType) -> str:
  labels = {
    "perspective_suggestion": "视角建议",
    "polish_selection": "润色选中",
    "quick_generate_next_paragraph": "快速生成下一段",
    "generate_next_paragraph": "生成下一段落",
    "generate_next_section": "生成下一部分",
    "generate_chapter_blueprint": "章节基础铺设",
    "polish_document_selection": "资料润色选区",
    "generate_document_continuation": "资料生成后续",
    "chat_about_work": "作品聊天",
  }
  return labels.get(request_type, request_type)

def _project_input(project) -> dict[str, object]:
  return {
    "title": project.title,
    "subtitle": project.subtitle,
    "genre": project.genre,
    "status": project.status,
    "description": project.description,
  }


_CHAPTER_REQUEST_TYPES = {
  "polish_selection",
  "quick_generate_next_paragraph",
  "generate_next_paragraph",
  "generate_next_section",
  "generate_chapter_blueprint",
}
_CONTINUATION_REQUEST_TYPES = {
  "quick_generate_next_paragraph",
  "generate_chapter_blueprint",
  "generate_next_paragraph",
  "generate_next_section",
}
