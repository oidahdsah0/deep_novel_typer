from __future__ import annotations

from fastapi import APIRouter, Depends

from app.APIs.dependencies import get_library_service
from app.Services.library_service import LibraryService
from app.Schemas.workspace import LibrarySnapshot

router = APIRouter()


@router.get("", response_model=LibrarySnapshot)
async def get_library(
  service: LibraryService = Depends(get_library_service),
) -> LibrarySnapshot:
  return await service.get_library()
