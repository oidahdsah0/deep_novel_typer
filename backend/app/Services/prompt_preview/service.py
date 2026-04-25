from __future__ import annotations

from app.Schemas.prompt_preview import (
  PromptPreviewRequest,
  PromptPreviewResponse,
)
from app.Services.api_configs import APIConfigService
from app.Services.chapter_service import ChapterService
from app.Services.document_service import DocumentService
from app.Services.perspective_service import PerspectiveService
from app.Services.prompt_profiles import PromptProfileService
from app.Services.project_service import ProjectService

from .preview_items import PromptPreviewItemBuilder
from .request_inputs import PromptPreviewInputBuilder, PreviewInput
from .request_options import PromptPreviewConfigResolver


class PromptPreviewService:
  def __init__(
    self,
    project_service: ProjectService,
    chapter_service: ChapterService,
    document_service: DocumentService,
    perspective_service: PerspectiveService,
    prompt_profile_service: PromptProfileService,
    api_config_service: APIConfigService,
  ) -> None:
    self._inputs = PromptPreviewInputBuilder(
      project_service,
      chapter_service,
      document_service,
      perspective_service,
    )
    self._configs = PromptPreviewConfigResolver(
      prompt_profile_service,
      api_config_service,
    )
    self._items = PromptPreviewItemBuilder(prompt_profile_service, self._configs)

  async def preview(
    self, project_id: str, request: PromptPreviewRequest
  ) -> PromptPreviewResponse:
    if request.request_type == "perspective_suggestion":
      inputs, response_warnings = await self._inputs.perspective_inputs(
        project_id, request
      )
    else:
      inputs = [await self._inputs.single_request_input(project_id, request)]
      response_warnings = []

    items = [
      await self._items.build_item(
        project_id=project_id,
        preview_input=preview_input,
        effective_config=await self._effective_config(
          project_id,
          preview_input,
          request,
        ),
        request=request,
      )
      for preview_input in inputs
    ]
    return PromptPreviewResponse(
      request_type=request.request_type,
      items=items,
      warnings=response_warnings,
    )

  async def _effective_config(
    self,
    project_id: str,
    preview_input: PreviewInput,
    request: PromptPreviewRequest,
  ):
    if preview_input.perspective is not None:
      return await self._configs.effective_config_for_perspective(
        project_id,
        preview_input.perspective,
        request,
      )
    return await self._configs.effective_config_for_request(
      project_id,
      preview_input.request_type,
      request,
    )
