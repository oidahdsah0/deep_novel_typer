from __future__ import annotations

import json

from app.Schemas.embeddings import ClusterPoint, HeatmapItem


def heatmap_item_rows(
  run_id: str,
  items: list[HeatmapItem],
  vector_refs: list[str],
) -> list[tuple[object, ...]]:
  rows: list[tuple[object, ...]] = []
  for item, vector_ref in zip(items, vector_refs, strict=True):
    for tag_id, score in item.scores.items():
      rows.append(
        (
          run_id,
          item.token_index,
          item.text,
          item.normalized_text,
          item.start_offset,
          item.end_offset,
          vector_ref,
          tag_id,
          score.raw_score,
          score.raw_distance,
          score.closeness,
          None,
          None,
          None,
          json.dumps({"nearest_tag_id": item.nearest_tag_id}, ensure_ascii=False),
        )
      )
  return rows


def cluster_item_rows(
  run_id: str,
  points: list[ClusterPoint],
  vector_refs: list[str],
) -> list[tuple[object, ...]]:
  rows: list[tuple[object, ...]] = []
  for point, vector_ref in zip(points, vector_refs, strict=True):
    rows.append(
      (
        run_id,
        point.token_index,
        point.text,
        point.normalized_text,
        point.start_offset,
        point.end_offset,
        vector_ref,
        point.tag_id,
        point.raw_score,
        point.raw_distance,
        point.closeness,
        point.cluster_id,
        point.x,
        point.y,
        json.dumps({"cluster_mode": "fixed_tag_centers"}, ensure_ascii=False),
      )
    )
  return rows
