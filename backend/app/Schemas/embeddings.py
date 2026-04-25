from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.Schemas.common import (
  EmbeddingClusterMode,
  EmbeddingDistanceAlgorithm,
  EmbeddingResourceType,
  EmbeddingSegmentationMode,
)


class EmbeddingTag(BaseModel):
  id: str
  project_id: str
  name: str
  description: str = ""
  color: str = "#d94841"
  is_enabled: bool = True
  embedding_config_id: str | None = None
  embedding_model_signature: str | None = None
  embedding_vector_ref: str | None = None
  created_at: str
  updated_at: str


class CreateEmbeddingTagRequest(BaseModel):
  name: str = Field(min_length=1, max_length=80)
  description: str = Field(default="", max_length=1000)
  color: str = Field(default="#d94841", pattern=r"^#[0-9a-fA-F]{6}$")
  is_enabled: bool = True

  @field_validator("name", "description", "color", mode="before")
  @classmethod
  def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip()
    return value


class UpdateEmbeddingTagRequest(BaseModel):
  name: str | None = Field(default=None, min_length=1, max_length=80)
  description: str | None = Field(default=None, max_length=1000)
  color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
  is_enabled: bool | None = None

  @field_validator("name", "description", "color", mode="before")
  @classmethod
  def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip()
    return value


class EmbeddingProjectSettings(BaseModel):
  project_id: str
  api_config_id: str | None = None
  segmentation_mode: EmbeddingSegmentationMode = "word"
  segment_size: int = Field(default=1, ge=1, le=12)
  algorithm: EmbeddingDistanceAlgorithm = "cosine"
  updated_at: str | None = None


class UpdateEmbeddingProjectSettingsRequest(BaseModel):
  api_config_id: str | None = Field(default=None, max_length=160)
  segmentation_mode: EmbeddingSegmentationMode = "word"
  segment_size: int = Field(default=1, ge=1, le=12)
  algorithm: EmbeddingDistanceAlgorithm = "cosine"

  @field_validator("api_config_id", mode="before")
  @classmethod
  def strip_api_config_id(cls, value: object) -> object:
    if isinstance(value, str):
      stripped = value.strip()
      return stripped or None
    return value


class EmbeddingSegmentPreview(BaseModel):
  token_index: int
  text: str
  normalized_text: str
  start_offset: int
  end_offset: int
  segmentation_mode: EmbeddingSegmentationMode


class EmbeddingCacheStats(BaseModel):
  requested_count: int
  unique_count: int
  cache_hit_count: int
  cache_miss_count: int


class EmbeddingTextRange(BaseModel):
  start_offset: int | None = Field(default=None, ge=0)
  end_offset: int | None = Field(default=None, ge=0)


class HeatmapRequest(BaseModel):
  resource_type: EmbeddingResourceType
  resource_id: str = Field(min_length=1, max_length=160)
  api_config_id: str | None = Field(default=None, max_length=160)
  segmentation_mode: EmbeddingSegmentationMode = "word"
  segment_size: int = Field(default=1, ge=1, le=12)
  algorithm: EmbeddingDistanceAlgorithm = "cosine"
  tag_ids: list[str] = Field(default_factory=list, max_length=50)
  range: EmbeddingTextRange | None = None
  force_reembed: bool = False

  @field_validator("resource_id", "api_config_id", mode="before")
  @classmethod
  def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
      stripped = value.strip()
      return stripped or None
    return value

  @field_validator("tag_ids")
  @classmethod
  def normalize_tag_ids(cls, value: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for tag_id in value:
      stripped = tag_id.strip()
      if not stripped or stripped in seen:
        continue
      seen.add(stripped)
      normalized.append(stripped)
    return normalized


class HeatmapTagScore(BaseModel):
  raw_score: float | None = None
  raw_distance: float | None = None
  closeness: float


class HeatmapItem(BaseModel):
  token_index: int
  text: str
  normalized_text: str
  start_offset: int
  end_offset: int
  scores: dict[str, HeatmapTagScore]
  nearest_tag_id: str | None = None


class HeatmapResponse(BaseModel):
  run_id: str
  status: str
  resource_type: EmbeddingResourceType
  resource_id: str
  model_signature: str
  model_signature_hash: str
  segmentation_mode: EmbeddingSegmentationMode
  segment_size: int
  algorithm: EmbeddingDistanceAlgorithm
  tags: list[EmbeddingTag]
  items: list[HeatmapItem]
  token_cache: EmbeddingCacheStats
  tag_cache: EmbeddingCacheStats
  warnings: list[str] = Field(default_factory=list)


class ClusterRequest(BaseModel):
  resource_type: EmbeddingResourceType
  resource_id: str = Field(min_length=1, max_length=160)
  api_config_id: str | None = Field(default=None, max_length=160)
  segmentation_mode: EmbeddingSegmentationMode = "word"
  segment_size: int = Field(default=1, ge=1, le=12)
  algorithm: EmbeddingDistanceAlgorithm = "cosine"
  cluster_mode: EmbeddingClusterMode = "fixed_tag_centers"
  tag_ids: list[str] = Field(default_factory=list, max_length=50)
  range: EmbeddingTextRange | None = None
  force_reembed: bool = False

  @field_validator("resource_id", "api_config_id", mode="before")
  @classmethod
  def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
      stripped = value.strip()
      return stripped or None
    return value

  @field_validator("tag_ids")
  @classmethod
  def normalize_tag_ids(cls, value: list[str]) -> list[str]:
    return _normalize_tag_ids(value)


class ClusterPoint(BaseModel):
  token_index: int
  text: str
  normalized_text: str
  start_offset: int
  end_offset: int
  cluster_id: str
  tag_id: str
  raw_score: float | None = None
  raw_distance: float | None = None
  closeness: float
  x: float
  y: float


class ClusterSummary(BaseModel):
  cluster_id: str
  tag_id: str
  name: str
  color: str
  point_count: int
  average_closeness: float | None = None
  x: float
  y: float


class ClusterTagAnchor(BaseModel):
  tag_id: str
  name: str
  color: str
  x: float
  y: float


class ClusterResponse(BaseModel):
  run_id: str
  status: str
  resource_type: EmbeddingResourceType
  resource_id: str
  model_signature: str
  model_signature_hash: str
  segmentation_mode: EmbeddingSegmentationMode
  segment_size: int
  algorithm: EmbeddingDistanceAlgorithm
  cluster_mode: EmbeddingClusterMode
  projection: str = "pca"
  tags: list[EmbeddingTag]
  points: list[ClusterPoint]
  clusters: list[ClusterSummary]
  tag_anchors: list[ClusterTagAnchor]
  token_cache: EmbeddingCacheStats
  tag_cache: EmbeddingCacheStats
  warnings: list[str] = Field(default_factory=list)


def _normalize_tag_ids(value: list[str]) -> list[str]:
  normalized: list[str] = []
  seen: set[str] = set()
  for tag_id in value:
    stripped = tag_id.strip()
    if not stripped or stripped in seen:
      continue
    seen.add(stripped)
    normalized.append(stripped)
  return normalized
