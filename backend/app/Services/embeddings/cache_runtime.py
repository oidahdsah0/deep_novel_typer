from __future__ import annotations

import asyncio
import hashlib
from time import perf_counter

from app.Schemas.common import EmbeddingSegmentationMode
from app.Schemas.embeddings import EmbeddingCacheStats
from app.Services.api_configs import EffectiveAPIConfig
from app.Services.debug_log_service import DebugLogService, EmbeddingDebugContext
from app.Services.embeddings.cache import (
  EmbeddingModelSignature,
  build_model_signature,
  embedding_cache_id,
  embedding_collection_name,
  normalize_embedding_text,
)
from app.Services.embeddings.chroma_store import CachedEmbedding, ChromaEmbeddingStore
from app.Services.embeddings.model_runtime import OpenAIEmbeddingRuntime


class CachedEmbeddingBatch:
  def __init__(
    self,
    *,
    normalized_texts: list[str],
    cache_ids: list[str],
    vectors: list[list[float]],
    stats: EmbeddingCacheStats,
    model_signature: EmbeddingModelSignature,
  ) -> None:
    self.normalized_texts = normalized_texts
    self.cache_ids = cache_ids
    self.vectors = vectors
    self.stats = stats
    self.model_signature = model_signature

  @classmethod
  def empty(cls, model_signature: EmbeddingModelSignature) -> "CachedEmbeddingBatch":
    return cls(
      normalized_texts=[],
      cache_ids=[],
      vectors=[],
      stats=EmbeddingCacheStats(
        requested_count=0,
        unique_count=0,
        cache_hit_count=0,
        cache_miss_count=0,
      ),
      model_signature=model_signature,
    )


class EmbeddingCacheRuntime:
  def __init__(
    self,
    store: ChromaEmbeddingStore,
    runtime: OpenAIEmbeddingRuntime,
    debug_log_service: DebugLogService | None = None,
  ) -> None:
    self._store = store
    self._runtime = runtime
    self._debug_log_service = debug_log_service
    self._inflight_lock = asyncio.Lock()
    self._inflight: dict[str, asyncio.Future[CachedEmbedding]] = {}

  async def ensure_embeddings(
    self,
    *,
    effective_config: EffectiveAPIConfig,
    project_id: str,
    segmentation_mode: EmbeddingSegmentationMode,
    texts: list[str],
    force_reembed: bool,
    debug_context: EmbeddingDebugContext | None = None,
  ) -> CachedEmbeddingBatch:
    normalized_inputs = [
      normalized for text in texts if (normalized := normalize_embedding_text(text))
    ]
    normalized_unique = _unique_normalized_texts(normalized_inputs)
    signature = build_model_signature(effective_config.config)
    collection_name = embedding_collection_name(project_id, signature.hash)
    unique_cache_ids = [
      embedding_cache_id(project_id, signature.hash, segmentation_mode, text) for text in normalized_unique
    ]
    cached = (
      {}
      if force_reembed
      else await self._store.get_embeddings(collection_name, unique_cache_ids)
    )
    cache_hit_count = len(cached)
    missing_pairs = [
      (cache_id, text)
      for cache_id, text in zip(unique_cache_ids, normalized_unique, strict=True)
      if cache_id not in cached
    ]
    if missing_pairs:
      cached.update(await self._fill_missing_single_flight(
        effective_config=effective_config,
        collection_name=collection_name,
        project_id=project_id,
        signature=signature,
        segmentation_mode=segmentation_mode,
        missing_pairs=missing_pairs,
        debug_context=debug_context,
        requested_count=len(texts),
        unique_count=len(normalized_unique),
        cache_hit_count=cache_hit_count,
        cache_miss_count=len(missing_pairs),
      ))
    vector_by_text = {
      text: cached[cache_id].embedding
      for text, cache_id in zip(normalized_unique, unique_cache_ids, strict=True)
    }
    cache_id_by_text = dict(zip(normalized_unique, unique_cache_ids, strict=True))
    return CachedEmbeddingBatch(
      normalized_texts=normalized_inputs,
      cache_ids=[cache_id_by_text[text] for text in normalized_inputs],
      vectors=[vector_by_text[text] for text in normalized_inputs],
      stats=EmbeddingCacheStats(
        requested_count=len(texts),
        unique_count=len(normalized_unique),
        cache_hit_count=cache_hit_count,
        cache_miss_count=len(missing_pairs),
      ),
      model_signature=signature,
    )

  async def _fill_missing_single_flight(
    self,
    *,
    effective_config: EffectiveAPIConfig,
    collection_name: str,
    project_id: str,
    signature: EmbeddingModelSignature,
    segmentation_mode: EmbeddingSegmentationMode,
    missing_pairs: list[tuple[str, str]],
    debug_context: EmbeddingDebugContext | None,
    requested_count: int,
    unique_count: int,
    cache_hit_count: int,
    cache_miss_count: int,
  ) -> dict[str, CachedEmbedding]:
    owned: list[tuple[str, str, str, asyncio.Future[CachedEmbedding]]] = []
    waiting: dict[str, asyncio.Future[CachedEmbedding]] = {}
    async with self._inflight_lock:
      loop = asyncio.get_running_loop()
      for cache_id, text in missing_pairs:
        key = _inflight_key(collection_name, cache_id)
        future = self._inflight.get(key)
        if future is None:
          future = loop.create_future()
          self._inflight[key] = future
          owned.append((key, cache_id, text, future))
        else:
          waiting[cache_id] = future

    resolved: dict[str, CachedEmbedding] = {}
    if owned:
      owned_pairs = [(cache_id, text) for _key, cache_id, text, _future in owned]
      try:
        generated = await self._fill_missing(
          effective_config=effective_config,
          collection_name=collection_name,
          project_id=project_id,
          signature=signature,
          segmentation_mode=segmentation_mode,
          missing_pairs=owned_pairs,
          debug_context=debug_context,
          requested_count=requested_count,
          unique_count=unique_count,
          cache_hit_count=cache_hit_count,
          cache_miss_count=cache_miss_count,
        )
      except Exception as exc:
        for _key, _cache_id, _text, future in owned:
          if not future.done():
            future.set_exception(exc)
            future.exception()
        raise
      else:
        for _key, cache_id, _text, future in owned:
          embedding = generated[cache_id]
          resolved[cache_id] = embedding
          if not future.done():
            future.set_result(embedding)
      finally:
        async with self._inflight_lock:
          for key, _cache_id, _text, future in owned:
            if self._inflight.get(key) is future:
              self._inflight.pop(key, None)

    for cache_id, future in waiting.items():
      resolved[cache_id] = await future
    return resolved

  async def _fill_missing(
    self,
    *,
    effective_config: EffectiveAPIConfig,
    collection_name: str,
    project_id: str,
    signature: EmbeddingModelSignature,
    segmentation_mode: EmbeddingSegmentationMode,
    missing_pairs: list[tuple[str, str]],
    debug_context: EmbeddingDebugContext | None,
    requested_count: int,
    unique_count: int,
    cache_hit_count: int,
    cache_miss_count: int,
  ) -> dict[str, CachedEmbedding]:
    missing_ids = [cache_id for cache_id, _text in missing_pairs]
    missing_texts = [text for _cache_id, text in missing_pairs]
    metadatas = [
      {
        "model_signature": signature.value,
        "model_signature_hash": signature.hash,
        "project_id": project_id,
        "api_config_id": effective_config.config.id,
        "segmentation_mode": segmentation_mode,
        "normalized_text": text,
      }
      for text in missing_texts
    ]
    request_body = _debug_request_body(
      effective_config=effective_config,
      project_id=project_id,
      signature=signature,
      segmentation_mode=segmentation_mode,
      missing_texts=missing_texts,
      debug_context=debug_context,
      requested_count=requested_count,
      unique_count=unique_count,
      cache_hit_count=cache_hit_count,
      cache_miss_count=cache_miss_count,
    )
    started_at = perf_counter()
    try:
      result = await self._runtime.embed_texts(
        effective_config,
        missing_texts,
        label=debug_context.request_type if debug_context else "embedding_cache_fill",
      )
    except Exception as exc:
      await self._record_debug(
        debug_context,
        request_body=request_body,
        response_body=_debug_error_body(exc, started_at),
        status="error",
        error_message=str(exc),
        prompt_tokens=None,
        total_tokens=None,
        duration_ms=_duration_ms(started_at),
      )
      raise
    await self._record_debug(
      debug_context,
      request_body=request_body,
      response_body=_debug_response_body(result),
      status="success",
      error_message=None,
      prompt_tokens=result.prompt_tokens,
      total_tokens=result.total_tokens,
      duration_ms=result.duration_ms,
    )
    await self._store.upsert_embeddings(
      collection_name,
      ids=missing_ids,
      embeddings=result.vectors,
      documents=missing_texts,
      metadatas=metadatas,
    )
    return {
      cache_id: CachedEmbedding(
        id=cache_id,
        embedding=embedding,
        document=document,
        metadata=metadata,
      )
      for cache_id, embedding, document, metadata in zip(
        missing_ids, result.vectors, missing_texts, metadatas, strict=True
      )
    }

  async def _record_debug(
    self,
    debug_context: EmbeddingDebugContext | None,
    *,
    request_body: dict[str, object],
    response_body: dict[str, object],
    status: str,
    error_message: str | None,
    prompt_tokens: int | None,
    total_tokens: int | None,
    duration_ms: int | None,
  ) -> None:
    if self._debug_log_service is None or debug_context is None:
      return
    try:
      await self._debug_log_service.record_embedding_request(
        context=debug_context,
        request_body=request_body,
        response_body=response_body,
        status=status,
        error_message=error_message,
        prompt_tokens=prompt_tokens,
        total_tokens=total_tokens,
        duration_ms=duration_ms,
      )
    except Exception:
      return


def _unique_normalized_texts(texts: list[str]) -> list[str]:
  seen: set[str] = set()
  result: list[str] = []
  for text in texts:
    normalized = normalize_embedding_text(text)
    if not normalized or normalized in seen:
      continue
    seen.add(normalized)
    result.append(normalized)
  return result


def _inflight_key(collection_name: str, cache_id: str) -> str:
  return f"{collection_name}:{cache_id}"


def _debug_request_body(
  *,
  effective_config: EffectiveAPIConfig,
  project_id: str,
  signature: EmbeddingModelSignature,
  segmentation_mode: EmbeddingSegmentationMode,
  missing_texts: list[str],
  debug_context: EmbeddingDebugContext | None,
  requested_count: int,
  unique_count: int,
  cache_hit_count: int,
  cache_miss_count: int,
) -> dict[str, object]:
  config = effective_config.config
  body: dict[str, object] = {
    "model": config.model,
    "dimensions": config.dimensions,
    "input_count": len(missing_texts),
    "input_hashes": [_text_hash(text) for text in missing_texts],
    "segmentation_mode": segmentation_mode,
    "cache": {
      "requested_count": requested_count,
      "unique_count": unique_count,
      "cache_hit_count": cache_hit_count,
      "cache_miss_count": cache_miss_count,
    },
    "model_signature_hash": signature.hash,
    "project_id": project_id,
    "api_config_id": config.id,
  }
  if debug_context is not None:
    body.update(_debug_context_body(debug_context))
  return body


def _debug_context_body(context: EmbeddingDebugContext) -> dict[str, object]:
  return {
    "tool_type": context.tool_type,
    "resource_type": context.resource_type,
    "resource_id": context.resource_id,
    "run_id": context.run_id,
    "algorithm": context.algorithm,
    "batch_label": context.batch_label or context.request_type,
  }


def _debug_response_body(result) -> dict[str, object]:
  first_vector = result.vectors[0] if result.vectors else []
  return {
    "model": result.model,
    "embedding_count": len(result.vectors),
    "embedding_dimensions": len(first_vector),
    "usage": {
      "prompt_tokens": result.prompt_tokens,
      "total_tokens": result.total_tokens,
    },
    "duration_ms": result.duration_ms,
  }


def _debug_error_body(exc: Exception, started_at: float) -> dict[str, object]:
  return {
    "embedding_count": 0,
    "embedding_dimensions": None,
    "usage": {
      "prompt_tokens": None,
      "total_tokens": None,
    },
    "duration_ms": _duration_ms(started_at),
    "error_type": exc.__class__.__name__,
  }


def _text_hash(text: str) -> str:
  return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _duration_ms(started_at: float) -> int:
  return max(0, round((perf_counter() - started_at) * 1000))
