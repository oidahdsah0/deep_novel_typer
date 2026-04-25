from __future__ import annotations

from fastapi import APIRouter, Depends

from app.APIs.dependencies import get_prompt_preview_service
from app.Services.prompt_preview_service import PromptPreviewService
from app.Schemas.prompt_preview import PromptPreviewRequest, PromptPreviewResponse

router = APIRouter()


@router.post("", response_model=PromptPreviewResponse)
async def preview_prompt(
  project_id: str,
  request: PromptPreviewRequest,
  service: PromptPreviewService = Depends(get_prompt_preview_service),
) -> PromptPreviewResponse:
  return await service.preview(project_id, request)
