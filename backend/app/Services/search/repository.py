from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from app.Services.search.indexing import (
  SearchDocument,
  delete_project_search,
  delete_search_document,
  upsert_search_document,
)
from app.Services.search.query import fts_query, should_use_like_search
from app.Services.search.ranking import fts_order_sql, like_score_sql
from app.Services.search.snippets import plain_snippet
from app.Utils.db import AsyncDatabase
from app.Schemas.search import ProjectSearchResourceType


class ProjectSearchRepository:
  def __init__(self, db: AsyncDatabase) -> None:
    self._db = db

  async def upsert(self, document: SearchDocument) -> None:
    async with self._db.transaction() as conn:
      await upsert_search_document(conn, document)

  async def clear_project(self, project_id: str) -> None:
    async with self._db.transaction() as conn:
      await delete_project_search(conn, project_id)

  async def delete_resources(
    self,
    project_id: str,
    resources: Sequence[tuple[ProjectSearchResourceType, str]],
  ) -> None:
    if not resources:
      return
    async with self._db.transaction() as conn:
      for resource_type, resource_id in resources:
        await delete_search_document(conn, project_id, resource_type, resource_id)

  async def search(
    self,
    project_id: str,
    query: str,
    resource_types: Sequence[ProjectSearchResourceType],
    limit: int,
  ) -> list[dict[str, object]]:
    if not resource_types:
      return []
    if should_use_like_search(query):
      return await self._search_like(project_id, query, resource_types, limit)
    return await self._search_fts(project_id, query, resource_types, limit)

  async def meta_rows(self, project_id: str) -> list[dict[str, object]]:
    return await self._db.fetch_all(
      """
      SELECT resource_type, resource_id, title, path_text, content_hash, updated_at
      FROM project_search_meta
      WHERE project_id = ?
      """,
      (project_id,),
    )

  async def _search_fts(
    self,
    project_id: str,
    query: str,
    resource_types: Sequence[ProjectSearchResourceType],
    limit: int,
  ) -> list[dict[str, object]]:
    placeholders = _placeholders(resource_types)
    rows = await self._db.fetch_all(
      f"""
      SELECT
        m.resource_type,
        m.resource_id,
        m.resource_subtype,
        m.title,
        m.path_text,
        m.updated_at,
        m.extra_json,
        bm25(project_search_fts, 0.0, 0.0, 0.0, 0.0, 8.0, 2.5, 1.0) AS score,
        snippet(project_search_fts, 4, '<mark>', '</mark>', '...', 12) AS title_snippet,
        snippet(project_search_fts, 5, '<mark>', '</mark>', '...', 12) AS path_snippet,
        snippet(project_search_fts, 6, '<mark>', '</mark>', '...', 22) AS content_snippet
      FROM project_search_fts f
      JOIN project_search_meta m ON m.rowid = f.rowid
      WHERE f.project_id = ?
        AND m.resource_type IN ({placeholders})
        AND project_search_fts MATCH ?
      ORDER BY {fts_order_sql()}
      LIMIT ?
      """,
      (project_id, *resource_types, fts_query(query), limit),
    )
    return [_decode_row(row) for row in rows]

  async def _search_like(
    self,
    project_id: str,
    query: str,
    resource_types: Sequence[ProjectSearchResourceType],
    limit: int,
  ) -> list[dict[str, object]]:
    placeholders = _placeholders(resource_types)
    pattern = f"%{query}%"
    rows = await self._db.fetch_all(
      f"""
      SELECT
        m.resource_type,
        m.resource_id,
        m.resource_subtype,
        m.title,
        m.path_text,
        m.updated_at,
        m.extra_json,
        f.body,
        {like_score_sql()}
      FROM project_search_fts f
      JOIN project_search_meta m ON m.rowid = f.rowid
      WHERE f.project_id = ?
        AND m.resource_type IN ({placeholders})
        AND (m.title LIKE ? OR m.path_text LIKE ? OR f.body LIKE ?)
      ORDER BY score ASC, m.updated_at DESC
      LIMIT ?
      """,
      (
        query,
        pattern,
        pattern,
        project_id,
        *resource_types,
        pattern,
        pattern,
        pattern,
        limit,
      ),
    )
    return [
      _decode_row(
        {
          **row,
          "title_snippet": plain_snippet(str(row["title"]), query),
          "path_snippet": plain_snippet(str(row["path_text"]), query),
          "content_snippet": plain_snippet(str(row["body"]), query),
        }
      )
      for row in rows
    ]


def _decode_row(row: dict[str, Any]) -> dict[str, object]:
  try:
    metadata = json.loads(str(row.get("extra_json") or "{}"))
  except json.JSONDecodeError:
    metadata = {}
  if not isinstance(metadata, dict):
    metadata = {}
  return {
    **row,
    "metadata": metadata,
  }


def _placeholders(values: Sequence[object]) -> str:
  if not values:
    raise ValueError("At least one value is required")
  return ", ".join("?" for _ in values)
