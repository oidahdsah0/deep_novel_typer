from __future__ import annotations

from app.Schemas.generation import GeneratedDraft, PolishSelectionRequest
from app.Services.chapter_service import ChapterService
from app.Services.project_service import ProjectService
from app.Services.structured_llm_service import require_text_payload

from .local_fallbacks import local_polish
from .preset_resolution import GenerationPresetResolver
from .request_inputs import polish_runtime_input
from .runtime import GenerationRuntime


class PolishGenerationActions:
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

  async def polish_selection(
    self, project_id: str, request: PolishSelectionRequest
  ) -> GeneratedDraft:
    project = await self._project_service.get_manifest(project_id)
    chapter = await self._chapter_service.get_chapter(project_id, request.chapter_id)
    await self._presets.require_preset(project_id, "polish_mode", request.polish_preset_id)
    request_type = "polish_selection"
    effective_config = await self._runtime.effective_config_for_request(
      project_id, request_type
    )
    if not self._runtime.can_call_llm(effective_config):
      return GeneratedDraft(text=local_polish(request.selected_text), source="local")

    prompt_build = await self._runtime.build_prompt(
      project_id,
      request_type,
      polish_runtime_input(project, chapter, request),
    )
    response = await self._runtime.complete(
      project_id, request_type, effective_config, prompt_build
    )

    text = require_text_payload(response.payload, request_type=request_type)
    return GeneratedDraft(text=text, source="llm", model=response.model)
