from __future__ import annotations

from app.Schemas.generation import GenerateChapterBlueprintRequest, GeneratedChapterBlueprint
from app.Services.chapter_service import ChapterService
from app.Services.project_service import ProjectService

from .local_fallbacks import local_blueprint_points, require_blueprint_points
from .preset_resolution import GenerationPresetResolver
from .request_inputs import blueprint_runtime_input, previous_paragraph_for
from .runtime import GenerationRuntime


class BlueprintGenerationActions:
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

  async def generate_chapter_blueprint(
    self, project_id: str, request: GenerateChapterBlueprintRequest
  ) -> GeneratedChapterBlueprint:
    project = await self._project_service.get_manifest(project_id)
    chapter = await self._chapter_service.get_chapter(project_id, request.chapter_id)
    await self._presets.require_preset(
      project_id, "chapter_blueprint_mode", request.blueprint_preset_id
    )
    author_preset = await self._presets.require_preset(
      project_id, "author_persona", request.author_preset_id
    )
    request_type = "generate_chapter_blueprint"
    effective_config = await self._runtime.effective_config_for_request(
      project_id, request_type
    )
    if not self._runtime.can_call_llm(effective_config):
      return GeneratedChapterBlueprint(
        points=local_blueprint_points(chapter.title, request.blueprint_prompt),
        source="local",
      )

    previous_paragraph = previous_paragraph_for(
      chapter.content, request.previous_paragraph, request.cursor_index
    )
    prompt_build = await self._runtime.build_prompt(
      project_id,
      request_type,
      blueprint_runtime_input(project, chapter, request, author_preset, previous_paragraph),
    )
    response = await self._runtime.complete(
      project_id, request_type, effective_config, prompt_build
    )

    return GeneratedChapterBlueprint(
      points=require_blueprint_points(response.payload, request_type=request_type),
      source="llm",
      model=response.model,
    )
