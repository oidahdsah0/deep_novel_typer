from __future__ import annotations

from collections import deque
from hashlib import sha256

from app.Services.chapters.repository import ChapterRepository
from app.Services.chapters.tree import chapter_paths
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityNotFoundError
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Schemas.chapters import (
  ChapterSearchMatch,
  ChapterSearchResponse,
  ChapterSearchResult,
)


class ChapterSearchIndex:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
    repository: ChapterRepository,
  ) -> None:
    self._db = db
    self._store = store
    self._paths = paths
    self._repository = repository

  async def upsert(
    self,
    conn,
    project_id: str,
    chapter_id: str,
    title: str,
    content: str,
    updated_at: str,
  ) -> None:
    content_hash = sha256(content.encode("utf-8")).hexdigest()
    cursor = await conn.execute(
      """
      SELECT rowid FROM chapter_search_meta
      WHERE project_id = ? AND chapter_id = ?
      """,
      (project_id, chapter_id),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if row is None:
      cursor = await conn.execute(
        """
        INSERT INTO chapter_search_meta (project_id, chapter_id, content_hash, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (project_id, chapter_id, content_hash, updated_at),
      )
      rowid = cursor.lastrowid
      await cursor.close()
    else:
      rowid = row["rowid"]
      await conn.execute(
        """
        UPDATE chapter_search_meta
        SET content_hash = ?, updated_at = ?
        WHERE rowid = ?
        """,
        (content_hash, updated_at, rowid),
      )

    await conn.execute("DELETE FROM chapter_search_fts WHERE rowid = ?", (rowid,))
    await conn.execute(
      """
      INSERT INTO chapter_search_fts (rowid, project_id, chapter_id, title, content)
      VALUES (?, ?, ?, ?, ?)
      """,
      (rowid, project_id, chapter_id, title, content),
    )

  async def delete_chapters(self, conn, project_id: str, chapter_ids: list[str]) -> None:
    if not chapter_ids:
      return
    placeholders = ",".join("?" for _ in chapter_ids)
    await conn.execute(
      f"""
      DELETE FROM chapter_search_fts
      WHERE rowid IN (
        SELECT rowid FROM chapter_search_meta
        WHERE project_id = ? AND chapter_id IN ({placeholders})
      )
      """,
      (project_id, *chapter_ids),
    )
    await conn.execute(
      f"""
      DELETE FROM chapter_search_meta
      WHERE project_id = ? AND chapter_id IN ({placeholders})
      """,
      (project_id, *chapter_ids),
    )

  async def search(
    self,
    project_id: str,
    query: str,
    scope_node_id: str | None = None,
    limit: int = 30,
  ) -> ChapterSearchResponse:
    normalized_query = " ".join(query.strip().split())
    if not normalized_query:
      return ChapterSearchResponse(query="", results=[])

    await self.ensure(project_id)
    scope_chapter_ids = await self._scope_chapter_ids(project_id, scope_node_id)
    max_results = max(1, min(limit, 50))
    if _should_use_like_search(normalized_query):
      rows = await self._search_like(project_id, normalized_query, max_results * 4)
    else:
      rows = await self._search_fts(project_id, normalized_query, max_results * 4)

    nodes = await self._repository.flat_node_rows(project_id)
    paths = chapter_paths(nodes)
    results: list[ChapterSearchResult] = []
    seen: set[str] = set()
    for row in rows:
      chapter_id = str(row["chapter_id"])
      if scope_chapter_ids is not None and chapter_id not in scope_chapter_ids:
        continue
      if chapter_id in seen:
        continue
      seen.add(chapter_id)
      node_id = str(row.get("node_id") or chapter_id)
      title_snippet = str(row.get("title_snippet") or "")
      content_snippet = str(row.get("content_snippet") or "")
      matches: list[ChapterSearchMatch] = []
      if title_snippet:
        matches.append(ChapterSearchMatch(field="title", snippet=title_snippet))
      if content_snippet and content_snippet != title_snippet:
        matches.append(ChapterSearchMatch(field="content", snippet=content_snippet))
      results.append(
        ChapterSearchResult(
          chapter_id=chapter_id,
          node_id=node_id,
          title=str(row["title"]),
          path=paths.get(node_id, []),
          word_count=int(row["word_count"] or 0),
          score=float(row["score"] or 0),
          matches=matches,
        )
      )
      if len(results) >= max_results:
        break

    return ChapterSearchResponse(query=normalized_query, results=results)

  async def ensure(self, project_id: str) -> None:
    rows = await self._db.fetch_all(
      """
      SELECT c.id, c.title, c.file_path, c.updated_at, m.updated_at AS indexed_at
      FROM chapters c
      LEFT JOIN chapter_search_meta m ON m.project_id = c.project_id AND m.chapter_id = c.id
      WHERE c.project_id = ?
      ORDER BY c.order_index ASC
      """,
      (project_id,),
    )
    for row in rows:
      if row["indexed_at"] == row["updated_at"]:
        continue
      content_path = self._paths.project(project_id).root / str(row["file_path"])
      if not await self._store.exists(content_path):
        continue
      content = await self._store.read_text(content_path)
      async with self._db.transaction() as conn:
        await self.upsert(
          conn,
          project_id,
          str(row["id"]),
          str(row["title"]),
          content,
          str(row["updated_at"]),
        )

  async def _search_fts(
    self, project_id: str, query: str, limit: int
  ) -> list[dict[str, object]]:
    return await self._db.fetch_all(
      """
      SELECT
        f.chapter_id,
        n.id AS node_id,
        c.title,
        c.word_count,
        bm25(chapter_search_fts, 0.0, 0.0, 8.0, 1.0) AS score,
        snippet(chapter_search_fts, 2, '<mark>', '</mark>', '...', 12) AS title_snippet,
        snippet(chapter_search_fts, 3, '<mark>', '</mark>', '...', 18) AS content_snippet
      FROM chapter_search_fts f
      JOIN chapter_search_meta m ON m.rowid = f.rowid
      JOIN chapters c ON c.project_id = m.project_id AND c.id = m.chapter_id
      JOIN chapter_nodes n ON n.project_id = m.project_id AND n.chapter_id = m.chapter_id
      WHERE f.project_id = ? AND chapter_search_fts MATCH ?
      ORDER BY score ASC
      LIMIT ?
      """,
      (project_id, _fts_query(query), limit),
    )

  async def _search_like(
    self, project_id: str, query: str, limit: int
  ) -> list[dict[str, object]]:
    pattern = f"%{query}%"
    rows = await self._db.fetch_all(
      """
      SELECT
        f.chapter_id,
        n.id AS node_id,
        c.title,
        c.word_count,
        f.content,
        CASE
          WHEN c.title = ? THEN 0
          WHEN c.title LIKE ? THEN 1
          ELSE 2
        END AS score
      FROM chapter_search_fts f
      JOIN chapter_search_meta m ON m.rowid = f.rowid
      JOIN chapters c ON c.project_id = m.project_id AND c.id = m.chapter_id
      JOIN chapter_nodes n ON n.project_id = m.project_id AND n.chapter_id = m.chapter_id
      WHERE f.project_id = ? AND (c.title LIKE ? OR f.content LIKE ?)
      ORDER BY score ASC, c.order_index ASC
      LIMIT ?
      """,
      (query, pattern, project_id, pattern, pattern, limit),
    )
    return [
      {
        **row,
        "title_snippet": _plain_snippet(str(row["title"]), query),
        "content_snippet": _plain_snippet(str(row["content"]), query),
      }
      for row in rows
    ]

  async def _scope_chapter_ids(
    self, project_id: str, scope_node_id: str | None
  ) -> set[str] | None:
    if scope_node_id is None:
      return None
    rows = await self._repository.flat_node_rows(project_id)
    nodes = {str(row["id"]): row for row in rows}
    if scope_node_id not in nodes:
      raise EntityNotFoundError(f"Chapter node not found: {scope_node_id}")
    children: dict[str | None, list[dict[str, object]]] = {}
    for row in rows:
      parent_id = row["parent_id"]
      children.setdefault(str(parent_id) if parent_id else None, []).append(row)
    scoped: set[str] = set()
    queue: deque[str] = deque([scope_node_id])
    while queue:
      node_id = queue.popleft()
      node = nodes[node_id]
      if node["chapter_id"]:
        scoped.add(str(node["chapter_id"]))
      for child in children.get(node_id, []):
        queue.append(str(child["id"]))
    return scoped


def _should_use_like_search(query: str) -> bool:
  terms = query.split()
  return any(len(term) < 3 for term in terms) or len(query) < 3


def _fts_query(query: str) -> str:
  terms = [term.replace('"', '""') for term in query.split() if term]
  return " AND ".join(f'"{term}"' for term in terms) or '""'


def _plain_snippet(value: str, query: str, radius: int = 32) -> str:
  if not value:
    return ""
  lower_value = value.casefold()
  lower_query = query.casefold()
  index = lower_value.find(lower_query)
  if index < 0:
    return ""
  start = max(0, index - radius)
  end = min(len(value), index + len(query) + radius)
  prefix = "..." if start else ""
  suffix = "..." if end < len(value) else ""
  return (
    f"{prefix}{value[start:index]}<mark>{value[index:index + len(query)]}</mark>"
    f"{value[index + len(query):end]}{suffix}"
  )
