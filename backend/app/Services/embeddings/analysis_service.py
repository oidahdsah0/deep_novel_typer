from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from app.Schemas.embeddings import (
  ClusterRequest,
  ClusterResponse,
  EmbeddingTag,
  HeatmapItem,
  HeatmapRequest,
  HeatmapResponse,
)
from app.Services.api_configs import APIConfigService, EffectiveAPIConfig
from app.Services.chapter_service import ChapterService
from app.Services.debug_log_service import EmbeddingDebugContext
from app.Services.document_service import DocumentService
from app.Services.embeddings.cache import EmbeddingModelSignature, build_model_signature
from app.Services.embeddings.cache_runtime import CachedEmbeddingBatch, EmbeddingCacheRuntime
from app.Services.embeddings.analysis_rows import cluster_item_rows, heatmap_item_rows
from app.Services.embeddings.clustering import ClusterTagVector, build_fixed_tag_clusters
from app.Services.embeddings.heatmap import TagVector, build_heatmap_items
from app.Services.embeddings.repository import EmbeddingRepository
from app.Services.embeddings.segmentation import TextSegment, segment_text
from app.Services.project_service import ProjectService
from app.Utils.db import AsyncDatabase
from app.Utils.errors import DomainError, EntityNotFoundError


class EmbeddingAnalysisService:
  def __init__(
    self,
    db: AsyncDatabase,
    project_service: ProjectService,
    chapter_service: ChapterService,
    document_service: DocumentService,
    api_config_service: APIConfigService,
    repository: EmbeddingRepository,
    cache: EmbeddingCacheRuntime,
  ) -> None:
    self._db = db
    self._project_service = project_service
    self._chapter_service = chapter_service
    self._document_service = document_service
    self._api_config_service = api_config_service
    self._repository = repository
    self._cache = cache

  async def build_heatmap(self, project_id: str, request: HeatmapRequest) -> HeatmapResponse:
    prepared = await self._prepare(project_id, request, tool_type="heatmap")
    if not prepared.segments:
      prepared.warnings.append("分析范围内没有可用于 Embedding 的分词。")
      token_embeddings = CachedEmbeddingBatch.empty(prepared.signature)
      items: list[HeatmapItem] = []
    else:
      token_embeddings = await self._token_embeddings(project_id, request, prepared, "heatmap")
      items = build_heatmap_items(
        prepared.segments,
        token_embeddings.vectors,
        [
          TagVector(tag_id=tag.id, vector=vector)
          for tag, vector in zip(prepared.tags, prepared.tag_embeddings.vectors, strict=True)
        ],
        request.algorithm,
      )

    await self._insert_run_and_items(
      project_id=project_id,
      request=request,
      prepared=prepared,
      tool_type="heatmap",
      params={
        "tag_ids": [tag.id for tag in prepared.tags],
        "range": request.range.model_dump() if request.range else None,
        "segment_size": request.segment_size,
        "force_reembed": request.force_reembed,
      },
      rows=heatmap_item_rows(prepared.run_id, items, token_embeddings.cache_ids),
    )
    return HeatmapResponse(
      run_id=prepared.run_id,
      status="success",
      resource_type=request.resource_type,
      resource_id=request.resource_id,
      model_signature=prepared.signature.value,
      model_signature_hash=prepared.signature.hash,
      segmentation_mode=request.segmentation_mode,
      segment_size=request.segment_size,
      algorithm=request.algorithm,
      tags=prepared.tags,
      items=items,
      token_cache=token_embeddings.stats,
      tag_cache=prepared.tag_embeddings.stats,
      warnings=prepared.warnings,
    )

  async def build_clusters(self, project_id: str, request: ClusterRequest) -> ClusterResponse:
    prepared = await self._prepare(project_id, request, tool_type="clusters")
    if len(prepared.tags) < 2:
      prepared.warnings.append("语言簇至少需要 2 个标签才能形成对比；当前仅显示单簇归属。")

    if not prepared.segments:
      prepared.warnings.append("分析范围内没有可用于 Embedding 的分词。")
      token_embeddings = CachedEmbeddingBatch.empty(prepared.signature)
      cluster_result = build_fixed_tag_clusters(
        [],
        [],
        _cluster_tag_vectors(prepared.tags, prepared.tag_embeddings.vectors),
        request.algorithm,
      )
    else:
      token_embeddings = await self._token_embeddings(project_id, request, prepared, "clusters")
      cluster_result = build_fixed_tag_clusters(
        prepared.segments,
        token_embeddings.vectors,
        _cluster_tag_vectors(prepared.tags, prepared.tag_embeddings.vectors),
        request.algorithm,
      )

    await self._insert_run_and_items(
      project_id=project_id,
      request=request,
      prepared=prepared,
      tool_type="clusters",
      params={
        "tag_ids": [tag.id for tag in prepared.tags],
        "range": request.range.model_dump() if request.range else None,
        "segment_size": request.segment_size,
        "force_reembed": request.force_reembed,
        "cluster_mode": request.cluster_mode,
        "projection": "pca",
      },
      rows=cluster_item_rows(prepared.run_id, cluster_result.points, token_embeddings.cache_ids),
    )
    return ClusterResponse(
      run_id=prepared.run_id,
      status="success",
      resource_type=request.resource_type,
      resource_id=request.resource_id,
      model_signature=prepared.signature.value,
      model_signature_hash=prepared.signature.hash,
      segmentation_mode=request.segmentation_mode,
      segment_size=request.segment_size,
      algorithm=request.algorithm,
      cluster_mode=request.cluster_mode,
      tags=prepared.tags,
      points=cluster_result.points,
      clusters=cluster_result.clusters,
      tag_anchors=cluster_result.tag_anchors,
      token_cache=token_embeddings.stats,
      tag_cache=prepared.tag_embeddings.stats,
      warnings=prepared.warnings,
    )

  async def _prepare(self, project_id: str, request, *, tool_type: str):
    await self._project_service.get_manifest(project_id)
    tags = await self._selected_tags(project_id, request.tag_ids)
    if not tags:
      raise DomainError(f"At least one embedding tag is required for {tool_type} analysis.")

    resource_text = await self._resource_text(project_id, request.resource_type, request.resource_id)
    selected_text, offset_base = _apply_range(resource_text, request.range)
    source_hash = _content_hash(
      resource_text,
      request.range.start_offset if request.range else None,
      request.range.end_offset if request.range else None,
    )
    segments = _offset_segments(
      segment_text(selected_text, request.segmentation_mode, request.segment_size),
      offset_base,
    )

    run_id = f"embedding-run-{uuid4().hex[:12]}"
    effective_config = await self._require_embedding_config(request.api_config_id)
    signature = build_model_signature(effective_config.config)
    tag_embeddings = await self._cache.ensure_embeddings(
      effective_config=effective_config,
      project_id=project_id,
      segmentation_mode="sentence",
      texts=[_tag_embedding_text(tag) for tag in tags],
      force_reembed=request.force_reembed,
      debug_context=_embedding_debug_context(
        effective_config,
        project_id=project_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        algorithm=request.algorithm,
        run_id=run_id,
        tool_type=tool_type,
        batch_label="tags",
      ),
    )
    await self._persist_tag_embedding_refs(
      project_id,
      tags,
      effective_config.config.id,
      signature,
      tag_embeddings.cache_ids,
    )
    return _PreparedAnalysis(
      run_id=run_id,
      source_hash=source_hash,
      tags=tags,
      segments=segments,
      effective_config=effective_config,
      signature=signature,
      tag_embeddings=tag_embeddings,
      warnings=[],
    )

  async def _token_embeddings(
    self,
    project_id: str,
    request,
    prepared,
    tool_type: str,
  ) -> CachedEmbeddingBatch:
    return await self._cache.ensure_embeddings(
      effective_config=prepared.effective_config,
      project_id=project_id,
      segmentation_mode=request.segmentation_mode,
      texts=[segment.normalized_text for segment in prepared.segments],
      force_reembed=request.force_reembed,
      debug_context=_embedding_debug_context(
        prepared.effective_config,
        project_id=project_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        algorithm=request.algorithm,
        run_id=prepared.run_id,
        tool_type=tool_type,
        batch_label="tokens",
      ),
    )

  async def _insert_run_and_items(
    self,
    *,
    project_id: str,
    request,
    prepared,
    tool_type: str,
    params: dict[str, object],
    rows: list[tuple[object, ...]],
  ) -> None:
    async with self._db.transaction() as conn:
      await self._repository.insert_run(
        conn,
        run_id=prepared.run_id,
        project_id=project_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        tool_type=tool_type,  # type: ignore[arg-type]
        status="success",
        embedding_config_id=prepared.effective_config.config.id,
        model_signature=prepared.signature.value,
        segmentation_mode=request.segmentation_mode,
        algorithm=request.algorithm,
        params=params,
        source_content_hash=prepared.source_hash,
        error_message=None,
        now=_now(),
      )
      await self._repository.insert_items(conn, run_id=prepared.run_id, rows=rows)

  async def _selected_tags(self, project_id: str, tag_ids: list[str]) -> list[EmbeddingTag]:
    tags = await self._repository.list_tags(project_id)
    by_id = {tag.id: tag for tag in tags}
    if tag_ids:
      missing = [tag_id for tag_id in tag_ids if tag_id not in by_id]
      if missing:
        raise EntityNotFoundError(f"Embedding tag not found: {missing[0]}")
      return [by_id[tag_id] for tag_id in tag_ids]
    return [tag for tag in tags if tag.is_enabled]

  async def _resource_text(
    self, project_id: str, resource_type: str, resource_id: str
  ) -> str:
    if resource_type == "chapter":
      return (await self._chapter_service.get_chapter(project_id, resource_id)).content
    if resource_type == "document":
      return (await self._document_service.get_document(project_id, resource_id)).content
    raise DomainError(f"Unsupported embedding resource type: {resource_type}")

  async def _persist_tag_embedding_refs(
    self,
    project_id: str,
    tags: list[EmbeddingTag],
    embedding_config_id: str,
    signature: EmbeddingModelSignature,
    cache_ids: list[str],
  ) -> None:
    async with self._db.transaction() as conn:
      for tag, cache_id in zip(tags, cache_ids, strict=True):
        await self._repository.update_tag_embedding_ref(
          conn,
          project_id=project_id,
          tag_id=tag.id,
          embedding_config_id=embedding_config_id,
          model_signature=signature.value,
          vector_ref=cache_id,
          now=_now(),
        )

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


class _PreparedAnalysis:
  def __init__(
    self,
    *,
    run_id: str,
    source_hash: str,
    tags: list[EmbeddingTag],
    segments: list[TextSegment],
    effective_config: EffectiveAPIConfig,
    signature: EmbeddingModelSignature,
    tag_embeddings: CachedEmbeddingBatch,
    warnings: list[str],
  ) -> None:
    self.run_id = run_id
    self.source_hash = source_hash
    self.tags = tags
    self.segments = segments
    self.effective_config = effective_config
    self.signature = signature
    self.tag_embeddings = tag_embeddings
    self.warnings = warnings


def _offset_segments(segments: list[TextSegment], offset_base: int) -> list[TextSegment]:
  return [
    segment.__class__(
      token_index=segment.token_index,
      text=segment.text,
      normalized_text=segment.normalized_text,
      start_offset=segment.start_offset + offset_base,
      end_offset=segment.end_offset + offset_base,
      segmentation_mode=segment.segmentation_mode,
    )
    for segment in segments
  ]


def _embedding_debug_context(
  effective_config: EffectiveAPIConfig,
  *,
  project_id: str,
  resource_type: str,
  resource_id: str,
  algorithm: str,
  run_id: str,
  tool_type: str,
  batch_label: str,
) -> EmbeddingDebugContext:
  config = effective_config.config
  return EmbeddingDebugContext(
    project_id=project_id,
    request_type=f"embedding_{tool_type}_{batch_label}",
    api_config_id=config.id,
    provider=config.provider,
    model=config.model,
    tool_type=tool_type,
    resource_type=resource_type,
    resource_id=resource_id,
    run_id=run_id,
    algorithm=algorithm,
    batch_label=batch_label,
  )


def _apply_range(text: str, text_range) -> tuple[str, int]:
  if text_range is None:
    return text, 0
  start = text_range.start_offset if text_range.start_offset is not None else 0
  end = text_range.end_offset if text_range.end_offset is not None else len(text)
  if end < start:
    raise DomainError("Embedding range end_offset must be greater than or equal to start_offset.")
  if start > len(text) or end > len(text):
    raise DomainError("Embedding range exceeds resource text length.")
  return text[start:end], start


def _content_hash(text: str, start_offset: int | None, end_offset: int | None) -> str:
  payload = json.dumps(
    {"text": text, "start_offset": start_offset, "end_offset": end_offset},
    ensure_ascii=False,
    sort_keys=True,
  )
  return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _tag_embedding_text(tag: EmbeddingTag) -> str:
  if tag.description:
    return f"{tag.name}\n{tag.description}"
  return tag.name


def _cluster_tag_vectors(
  tags: list[EmbeddingTag],
  vectors: list[list[float]],
) -> list[ClusterTagVector]:
  return [
    ClusterTagVector(tag=tag, vector=vector)
    for tag, vector in zip(tags, vectors, strict=True)
  ]


def _now() -> str:
  return datetime.now(UTC).isoformat()
