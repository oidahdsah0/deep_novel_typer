from __future__ import annotations

from datetime import UTC, datetime

from app.Schemas.chapters import ChapterDetail
from app.Services.chapters.content import ChapterContent
from app.Services.chapters.repository import ChapterRepository
from app.Services.project_service import ProjectService
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityConflictError
from app.Utils.locks import AsyncLockRegistry


class ChapterSynopsis:
  def __init__(
    self,
    db: AsyncDatabase,
    locks: AsyncLockRegistry,
    project_service: ProjectService,
    repository: ChapterRepository,
    content: ChapterContent,
  ) -> None:
    self._db = db
    self._locks = locks
    self._project_service = project_service
    self._repository = repository
    self._content = content

  async def update(
    self,
    project_id: str,
    chapter_id: str,
    writing_synopsis: str,
    base_updated_at: str | None = None,
  ) -> ChapterDetail:
    async with self._locks.get(f"{project_id}:{chapter_id}"):
      await self._project_service.get_manifest(project_id)
      row = await self._repository.chapter_row(project_id, chapter_id)
      synopsis_updated_at = str(row["writing_synopsis_updated_at"] or row["updated_at"])
      if base_updated_at is not None and base_updated_at != synopsis_updated_at:
        raise EntityConflictError(
          "Chapter synopsis has changed since it was opened; refresh before saving again."
        )

      now = _now()
      async with self._db.transaction() as conn:
        await conn.execute(
          """
          UPDATE chapters
          SET writing_synopsis = ?, writing_synopsis_updated_at = ?
          WHERE project_id = ? AND id = ?
          """,
          (writing_synopsis, now, project_id, chapter_id),
        )
        await conn.execute(
          """
          UPDATE chapter_nodes
          SET updated_at = ?
          WHERE project_id = ? AND chapter_id = ?
          """,
          (now, project_id, chapter_id),
        )
        await conn.execute(
          "UPDATE projects SET updated_at = ? WHERE id = ?",
          (now, project_id),
        )

      return await self._content.detail(project_id, chapter_id)


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()
