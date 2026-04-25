from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from app.Services.api_configs import EffectiveAPIConfig
from app.Services.api_configs.health import is_configured
from app.Services.embeddings.cache import EmbeddingModelSignature, build_model_signature
from app.Services.model_request_queue_service import (
  ModelRequestPriority,
  ModelRequestQueueService,
)
from app.Utils.errors import DomainError
from app.Utils.openai_client_cache import get_cached_openai_client


@dataclass(frozen=True)
class EmbeddingBatchResult:
  vectors: list[list[float]]
  model: str
  model_signature: EmbeddingModelSignature
  prompt_tokens: int | None
  total_tokens: int | None
  duration_ms: int


class OpenAIEmbeddingRuntime:
  def __init__(
    self,
    request_queue: ModelRequestQueueService,
    *,
    timeout_seconds: float,
    headers: dict[str, str] | None = None,
  ) -> None:
    self._request_queue = request_queue
    self._timeout_seconds = timeout_seconds
    self._headers = headers or {}

  async def embed_texts(
    self,
    effective_config: EffectiveAPIConfig,
    texts: list[str],
    *,
    label: str = "embedding_batch",
  ) -> EmbeddingBatchResult:
    if not texts:
      return EmbeddingBatchResult(
        vectors=[],
        model=effective_config.config.model,
        model_signature=build_model_signature(effective_config.config),
        prompt_tokens=None,
        total_tokens=None,
        duration_ms=0,
      )
    if not is_configured(effective_config):
      raise DomainError("Embedding API config is missing API key, endpoint, or model.")

    config = effective_config.config
    client = await get_cached_openai_client(
      api_key=effective_config.api_key or "unused",
      base_url=config.base_url,
      headers=self._headers,
      timeout_seconds=self._timeout_seconds,
    )
    request_body: dict[str, object] = {
      "model": config.model,
      "input": texts,
    }
    if config.dimensions is not None:
      request_body["dimensions"] = config.dimensions

    start = perf_counter()
    response = await self._request_queue.run(
      label,
      lambda: client.embeddings.create(**request_body),
      kind="embedding",
      model=config.model,
      priority=ModelRequestPriority.manual,
    )

    duration_ms = max(0, round((perf_counter() - start) * 1000))
    vectors = _vectors_from_response(response)
    if len(vectors) != len(texts):
      raise DomainError(
        f"Embedding endpoint returned {len(vectors)} vectors for {len(texts)} input texts."
      )
    usage = getattr(response, "usage", None)
    prompt_tokens = _usage_value(usage, "prompt_tokens")
    total_tokens = _usage_value(usage, "total_tokens")
    return EmbeddingBatchResult(
      vectors=vectors,
      model=config.model,
      model_signature=build_model_signature(config),
      prompt_tokens=prompt_tokens,
      total_tokens=total_tokens,
      duration_ms=duration_ms,
    )


def _vectors_from_response(response: object) -> list[list[float]]:
  data = list(getattr(response, "data", []) or [])
  data.sort(key=lambda item: int(getattr(item, "index", 0)))
  vectors: list[list[float]] = []
  for item in data:
    embedding = getattr(item, "embedding", None)
    if not isinstance(embedding, list):
      raise DomainError("Embedding endpoint returned an invalid embedding payload.")
    vectors.append([float(value) for value in embedding])
  return vectors


def _usage_value(usage: object | None, key: str) -> int | None:
  value = getattr(usage, key, None)
  return int(value) if isinstance(value, int) else None
