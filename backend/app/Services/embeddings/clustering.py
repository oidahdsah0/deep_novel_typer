from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from app.Schemas.common import EmbeddingDistanceAlgorithm
from app.Schemas.embeddings import (
  ClusterPoint,
  ClusterSummary,
  ClusterTagAnchor,
  EmbeddingTag,
)
from app.Services.embeddings.projection import project_vectors_pca
from app.Services.embeddings.segmentation import TextSegment


@dataclass(frozen=True)
class ClusterTagVector:
  tag: EmbeddingTag
  vector: list[float]


@dataclass(frozen=True)
class ClusterBuildResult:
  points: list[ClusterPoint]
  clusters: list[ClusterSummary]
  tag_anchors: list[ClusterTagAnchor]


def build_fixed_tag_clusters(
  segments: list[TextSegment],
  segment_vectors: list[list[float]],
  tag_vectors: list[ClusterTagVector],
  algorithm: EmbeddingDistanceAlgorithm,
) -> ClusterBuildResult:
  projected = project_vectors_pca([*segment_vectors, *[tag.vector for tag in tag_vectors]])
  point_positions = projected[: len(segment_vectors)]
  tag_positions = projected[len(segment_vectors) :]

  anchors = [
    ClusterTagAnchor(
      tag_id=tag_vector.tag.id,
      name=tag_vector.tag.name,
      color=tag_vector.tag.color,
      x=position.x,
      y=position.y,
    )
    for tag_vector, position in zip(tag_vectors, tag_positions, strict=True)
  ]
  points = [
    _cluster_point(segment, vector, position, tag_vectors, algorithm)
    for segment, vector, position in zip(segments, segment_vectors, point_positions, strict=True)
  ]
  return ClusterBuildResult(
    points=points,
    clusters=_cluster_summaries(tag_vectors, anchors, points),
    tag_anchors=anchors,
  )


def _cluster_point(
  segment: TextSegment,
  vector: list[float],
  position,
  tag_vectors: list[ClusterTagVector],
  algorithm: EmbeddingDistanceAlgorithm,
) -> ClusterPoint:
  nearest_tag, nearest_raw = _nearest_tag(vector, tag_vectors, algorithm)
  return ClusterPoint(
    token_index=segment.token_index,
    text=segment.text,
    normalized_text=segment.normalized_text,
    start_offset=segment.start_offset,
    end_offset=segment.end_offset,
    cluster_id=nearest_tag.tag.id,
    tag_id=nearest_tag.tag.id,
    raw_score=nearest_raw if algorithm == "cosine" else None,
    raw_distance=nearest_raw if algorithm != "cosine" else None,
    closeness=_closeness(nearest_raw, algorithm),
    x=position.x,
    y=position.y,
  )


def _nearest_tag(
  vector: list[float],
  tag_vectors: list[ClusterTagVector],
  algorithm: EmbeddingDistanceAlgorithm,
) -> tuple[ClusterTagVector, float]:
  best_tag = tag_vectors[0]
  best_raw = _raw_metric(vector, best_tag.vector, algorithm)
  for tag in tag_vectors[1:]:
    raw = _raw_metric(vector, tag.vector, algorithm)
    if _is_better(raw, best_raw, algorithm):
      best_tag = tag
      best_raw = raw
  return best_tag, best_raw


def _cluster_summaries(
  tag_vectors: list[ClusterTagVector],
  anchors: list[ClusterTagAnchor],
  points: list[ClusterPoint],
) -> list[ClusterSummary]:
  points_by_tag: dict[str, list[ClusterPoint]] = {tag.tag.id: [] for tag in tag_vectors}
  for point in points:
    points_by_tag.setdefault(point.tag_id, []).append(point)

  anchors_by_tag = {anchor.tag_id: anchor for anchor in anchors}
  summaries: list[ClusterSummary] = []
  for tag in tag_vectors:
    tag_points = points_by_tag.get(tag.tag.id, [])
    anchor = anchors_by_tag[tag.tag.id]
    summaries.append(
      ClusterSummary(
        cluster_id=tag.tag.id,
        tag_id=tag.tag.id,
        name=tag.tag.name,
        color=tag.tag.color,
        point_count=len(tag_points),
        average_closeness=_average_closeness(tag_points),
        x=anchor.x,
        y=anchor.y,
      )
    )
  return summaries


def _average_closeness(points: list[ClusterPoint]) -> float | None:
  if not points:
    return None
  return sum(point.closeness for point in points) / len(points)


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
  raise ValueError(f"Unsupported cluster algorithm: {algorithm}")


def _is_better(raw: float, best_raw: float, algorithm: EmbeddingDistanceAlgorithm) -> bool:
  if algorithm == "cosine":
    return raw > best_raw
  return raw < best_raw


def _closeness(raw: float, algorithm: EmbeddingDistanceAlgorithm) -> float:
  if algorithm == "cosine":
    return max(0.0, min(1.0, (raw + 1.0) / 2.0))
  return 1.0 / (1.0 + max(0.0, raw))


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
