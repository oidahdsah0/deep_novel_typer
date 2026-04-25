from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.APIs.dependencies import get_project_service, get_workspace_service
from app.Services.project_service import ProjectService
from app.Services.workspace_service import WorkspaceService
from app.Schemas.common import ProjectStatus
from app.Schemas.projects import (
  CreateProjectRequest,
  ProjectDetail,
  ProjectSummary,
  UpdateProjectRequest,
)
from app.Schemas.workspace import WorkspaceSnapshot

router = APIRouter()


@router.get("", response_model=list[ProjectSummary])
async def list_projects(
  include_deleted: bool = False,
  status_filter: ProjectStatus | None = Query(default=None, alias="status"),
  q: str | None = None,
  service: ProjectService = Depends(get_project_service),
) -> list[ProjectSummary]:
  return await service.list_projects(include_deleted=include_deleted, status=status_filter, q=q)


@router.post("", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
async def create_project(
  request: CreateProjectRequest,
  service: ProjectService = Depends(get_project_service),
) -> ProjectDetail:
  return await service.create_project(request)


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
  project_id: str,
  service: ProjectService = Depends(get_project_service),
) -> ProjectDetail:
  return await service.get_manifest(project_id)


@router.patch("/{project_id}", response_model=ProjectDetail)
async def update_project(
  project_id: str,
  request: UpdateProjectRequest,
  service: ProjectService = Depends(get_project_service),
) -> ProjectDetail:
  return await service.update_project(project_id, request)


@router.post("/{project_id}/open", response_model=ProjectSummary)
async def open_project(
  project_id: str,
  service: ProjectService = Depends(get_project_service),
) -> ProjectSummary:
  return await service.mark_opened(project_id)


@router.delete("/{project_id}", response_model=ProjectSummary)
async def delete_project(
  project_id: str,
  service: ProjectService = Depends(get_project_service),
) -> ProjectSummary:
  return await service.trash_project(project_id)


@router.post("/{project_id}/restore", response_model=ProjectSummary)
async def restore_project(
  project_id: str,
  service: ProjectService = Depends(get_project_service),
) -> ProjectSummary:
  return await service.restore_project(project_id)


@router.get("/{project_id}/workspace", response_model=WorkspaceSnapshot)
async def get_project_workspace(
  project_id: str,
  chapter_id: str | None = None,
  service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceSnapshot:
  return await service.get_workspace(project_id, chapter_id=chapter_id)
