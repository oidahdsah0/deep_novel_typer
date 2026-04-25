from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.Schemas.common import EmbeddingSegmentationMode
from app.Schemas.embeddings import (
  ClusterRequest,
  ClusterResponse,
  CreateEmbeddingTagRequest,
  EmbeddingCacheStats,
  EmbeddingProjectSettings,
  EmbeddingTag,
  HeatmapRequest,
  HeatmapResponse,
  UpdateEmbeddingProjectSettingsRequest,
  UpdateEmbeddingTagRequest,
)
from app.Services.api_configs import APIConfigService, EffectiveAPIConfig
from app.Services.chapter_service import ChapterService
from app.Services.debug_log_service import DebugLogService
from app.Services.document_service import DocumentService
from app.Services.embeddings.analysis_service import EmbeddingAnalysisService
from app.Services.embeddings.cache_runtime import EmbeddingCacheRuntime
from app.Services.embeddings.chroma_store import ChromaEmbeddingStore
from app.Services.embeddings.model_runtime import OpenAIEmbeddingRuntime
from app.Services.embeddings.repository import EmbeddingRepository, _tag_from_row, settings_from_row
from app.Services.project_service import ProjectService
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityConflictError, EntityNotFoundError
from app.Utils.ids import slugify
from app.Utils.locks import AsyncLockRegistry


class EmbeddingService:
  def __init__(
    self,
    db: AsyncDatabase,
    locks: AsyncLockRegistry,
    project_service: ProjectService,
    chapter_service: ChapterService,
    document_service: DocumentService,
    api_config_service: APIConfigService,
    runtime: OpenAIEmbeddingRuntime,
    *,
    chroma_path: Path,
    debug_log_service: DebugLogService | None = None,
  ) -> None:
    self._db = db
    self._locks = locks
    self._project_service = project_service
    self._chapter_service = chapter_service
    self._document_service = document_service
    self._api_config_service = api_config_service
    self._repository = EmbeddingRepository(db)
    self._cache = EmbeddingCacheRuntime(
      ChromaEmbeddingStore(chroma_path),
      runtime,
      debug_log_service,
    )
    self._analysis = EmbeddingAnalysisService(
      db,
      project_service,
      chapter_service,
      document_service,
      api_config_service,
      self._repository,
      self._cache,
    )

  async def list_tags(self, project_id: str) -> list[EmbeddingTag]:
    await self._project_service.get_manifest(project_id)
    return await self._repository.list_tags(project_id)

  async def get_settings(self, project_id: str) -> EmbeddingProjectSettings:
    await self._project_service.get_manifest(project_id)
    row = await self._repository.fetch_project_settings_row(project_id)
    if row is not None:
      return settings_from_row(row)
    return EmbeddingProjectSettings(project_id=project_id)

  async def update_settings(
    self,
    project_id: str,
    request: UpdateEmbeddingProjectSettingsRequest,
  ) -> EmbeddingProjectSettings:
    await self._project_service.get_manifest(project_id)
    if request.api_config_id is not None:
      await self._require_embedding_config(request.api_config_id)

    now = _now()
    async with self._locks.get(f"{project_id}:embedding-settings"):
      async with self._db.transaction() as conn:
        await self._repository.upsert_project_settings(
          conn,
          project_id=project_id,
          api_config_id=request.api_config_id,
          segmentation_mode=request.segmentation_mode,
          segment_size=request.segment_size,
          algorithm=request.algorithm,
          now=now,
        )
      await self._project_service.touch_project(project_id, now)
    return await self.get_settings(project_id)

  async def create_tag(
    self, project_id: str, request: CreateEmbeddingTagRequest
  ) -> EmbeddingTag:
    await self._project_service.get_manifest(project_id)
    tag_id = slugify(request.name, fallback_prefix="embedding-tag")
    now = _now()
    async with self._locks.get(f"{project_id}:embedding-tags"):
      if await self._repository.tag_exists(project_id, tag_id):
        raise EntityConflictError(f"Embedding tag already exists: {tag_id}")
      async with self._db.transaction() as conn:
        await self._repository.insert_tag(
          conn,
          project_id=project_id,
          tag_id=tag_id,
          name=request.name,
          description=request.description,
          color=request.color,
          is_enabled=request.is_enabled,
          now=now,
        )
      await self._project_service.touch_project(project_id, now)
    return await self._require_tag(project_id, tag_id)

  async def update_tag(
    self, project_id: str, tag_id: str, request: UpdateEmbeddingTagRequest
  ) -> EmbeddingTag:
    await self._project_service.get_manifest(project_id)
    await self._require_tag(project_id, tag_id)
    updates = request.model_dump(exclude_unset=True)
    if not updates:
      return await self._require_tag(project_id, tag_id)

    now = _now()
    assignments: list[str] = []
    params: list[object] = []
    text_changed = False
    for field, value in updates.items():
      assignments.append(f"{field} = ?")
      params.append(int(value) if field == "is_enabled" else value)
      if field in {"name", "description"}:
        text_changed = True
    if text_changed:
      assignments.extend(
        [
          "embedding_config_id = NULL",
          "embedding_model_signature = NULL",
          "embedding_vector_ref = NULL",
        ]
      )
    assignments.append("updated_at = ?")
    params.append(now)

    async with self._locks.get(f"{project_id}:embedding-tags"):
      async with self._db.transaction() as conn:
        await self._repository.update_tag(
          conn,
          project_id=project_id,
          tag_id=tag_id,
          assignments=assignments,
          params=params,
        )
      await self._project_service.touch_project(project_id, now)
    return await self._require_tag(project_id, tag_id)

  async def delete_tag(self, project_id: str, tag_id: str) -> None:
    await self._project_service.get_manifest(project_id)
    await self._require_tag(project_id, tag_id)
    now = _now()
    async with self._locks.get(f"{project_id}:embedding-tags"):
      async with self._db.transaction() as conn:
        await self._repository.delete_tag(conn, project_id=project_id, tag_id=tag_id)
      await self._project_service.touch_project(project_id, now)

  async def cache_text_embeddings(
    self,
    *,
    project_id: str,
    api_config_id: str | None,
    segmentation_mode: EmbeddingSegmentationMode,
    texts: list[str],
    force_reembed: bool = False,
  ) -> EmbeddingCacheStats:
    await self._project_service.get_manifest(project_id)
    effective_config = await self._require_embedding_config(api_config_id)
    result = await self._cache.ensure_embeddings(
      effective_config=effective_config,
      project_id=project_id,
      segmentation_mode=segmentation_mode,
      texts=texts,
      force_reembed=force_reembed,
    )
    return result.stats

  async def build_heatmap(self, project_id: str, request: HeatmapRequest) -> HeatmapResponse:
    return await self._analysis.build_heatmap(project_id, request)

  async def build_clusters(self, project_id: str, request: ClusterRequest) -> ClusterResponse:
    return await self._analysis.build_clusters(project_id, request)

  async def _require_tag(self, project_id: str, tag_id: str) -> EmbeddingTag:
    row = await self._repository.fetch_tag_row(project_id, tag_id)
    if row is None:
      raise EntityNotFoundError(f"Embedding tag not found: {tag_id}")
    return _tag_from_row(row)

  async def _require_embedding_config(
    self, api_config_id: str | None
  ) -> EffectiveAPIConfig:
    effective_config = await self._api_config_service.get_effective_config(
      api_config_id,
      kind="embedding",
    )
    if effective_config is None:
      raise EntityNotFoundError("Embedding API config not found.")
    return effective_config


def _now() -> str:
  return datetime.now(UTC).isoformat()
