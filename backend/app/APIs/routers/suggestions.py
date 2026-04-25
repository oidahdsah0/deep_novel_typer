from __future__ import annotations

from fastapi import APIRouter, Depends

from app.APIs.dependencies import get_suggestion_queue_service
from app.Services.suggestion_queue_service import SuggestionQueueService
from app.Schemas.suggestions import DraftParagraphRequest, SuggestionCard

router = APIRouter()


@router.post("", response_model=list[SuggestionCard])
async def suggest_for_paragraph(
  project_id: str,
  request: DraftParagraphRequest,
  service: SuggestionQueueService = Depends(get_suggestion_queue_service),
) -> list[SuggestionCard]:
  return await service.request_suggestions(
    project_id,
    request.chapter_id,
    request.paragraph,
    perspective_id=request.perspective_id,
    trigger=request.trigger,
  )
