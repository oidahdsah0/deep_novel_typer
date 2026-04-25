from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.APIs.dependencies import get_perspective_service
from app.Services.perspective_service import PerspectiveService
from app.Schemas.perspectives import CreatePerspectiveRequest, Perspective, UpdatePerspectiveRequest

router = APIRouter()


@router.get("", response_model=list[Perspective])
async def list_perspectives(
  project_id: str,
  service: PerspectiveService = Depends(get_perspective_service),
) -> list[Perspective]:
  return await service.list_perspectives(project_id)


@router.post("", response_model=Perspective, status_code=status.HTTP_201_CREATED)
async def create_perspective(
  project_id: str,
  request: CreatePerspectiveRequest,
  service: PerspectiveService = Depends(get_perspective_service),
) -> Perspective:
  return await service.create_perspective(project_id, request)


@router.patch("/{perspective_id}", response_model=Perspective)
async def update_perspective(
  project_id: str,
  perspective_id: str,
  request: UpdatePerspectiveRequest,
  service: PerspectiveService = Depends(get_perspective_service),
) -> Perspective:
  return await service.update_perspective(project_id, perspective_id, request)


@router.delete("/{perspective_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_perspective(
  project_id: str,
  perspective_id: str,
  service: PerspectiveService = Depends(get_perspective_service),
) -> Response:
  await service.delete_perspective(project_id, perspective_id)
  return Response(status_code=status.HTTP_204_NO_CONTENT)
