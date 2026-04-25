from __future__ import annotations

from app.Services.documents.repository import DocumentRepository
from app.Services.project_service import ProjectService
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityConflictError
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore


class DocumentDeletion:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
    locks: AsyncLockRegistry,
    project_service: ProjectService,
    repository: DocumentRepository,
  ) -> None:
    self._db = db
    self._store = store
    self._paths = paths
    self._locks = locks
    self._project_service = project_service
    self._repository = repository

  async def delete_node(self, project_id: str, node_id: str, now: str) -> None:
    await self._project_service.get_manifest(project_id)
    async with self._locks.get(f"{project_id}:document-nodes"):
      rows = await self._repository.subtree_node_rows(project_id, node_id)
      trash_root = self._paths.trashed_project_item(
        project_id, "document-nodes", node_id, _safe_timestamp(now)
      )
      if await self._store.exists(trash_root):
        raise EntityConflictError(f"Trash target already exists: {trash_root.name}")

      moved_files: list[dict[str, str]] = []
      project_paths = self._paths.project(project_id)
      for row in rows:
        file_path = row["file_path"]
        if not file_path:
          continue
        source = project_paths.root / str(file_path)
        target = trash_root / str(file_path)
        if await self._store.exists(source):
          await self._store.move_path(source, target)
          moved_files.append(
            {
              "document_id": str(row["id"]),
              "title": str(row["title"]),
              "file_path": str(file_path),
              "trash_path": str(target),
            }
          )

      await self._store.write_json(
        trash_root / "manifest.json",
        {
          "kind": "document_node_delete",
          "project_id": project_id,
          "node_id": node_id,
          "deleted_at": now,
          "nodes": [
            {
              "id": str(row["id"]),
              "parent_id": row["parent_id"],
              "type": str(row["type"]),
              "title": str(row["title"]),
              "file_path": row["file_path"],
            }
            for row in rows
          ],
          "files": moved_files,
        },
      )

      node_ids = [str(row["id"]) for row in rows]
      async with self._db.transaction() as conn:
        node_placeholders = _placeholders(node_ids)
        await conn.execute(
          f"""
          DELETE FROM document_nodes
          WHERE project_id = ? AND id IN ({node_placeholders})
          """,
          (project_id, *node_ids),
        )
        await conn.execute(
          "UPDATE projects SET updated_at = ? WHERE id = ?",
          (now, project_id),
        )


def _placeholders(values: list[str]) -> str:
  return ",".join("?" for _ in values)


def _safe_timestamp(value: str) -> str:
  return value.replace(":", "").replace(".", "").replace("+", "-")
