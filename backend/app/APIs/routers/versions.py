from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.APIs.dependencies import get_version_service
from app.Services.version_service import VersionService
from app.Schemas.common import VersionedResourceType
from app.Schemas.versions import (
  CreateResourceVersionRequest,
  ResourceVersion,
  ResourceVersionDetail,
  RestoreResourceVersionResponse,
)

router = APIRouter()


@router.get("", response_model=list[ResourceVersion])
async def list_versions(
  project_id: str,
  resource_type: VersionedResourceType = Query(...),
  resource_id: str = Query(..., min_length=1, max_length=120),
  service: VersionService = Depends(get_version_service),
) -> list[ResourceVersion]:
  return await service.list_versions(project_id, resource_type, resource_id)


@router.post("", response_model=ResourceVersion, status_code=status.HTTP_201_CREATED)
async def create_version(
  project_id: str,
  request: CreateResourceVersionRequest,
  service: VersionService = Depends(get_version_service),
) -> ResourceVersion:
  return await service.create_current_version(
    project_id,
    request.resource_type,
    request.resource_id,
    version_type=request.version_type,
    label=request.label,
    note=request.note,
  )


@router.get("/{version_id}", response_model=ResourceVersionDetail)
async def get_version(
  project_id: str,
  version_id: str,
  service: VersionService = Depends(get_version_service),
) -> ResourceVersionDetail:
  return await service.get_version(project_id, version_id)


@router.post("/{version_id}/restore", response_model=RestoreResourceVersionResponse)
async def restore_version(
  project_id: str,
  version_id: str,
  service: VersionService = Depends(get_version_service),
) -> RestoreResourceVersionResponse:
  return await service.restore_version(project_id, version_id)
