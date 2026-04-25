from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.Schemas.api_configs import APIConfig
from app.Schemas.common import EmbeddingSegmentationMode


@dataclass(frozen=True)
class EmbeddingModelSignature:
  value: str
  hash: str


def build_model_signature(config: APIConfig) -> EmbeddingModelSignature:
  dimensions = "" if config.dimensions is None else str(config.dimensions)
  value = "|".join(
    [
      config.id,
      config.provider,
      config.base_url.rstrip("/"),
      config.model,
      dimensions,
    ]
  )
  return EmbeddingModelSignature(value=value, hash=_sha256(value))


def normalize_embedding_text(text: str) -> str:
  return re.sub(r"\s+", " ", text).strip()


def embedding_cache_id(
  project_id: str,
  model_signature_hash: str,
  segmentation_mode: EmbeddingSegmentationMode,
  normalized_text: str,
) -> str:
  text_hash = _sha256(normalized_text)
  project_hash = _sha256(project_id)
  return f"embedding:{project_hash}:{model_signature_hash}:{segmentation_mode}:{text_hash}"


def embedding_collection_name(project_id: str, model_signature_hash: str) -> str:
  project_hash = _sha256(project_id)
  return f"embeddings_{project_hash[:12]}_{model_signature_hash[:20]}"


def _sha256(value: str) -> str:
  return hashlib.sha256(value.encode("utf-8")).hexdigest()
