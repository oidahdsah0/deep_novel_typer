from __future__ import annotations

from app.Services.chapters.repository import ChapterRepository
from app.Services.chapters.search_index import ChapterSearchIndex
from app.Services.project_service import ProjectService
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityConflictError
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore


class ChapterDeletion:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
    locks: AsyncLockRegistry,
    project_service: ProjectService,
    repository: ChapterRepository,
    search_index: ChapterSearchIndex,
  ) -> None:
    self._db = db
    self._store = store
    self._paths = paths
    self._locks = locks
    self._project_service = project_service
    self._repository = repository
    self._search_index = search_index

  async def delete_node(self, project_id: str, node_id: str, now: str) -> None:
    await self._project_service.get_manifest(project_id)
    async with self._locks.get(f"{project_id}:chapter-nodes"):
      rows = await self._repository.subtree_node_rows(project_id, node_id)
      chapter_ids = [
        str(row["chapter_id"])
        for row in rows
        if row["chapter_id"] is not None
      ]
      all_chapters = await self._project_service.list_chapters(project_id)
      if chapter_ids and len(chapter_ids) >= len(all_chapters):
        raise EntityConflictError("Cannot delete the last chapter")

      trash_root = self._paths.trashed_project_item(
        project_id, "chapter-nodes", node_id, _safe_timestamp(now)
      )
      if await self._store.exists(trash_root):
        raise EntityConflictError(f"Trash target already exists: {trash_root.name}")

      chapters = await self._repository.chapter_rows_by_ids(project_id, chapter_ids)
      moved_files: list[dict[str, str]] = []
      project_paths = self._paths.project(project_id)
      for chapter in chapters:
        file_path = str(chapter["file_path"])
        source = project_paths.root / file_path
        target = trash_root / file_path
        if await self._store.exists(source):
          await self._store.move_path(source, target)
          moved_files.append(
            {
              "chapter_id": str(chapter["id"]),
              "title": str(chapter["title"]),
              "file_path": file_path,
              "trash_path": str(target),
            }
          )

      await self._store.write_json(
        trash_root / "manifest.json",
        {
          "kind": "chapter_node_delete",
          "project_id": project_id,
          "node_id": node_id,
          "deleted_at": now,
          "nodes": [
            {
              "id": str(row["id"]),
              "parent_id": row["parent_id"],
              "type": str(row["type"]),
              "title": str(row["title"]),
              "chapter_id": row["chapter_id"],
            }
            for row in rows
          ],
          "files": moved_files,
        },
      )

      node_ids = [str(row["id"]) for row in rows]
      async with self._db.transaction() as conn:
        await self._search_index.delete_chapters(conn, project_id, chapter_ids)
        node_placeholders = _placeholders(node_ids)
        await conn.execute(
          f"""
          DELETE FROM chapter_nodes
          WHERE project_id = ? AND id IN ({node_placeholders})
          """,
          (project_id, *node_ids),
        )

        if chapter_ids:
          chapter_placeholders = _placeholders(chapter_ids)
          await conn.execute(
            f"""
            DELETE FROM chapters
            WHERE project_id = ? AND id IN ({chapter_placeholders})
            """,
            (project_id, *chapter_ids),
          )

        await conn.execute(
          "UPDATE projects SET updated_at = ? WHERE id = ?",
          (now, project_id),
        )


def _placeholders(values: list[str]) -> str:
  return ",".join("?" for _ in values)


def _safe_timestamp(value: str) -> str:
  return value.replace(":", "").replace(".", "").replace("+", "-")
