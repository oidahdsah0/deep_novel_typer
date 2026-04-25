from __future__ import annotations

from app.Services.chapters.search_index import ChapterSearchIndex
from app.Utils.db import AsyncDatabase


class ChapterMetadataRecovery:
  def __init__(self, db: AsyncDatabase, search_index: ChapterSearchIndex) -> None:
    self._db = db
    self._search_index = search_index

  async def rollback_created_chapter(
    self, project_id: str, chapter_id: str, project_updated_at: str
  ) -> None:
    async with self._db.transaction() as conn:
      await self._search_index.delete_chapters(conn, project_id, [chapter_id])
      await conn.execute(
        "DELETE FROM chapter_nodes WHERE project_id = ? AND chapter_id = ?",
        (project_id, chapter_id),
      )
      await conn.execute(
        "DELETE FROM chapters WHERE project_id = ? AND id = ?",
        (project_id, chapter_id),
      )
      await conn.execute(
        "UPDATE projects SET updated_at = ? WHERE id = ?",
        (project_updated_at, project_id),
      )

  async def restore_chapter_metadata(
    self,
    *,
    project_id: str,
    chapter_id: str,
    title: str,
    content: str,
    word_count: int,
    updated_at: str,
    project_updated_at: str,
  ) -> None:
    async with self._db.transaction() as conn:
      await conn.execute(
        """
        UPDATE chapters
        SET word_count = ?, updated_at = ?
        WHERE project_id = ? AND id = ?
        """,
        (word_count, updated_at, project_id, chapter_id),
      )
      await conn.execute(
        """
        UPDATE chapter_nodes
        SET updated_at = ?
        WHERE project_id = ? AND chapter_id = ?
        """,
        (updated_at, project_id, chapter_id),
      )
      await self._search_index.upsert(
        conn, project_id, chapter_id, title, content, updated_at
      )
      await conn.execute(
        "UPDATE projects SET updated_at = ? WHERE id = ?",
        (project_updated_at, project_id),
      )
