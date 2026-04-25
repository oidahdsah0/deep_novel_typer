from __future__ import annotations

from app.Services.chapters.tree import build_chapter_tree
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityNotFoundError
from app.Utils.ids import slugify
from app.Utils.tree import collect_subtree_rows
from app.Schemas.chapters import ChapterNode


class ChapterRepository:
  def __init__(self, db: AsyncDatabase) -> None:
    self._db = db

  async def list_tree(self, project_id: str) -> list[ChapterNode]:
    return build_chapter_tree(await self.list_tree_rows(project_id))

  async def list_tree_rows(self, project_id: str) -> list[dict[str, object]]:
    return await self._db.fetch_all(
      """
      SELECT n.id, n.parent_id, n.type, n.title, n.chapter_id, n.updated_at,
             COALESCE(c.word_count, 0) AS word_count
      FROM chapter_nodes n
      LEFT JOIN chapters c ON c.project_id = n.project_id AND c.id = n.chapter_id
      WHERE n.project_id = ?
      ORDER BY
        CASE WHEN n.parent_id IS NULL THEN '' ELSE n.parent_id END ASC,
        n.order_index ASC,
        n.title ASC
      """,
      (project_id,),
    )

  async def chapter_row(self, project_id: str, chapter_id: str) -> dict[str, object]:
    row = await self._db.fetch_one(
      """
      SELECT id, title, order_index, word_count, file_path,
             writing_synopsis, writing_synopsis_updated_at, updated_at
      FROM chapters
      WHERE project_id = ? AND id = ?
      """,
      (project_id, chapter_id),
    )
    if row is None:
      raise EntityNotFoundError(f"Chapter not found: {chapter_id}")
    return row

  async def node_row(self, project_id: str, node_id: str) -> dict[str, object]:
    row = await self._db.fetch_one(
      """
      SELECT id, project_id, parent_id, type, title, chapter_id, order_index, created_at, updated_at
      FROM chapter_nodes
      WHERE project_id = ? AND id = ?
      """,
      (project_id, node_id),
    )
    if row is None:
      raise EntityNotFoundError(f"Chapter node not found: {node_id}")
    return row

  async def node_detail(self, project_id: str, node_id: str) -> ChapterNode:
    row = await self._db.fetch_one(
      """
      SELECT n.id, n.parent_id, n.type, n.title, n.chapter_id, n.updated_at,
             COALESCE(c.word_count, 0) AS word_count
      FROM chapter_nodes n
      LEFT JOIN chapters c ON c.project_id = n.project_id AND c.id = n.chapter_id
      WHERE n.project_id = ? AND n.id = ?
      """,
      (project_id, node_id),
    )
    if row is None:
      raise EntityNotFoundError(f"Chapter node not found: {node_id}")
    return ChapterNode(
      id=str(row["id"]),
      parent_id=row["parent_id"],  # type: ignore[arg-type]
      type=row["type"],  # type: ignore[arg-type]
      title=str(row["title"]),
      chapter_id=row["chapter_id"],  # type: ignore[arg-type]
      word_count=int(row["word_count"] or 0),
      updated_at=str(row["updated_at"]),
    )

  async def next_node_id(self, project_id: str, title: str) -> str:
    existing = {
      str(row["id"])
      for row in await self._db.fetch_all(
        "SELECT id FROM chapter_nodes WHERE project_id = ?",
        (project_id,),
      )
    }
    return next_id(slugify(title, fallback_prefix="chapter-folder"), existing)

  async def next_order(self, project_id: str, parent_id: str | None) -> int:
    row = await self._db.fetch_one(
      """
      SELECT COALESCE(MAX(order_index), 0) AS max_order
      FROM chapter_nodes
      WHERE project_id = ? AND (
        (? IS NULL AND parent_id IS NULL) OR parent_id = ?
      )
      """,
      (project_id, parent_id, parent_id),
    )
    return int(row["max_order"] or 0) + 1

  async def existing_node_ids(self, project_id: str) -> set[str]:
    return {
      str(row["id"])
      for row in await self._db.fetch_all(
        "SELECT id FROM chapter_nodes WHERE project_id = ?",
        (project_id,),
      )
    }

  async def flat_node_rows(self, project_id: str) -> list[dict[str, object]]:
    return await self._db.fetch_all(
      """
      SELECT id, parent_id, type, title, chapter_id, order_index
      FROM chapter_nodes
      WHERE project_id = ?
      ORDER BY order_index ASC
      """,
      (project_id,),
    )

  async def subtree_node_rows(
    self, project_id: str, node_id: str
  ) -> list[dict[str, object]]:
    return collect_subtree_rows(
      await self.flat_node_rows(project_id),
      node_id,
      EntityNotFoundError(f"Chapter node not found: {node_id}"),
    )

  async def chapter_rows_by_ids(
    self, project_id: str, chapter_ids: list[str]
  ) -> list[dict[str, object]]:
    if not chapter_ids:
      return []
    placeholders = ",".join("?" for _ in chapter_ids)
    return await self._db.fetch_all(
      f"""
      SELECT id, title, file_path
      FROM chapters
      WHERE project_id = ? AND id IN ({placeholders})
      ORDER BY order_index ASC
      """,
      (project_id, *chapter_ids),
    )


def next_id(base_id: str, existing_ids: set[str]) -> str:
  if base_id not in existing_ids:
    return base_id

  suffix = 2
  while f"{base_id}-{suffix}" in existing_ids:
    suffix += 1
  return f"{base_id}-{suffix}"
