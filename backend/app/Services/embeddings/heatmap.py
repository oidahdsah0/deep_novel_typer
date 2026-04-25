from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from app.Schemas.common import EmbeddingDistanceAlgorithm
from app.Schemas.embeddings import HeatmapItem, HeatmapTagScore
from app.Services.embeddings.segmentation import TextSegment


@dataclass(frozen=True)
class TagVector:
  tag_id: str
  vector: list[float]


def build_heatmap_items(
  segments: list[TextSegment],
  segment_vectors: list[list[float]],
  tag_vectors: list[TagVector],
  algorithm: EmbeddingDistanceAlgorithm,
) -> list[HeatmapItem]:
  raw_by_tag: dict[str, list[float]] = {tag.tag_id: [] for tag in tag_vectors}
  for vector in segment_vectors:
    for tag in tag_vectors:
      raw_by_tag[tag.tag_id].append(_raw_metric(vector, tag.vector, algorithm))

  closeness_by_tag = {
    tag_id: _normalize_closeness(values, algorithm) for tag_id, values in raw_by_tag.items()
  }
  items: list[HeatmapItem] = []
  for index, segment in enumerate(segments):
    scores: dict[str, HeatmapTagScore] = {}
    nearest_tag_id: str | None = None
    nearest_closeness = -1.0
    for tag in tag_vectors:
      raw = raw_by_tag[tag.tag_id][index]
      closeness = closeness_by_tag[tag.tag_id][index]
      if closeness > nearest_closeness:
        nearest_closeness = closeness
        nearest_tag_id = tag.tag_id
      scores[tag.tag_id] = HeatmapTagScore(
        raw_score=raw if algorithm == "cosine" else None,
        raw_distance=raw if algorithm != "cosine" else None,
        closeness=closeness,
      )
    items.append(
      HeatmapItem(
        token_index=segment.token_index,
        text=segment.text,
        normalized_text=segment.normalized_text,
        start_offset=segment.start_offset,
        end_offset=segment.end_offset,
        scores=scores,
        nearest_tag_id=nearest_tag_id,
      )
    )
  return items


def _raw_metric(
  vector: list[float], tag_vector: list[float], algorithm: EmbeddingDistanceAlgorithm
) -> float:
  _ensure_same_dimensions(vector, tag_vector)
  if algorithm == "cosine":
    return _cosine_similarity(vector, tag_vector)
  if algorithm == "euclidean":
    return sqrt(sum((left - right) ** 2 for left, right in zip(vector, tag_vector, strict=True)))
  if algorithm == "manhattan":
    return sum(abs(left - right) for left, right in zip(vector, tag_vector, strict=True))
  raise ValueError(f"Unsupported heatmap algorithm: {algorithm}")


def _normalize_closeness(
  values: list[float], algorithm: EmbeddingDistanceAlgorithm
) -> list[float]:
  if not values:
    return []
  if len(values) == 1:
    return [1.0]
  minimum = min(values)
  maximum = max(values)
  if maximum == minimum:
    return [1.0 for _value in values]
  if algorithm == "cosine":
    return [(value - minimum) / (maximum - minimum) for value in values]
  return [(maximum - value) / (maximum - minimum) for value in values]


def _cosine_similarity(vector: list[float], tag_vector: list[float]) -> float:
  dot = sum(left * right for left, right in zip(vector, tag_vector, strict=True))
  left_norm = sqrt(sum(value * value for value in vector))
  right_norm = sqrt(sum(value * value for value in tag_vector))
  if left_norm == 0 or right_norm == 0:
    return 0.0
  return dot / (left_norm * right_norm)


def _ensure_same_dimensions(vector: list[float], tag_vector: list[float]) -> None:
  if len(vector) != len(tag_vector):
    raise ValueError(
      f"Embedding dimensions do not match: token={len(vector)}, tag={len(tag_vector)}"
    )
