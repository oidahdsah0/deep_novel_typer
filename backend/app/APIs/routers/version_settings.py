from __future__ import annotations

from fastapi import APIRouter, Depends

from app.APIs.dependencies import get_version_service
from app.Services.version_service import VersionService
from app.Schemas.versions import UpdateVersionSettingsRequest, VersionSettings

router = APIRouter()


@router.get("", response_model=VersionSettings)
async def get_version_settings(
  service: VersionService = Depends(get_version_service),
) -> VersionSettings:
  return await service.get_settings()


@router.patch("", response_model=VersionSettings)
async def update_version_settings(
  request: UpdateVersionSettingsRequest,
  service: VersionService = Depends(get_version_service),
) -> VersionSettings:
  return await service.update_settings(request)
