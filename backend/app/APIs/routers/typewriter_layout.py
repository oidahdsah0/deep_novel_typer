from __future__ import annotations

from fastapi import APIRouter, Depends

from app.APIs.dependencies import get_typewriter_layout_service
from app.Schemas.typewriter_layout import (
  TypewriterLayoutSettings,
  UpdateTypewriterLayoutSettingsRequest,
)
from app.Services.typewriter_layout import TypewriterLayoutService

router = APIRouter()


@router.get("", response_model=TypewriterLayoutSettings)
async def get_typewriter_layout_settings(
  service: TypewriterLayoutService = Depends(get_typewriter_layout_service),
) -> TypewriterLayoutSettings:
  return await service.get_settings()


@router.patch("", response_model=TypewriterLayoutSettings)
async def update_typewriter_layout_settings(
  request: UpdateTypewriterLayoutSettingsRequest,
  service: TypewriterLayoutService = Depends(get_typewriter_layout_service),
) -> TypewriterLayoutSettings:
  return await service.update_settings(request)
