from __future__ import annotations

from app.Schemas.generation import (
  GenerateDraftRequest,
  GenerateQuickDraftRequest,
  GeneratedDraft,
)
from app.Services.chapter_service import ChapterService
from app.Services.project_service import ProjectService
from app.Services.structured_llm_service import require_text_payload

from .local_fallbacks import local_draft
from .preset_resolution import GenerationPresetResolver
from .request_inputs import (
  draft_request_type,
  draft_runtime_input,
  previous_paragraph_for,
  quick_runtime_input,
)
from .runtime import GenerationRuntime


class DraftGenerationActions:
  def __init__(
    self,
    project_service: ProjectService,
    chapter_service: ChapterService,
    presets: GenerationPresetResolver,
    runtime: GenerationRuntime,
  ) -> None:
    self._project_service = project_service
    self._chapter_service = chapter_service
    self._presets = presets
    self._runtime = runtime

  async def generate_draft(
    self, project_id: str, request: GenerateDraftRequest
  ) -> GeneratedDraft:
    project = await self._project_service.get_manifest(project_id)
    chapter = await self._chapter_service.get_chapter(project_id, request.chapter_id)
    await self._presets.require_preset(project_id, "writing_mode", request.writing_preset_id)
    author_preset = await self._presets.require_preset(
      project_id, "author_persona", request.author_preset_id
    )
    request_type = draft_request_type(request)
    effective_config = await self._runtime.effective_config_for_request(
      project_id, request_type
    )
    if not self._runtime.can_call_llm(effective_config):
      return GeneratedDraft(
        text=local_draft(
          request.action,
          chapter.content,
          request.previous_paragraph,
          request.cursor_index,
        ),
        source="local",
      )

    previous_paragraph = previous_paragraph_for(
      chapter.content, request.previous_paragraph, request.cursor_index
    )
    prompt_build = await self._runtime.build_prompt(
      project_id,
      request_type,
      draft_runtime_input(project, chapter, request, author_preset, previous_paragraph),
    )
    response = await self._runtime.complete(
      project_id, request_type, effective_config, prompt_build
    )

    text = require_text_payload(response.payload, request_type=request_type)
    return GeneratedDraft(text=text, source="llm", model=response.model)

  async def generate_quick_draft(
    self, project_id: str, request: GenerateQuickDraftRequest
  ) -> GeneratedDraft:
    project = await self._project_service.get_manifest(project_id)
    chapter = await self._chapter_service.get_chapter(project_id, request.chapter_id)
    await self._presets.require_preset(
      project_id, "quick_generation_mode", request.quick_preset_id
    )
    author_preset = await self._presets.require_preset(
      project_id, "author_persona", request.author_preset_id
    )
    request_type = "quick_generate_next_paragraph"
    effective_config = await self._runtime.effective_config_for_request(
      project_id, request_type
    )
    if not self._runtime.can_call_llm(effective_config):
      return GeneratedDraft(
        text=local_draft(
          "next_paragraph",
          chapter.content,
          request.previous_paragraph,
          request.cursor_index,
        ),
        source="local",
      )

    previous_paragraph = previous_paragraph_for(
      chapter.content, request.previous_paragraph, request.cursor_index
    )
    prompt_build = await self._runtime.build_prompt(
      project_id,
      request_type,
      quick_runtime_input(project, chapter, request, author_preset, previous_paragraph),
    )
    response = await self._runtime.complete(
      project_id,
      request_type,
      effective_config,
      prompt_build,
    )

    text = require_text_payload(response.payload, request_type=request_type)
    return GeneratedDraft(text=text, source="llm", model=response.model)
