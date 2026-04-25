from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.APIs.dependencies import get_project_search_service
from app.Services.search import ProjectSearchService
from app.Schemas.search import ProjectSearchResponse, ProjectSearchScope

router = APIRouter()


@router.get("", response_model=ProjectSearchResponse)
async def search_project(
  project_id: str,
  q: str = Query(default="", max_length=200),
  scope: ProjectSearchScope = Query(default="all"),
  limit: int = Query(default=50, ge=1, le=100),
  service: ProjectSearchService = Depends(get_project_search_service),
) -> ProjectSearchResponse:
  return await service.search_project(project_id, query=q, scope=scope, limit=limit)
