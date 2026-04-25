from __future__ import annotations

from app.Services.documents.tree import build_document_tree
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityNotFoundError
from app.Utils.ids import slugify
from app.Utils.tree import collect_subtree_rows
from app.Schemas.documents import DocumentNode


class DocumentRepository:
  def __init__(self, db: AsyncDatabase) -> None:
    self._db = db

  async def list_tree(self, project_id: str) -> list[DocumentNode]:
    return build_document_tree(await self.list_tree_rows(project_id))

  async def list_tree_rows(self, project_id: str) -> list[dict[str, object]]:
    return await self._db.fetch_all(
      """
      SELECT id, parent_id, type, title, updated_at
      FROM document_nodes
      WHERE project_id = ?
      ORDER BY
        CASE WHEN parent_id IS NULL THEN '' ELSE parent_id END ASC,
        order_index ASC,
        title ASC
      """,
      (project_id,),
    )

  async def node_row(self, project_id: str, node_id: str) -> dict[str, object]:
    row = await self._db.fetch_one(
      """
      SELECT id, project_id, parent_id, type, title, file_path, order_index, created_at, updated_at
      FROM document_nodes
      WHERE project_id = ? AND id = ?
      """,
      (project_id, node_id),
    )
    if row is None:
      raise EntityNotFoundError(f"Document node not found: {node_id}")
    return row

  async def node_detail(self, project_id: str, node_id: str) -> DocumentNode:
    row = await self.node_row(project_id, node_id)
    return DocumentNode(
      id=str(row["id"]),
      parent_id=row["parent_id"],  # type: ignore[arg-type]
      type=row["type"],  # type: ignore[arg-type]
      title=str(row["title"]),
      updated_at=str(row["updated_at"]),
    )

  async def next_node_id(self, project_id: str, title: str) -> str:
    base_id = slugify(title, fallback_prefix="doc")
    existing = {
      str(row["id"])
      for row in await self._db.fetch_all(
        "SELECT id FROM document_nodes WHERE project_id = ?",
        (project_id,),
      )
    }
    if base_id not in existing:
      return base_id
    index = 2
    while f"{base_id}-{index}" in existing:
      index += 1
    return f"{base_id}-{index}"

  async def next_order(self, project_id: str, parent_id: str | None) -> int:
    row = await self._db.fetch_one(
      """
      SELECT COALESCE(MAX(order_index), 0) AS max_order
      FROM document_nodes
      WHERE project_id = ? AND (
        (? IS NULL AND parent_id IS NULL) OR parent_id = ?
      )
      """,
      (project_id, parent_id, parent_id),
    )
    return int(row["max_order"] or 0) + 1

  async def flat_node_rows(self, project_id: str) -> list[dict[str, object]]:
    return await self._db.fetch_all(
      """
      SELECT id, parent_id, type, title, file_path, order_index
      FROM document_nodes
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
      EntityNotFoundError(f"Document node not found: {node_id}"),
    )
