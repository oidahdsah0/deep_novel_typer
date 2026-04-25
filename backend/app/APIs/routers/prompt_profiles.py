from __future__ import annotations

from fastapi import APIRouter, Depends

from app.APIs.dependencies import get_prompt_profile_service
from app.Services.prompt_profiles import PromptProfileService
from app.Schemas.common import PromptRequestType
from app.Schemas.prompt_profiles import (
  PromptProfile,
  PromptProfileLibrary,
  PromptProfileVersion,
  PromptProfileVersionDetail,
  RestorePromptProfileVersionResponse,
  UpdatePromptProfileRequest,
)

router = APIRouter()


@router.get("", response_model=PromptProfileLibrary)
async def list_prompt_profiles(
  project_id: str,
  service: PromptProfileService = Depends(get_prompt_profile_service),
) -> PromptProfileLibrary:
  return await service.list_profiles(project_id)


@router.put("/{request_type}", response_model=PromptProfile)
async def update_prompt_profile(
  project_id: str,
  request_type: PromptRequestType,
  request: UpdatePromptProfileRequest,
  service: PromptProfileService = Depends(get_prompt_profile_service),
) -> PromptProfile:
  return await service.update_profile(project_id, request_type, request)


@router.get("/{request_type}/versions", response_model=list[PromptProfileVersion])
async def list_prompt_profile_versions(
  project_id: str,
  request_type: PromptRequestType,
  service: PromptProfileService = Depends(get_prompt_profile_service),
) -> list[PromptProfileVersion]:
  return await service.list_versions(project_id, request_type)


@router.get("/{request_type}/versions/{version_id}", response_model=PromptProfileVersionDetail)
async def get_prompt_profile_version(
  project_id: str,
  request_type: PromptRequestType,
  version_id: str,
  service: PromptProfileService = Depends(get_prompt_profile_service),
) -> PromptProfileVersionDetail:
  return await service.get_version(project_id, request_type, version_id)


@router.post(
  "/{request_type}/versions/{version_id}/restore",
  response_model=RestorePromptProfileVersionResponse,
)
async def restore_prompt_profile_version(
  project_id: str,
  request_type: PromptRequestType,
  version_id: str,
  service: PromptProfileService = Depends(get_prompt_profile_service),
) -> RestorePromptProfileVersionResponse:
  return await service.restore_version(project_id, request_type, version_id)
