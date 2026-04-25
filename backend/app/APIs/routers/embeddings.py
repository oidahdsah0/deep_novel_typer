from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.APIs.dependencies import get_embedding_service
from app.Schemas.embeddings import (
  ClusterRequest,
  ClusterResponse,
  CreateEmbeddingTagRequest,
  EmbeddingProjectSettings,
  EmbeddingTag,
  HeatmapRequest,
  HeatmapResponse,
  UpdateEmbeddingProjectSettingsRequest,
  UpdateEmbeddingTagRequest,
)
from app.Services.embeddings import EmbeddingService

router = APIRouter()


@router.get("/embedding-tags", response_model=list[EmbeddingTag])
async def list_embedding_tags(
  project_id: str,
  service: EmbeddingService = Depends(get_embedding_service),
) -> list[EmbeddingTag]:
  return await service.list_tags(project_id)


@router.get("/embedding-settings", response_model=EmbeddingProjectSettings)
async def get_embedding_settings(
  project_id: str,
  service: EmbeddingService = Depends(get_embedding_service),
) -> EmbeddingProjectSettings:
  return await service.get_settings(project_id)


@router.patch("/embedding-settings", response_model=EmbeddingProjectSettings)
async def update_embedding_settings(
  project_id: str,
  request: UpdateEmbeddingProjectSettingsRequest,
  service: EmbeddingService = Depends(get_embedding_service),
) -> EmbeddingProjectSettings:
  return await service.update_settings(project_id, request)


@router.post(
  "/embedding-tags",
  response_model=EmbeddingTag,
  status_code=status.HTTP_201_CREATED,
)
async def create_embedding_tag(
  project_id: str,
  request: CreateEmbeddingTagRequest,
  service: EmbeddingService = Depends(get_embedding_service),
) -> EmbeddingTag:
  return await service.create_tag(project_id, request)


@router.patch("/embedding-tags/{tag_id}", response_model=EmbeddingTag)
async def update_embedding_tag(
  project_id: str,
  tag_id: str,
  request: UpdateEmbeddingTagRequest,
  service: EmbeddingService = Depends(get_embedding_service),
) -> EmbeddingTag:
  return await service.update_tag(project_id, tag_id, request)


@router.delete("/embedding-tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_embedding_tag(
  project_id: str,
  tag_id: str,
  service: EmbeddingService = Depends(get_embedding_service),
) -> Response:
  await service.delete_tag(project_id, tag_id)
  return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/embeddings/heatmap", response_model=HeatmapResponse)
async def build_embedding_heatmap(
  project_id: str,
  request: HeatmapRequest,
  service: EmbeddingService = Depends(get_embedding_service),
) -> HeatmapResponse:
  return await service.build_heatmap(project_id, request)


@router.post("/embeddings/clusters", response_model=ClusterResponse)
async def build_embedding_clusters(
  project_id: str,
  request: ClusterRequest,
  service: EmbeddingService = Depends(get_embedding_service),
) -> ClusterResponse:
  return await service.build_clusters(project_id, request)
