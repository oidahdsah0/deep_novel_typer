from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ProjectedPoint:
  x: float
  y: float


def project_vectors_pca(vectors: list[list[float]]) -> list[ProjectedPoint]:
  if not vectors:
    return []
  if len(vectors) == 1:
    return [ProjectedPoint(x=0.0, y=0.0)]

  array = np.asarray(vectors, dtype=float)
  if array.ndim != 2 or array.shape[1] == 0:
    return [ProjectedPoint(x=0.0, y=0.0) for _vector in vectors]

  centered = array - array.mean(axis=0, keepdims=True)
  if not np.any(centered):
    return [ProjectedPoint(x=0.0, y=0.0) for _vector in vectors]

  _u, _s, components = np.linalg.svd(centered, full_matrices=False)
  width = min(2, components.shape[0])
  coordinates = centered @ components[:width].T
  if width == 1:
    zeros = np.zeros((coordinates.shape[0], 1), dtype=float)
    coordinates = np.concatenate([coordinates, zeros], axis=1)

  normalized = _normalize_axes(coordinates[:, :2])
  return [
    ProjectedPoint(x=float(row[0]), y=float(row[1]))
    for row in normalized
  ]


def _normalize_axes(coordinates: np.ndarray) -> np.ndarray:
  result = coordinates.copy()
  for column in range(result.shape[1]):
    maximum = float(np.max(np.abs(result[:, column])))
    if maximum > 0:
      result[:, column] = result[:, column] / maximum
  return result
