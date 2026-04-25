from __future__ import annotations

from app.Schemas.generation import (
  GenerateDocumentContinuationRequest,
  GeneratedDraft,
  PolishDocumentSelectionRequest,
)
from app.Services.document_service import DocumentService
from app.Services.chapter_service import ChapterService
from app.Services.project_service import ProjectService
from app.Services.structured_llm_service import require_text_payload

from .local_fallbacks import local_document_continuation, local_polish
from .preset_resolution import GenerationPresetResolver
from .request_inputs import (
  document_continuation_runtime_input,
  document_polish_runtime_input,
)
from .runtime import GenerationRuntime


class DocumentGenerationActions:
  def __init__(
    self,
    project_service: ProjectService,
    document_service: DocumentService,
    chapter_service: ChapterService,
    presets: GenerationPresetResolver,
    runtime: GenerationRuntime,
  ) -> None:
    self._project_service = project_service
    self._document_service = document_service
    self._chapter_service = chapter_service
    self._presets = presets
    self._runtime = runtime

  async def polish_document_selection(
    self, project_id: str, request: PolishDocumentSelectionRequest
  ) -> GeneratedDraft:
    project = await self._project_service.get_manifest(project_id)
    document = await self._document_service.get_document(project_id, request.document_id)
    chapter = await self._request_chapter(project_id, request.chapter_id)
    await self._presets.require_preset(
      project_id, "document_polish_mode", request.polish_preset_id
    )
    editor_preset = await self._presets.require_preset(
      project_id, "editor_persona", request.editor_preset_id
    )
    request_type = "polish_document_selection"
    effective_config = await self._runtime.effective_config_for_request(
      project_id, request_type
    )
    if not self._runtime.can_call_llm(effective_config):
      return GeneratedDraft(text=local_polish(request.selected_text), source="local")

    prompt_build = await self._runtime.build_prompt(
      project_id,
      request_type,
      document_polish_runtime_input(project, document, request, editor_preset, chapter),
    )
    response = await self._runtime.complete(
      project_id, request_type, effective_config, prompt_build
    )

    text = require_text_payload(response.payload, request_type=request_type)
    return GeneratedDraft(text=text, source="llm", model=response.model)

  async def generate_document_continuation(
    self, project_id: str, request: GenerateDocumentContinuationRequest
  ) -> GeneratedDraft:
    project = await self._project_service.get_manifest(project_id)
    document = await self._document_service.get_document(project_id, request.document_id)
    chapter = await self._request_chapter(project_id, request.chapter_id)
    await self._presets.require_preset(
      project_id, "document_generation_mode", request.generation_preset_id
    )
    editor_preset = await self._presets.require_preset(
      project_id, "editor_persona", request.editor_preset_id
    )
    request_type = "generate_document_continuation"
    effective_config = await self._runtime.effective_config_for_request(
      project_id, request_type
    )
    if not self._runtime.can_call_llm(effective_config):
      return GeneratedDraft(
        text=local_document_continuation(document.content), source="local"
      )

    prompt_build = await self._runtime.build_prompt(
      project_id,
      request_type,
      document_continuation_runtime_input(project, document, request, editor_preset, chapter),
    )
    response = await self._runtime.complete(
      project_id, request_type, effective_config, prompt_build
    )

    text = require_text_payload(response.payload, request_type=request_type)
    return GeneratedDraft(text=text, source="llm", model=response.model)

  async def _request_chapter(self, project_id: str, chapter_id: str | None):
    if not chapter_id:
      return None
    return await self._chapter_service.get_chapter(project_id, chapter_id)
