from __future__ import annotations

from pathlib import Path

from app.Schemas.chapters import ChapterSummary
from app.Schemas.documents import WorkspaceDocument
from app.Schemas.projects import ProjectDetail, ProjectSummary
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityNotFoundError


class ProjectRepository:
  def __init__(self, db: AsyncDatabase) -> None:
    self._db = db

  async def list_projects(
    self,
    include_deleted: bool = False,
    status: str | None = None,
    q: str | None = None,
  ) -> list[ProjectSummary]:
    where = []
    params: list[str] = []
    if not include_deleted:
      where.append("p.deleted_at IS NULL")
    if status:
      where.append("p.status = ?")
      params.append(status)
    if q:
      where.append(
        "(p.title LIKE ? OR p.subtitle LIKE ? OR p.description LIKE ? OR p.genre LIKE ?)"
      )
      params.extend([f"%{q}%"] * 4)

    rows = await self._db.fetch_all(_project_summary_query(where), params)
    return [summary_from_row(row) for row in rows]

  async def get_manifest(
    self, project_id: str, include_deleted: bool = False
  ) -> ProjectDetail:
    project = await self.get_project_summary(
      project_id, include_deleted=include_deleted
    )
    chapters = await self.list_chapters(project_id, include_deleted=include_deleted)
    documents = await self.list_documents(project_id, include_deleted=include_deleted)
    return ProjectDetail(
      **project.model_dump(),
      chapters=chapters,
      documents=documents,
    )

  async def update_project_fields(
    self, project_id: str, updates: dict[str, object], updated_at: str
  ) -> None:
    assignments = [f"{field} = ?" for field in updates]
    params = [str(value) for value in updates.values()]
    params.extend([updated_at, project_id])
    await self._db.execute(
      f"UPDATE projects SET {', '.join(assignments)}, updated_at = ? WHERE id = ?",
      params,
    )

  async def mark_opened(self, project_id: str, opened_at: str) -> None:
    await self._db.execute(
      "UPDATE projects SET last_opened_at = ?, updated_at = ? WHERE id = ?",
      (opened_at, opened_at, project_id),
    )

  async def mark_deleted(
    self, project_id: str, *, deleted_at: str, trash_root: Path
  ) -> None:
    await self._db.execute(
      "UPDATE projects SET deleted_at = ?, root_path = ?, updated_at = ? WHERE id = ?",
      (deleted_at, str(trash_root), deleted_at, project_id),
    )

  async def mark_restored(
    self, project_id: str, *, root_path: Path, updated_at: str
  ) -> None:
    await self._db.execute(
      "UPDATE projects SET deleted_at = NULL, root_path = ?, updated_at = ? WHERE id = ?",
      (str(root_path), updated_at, project_id),
    )

  async def touch_project(self, project_id: str, updated_at: str) -> None:
    await self._db.execute(
      "UPDATE projects SET updated_at = ? WHERE id = ?",
      (updated_at, project_id),
    )

  async def get_project_summary(
    self, project_id: str, include_deleted: bool = False
  ) -> ProjectSummary:
    row = await self.get_project_row(project_id, include_deleted=include_deleted)
    return summary_from_row(row)

  async def get_project_row(
    self, project_id: str, include_deleted: bool = False
  ) -> dict[str, object]:
    where = ["p.id = ?"]
    if not include_deleted:
      where.append("p.deleted_at IS NULL")
    row = await self._db.fetch_one(_project_summary_query(where), (project_id,))
    if row is None:
      raise EntityNotFoundError(f"Project not found: {project_id}")
    return row

  async def project_exists(self, project_id: str) -> bool:
    row = await self._db.fetch_one("SELECT id FROM projects WHERE id = ?", (project_id,))
    return row is not None

  async def insert_project(
    self,
    detail: ProjectDetail,
    root_path: Path,
    perspectives: list[dict[str, object]],
  ) -> None:
    async with self._db.transaction() as conn:
      await conn.execute(
        """
        INSERT INTO projects (
          id, title, subtitle, description, genre, status, root_path,
          created_at, updated_at, last_opened_at, deleted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
          detail.id,
          detail.title,
          detail.subtitle,
          detail.description,
          detail.genre,
          detail.status,
          str(root_path),
          detail.created_at,
          detail.updated_at,
          detail.last_opened_at,
          detail.deleted_at,
        ),
      )
      for chapter in detail.chapters:
        await conn.execute(
          """
          INSERT INTO chapters (
            id, project_id, title, order_index, word_count, file_path,
            writing_synopsis, writing_synopsis_updated_at, created_at, updated_at
          )
          VALUES (?, ?, ?, ?, ?, ?, '', ?, ?, ?)
          """,
          (
            chapter.id,
            detail.id,
            chapter.title,
            chapter.order,
            chapter.word_count,
            f"chapters/{chapter.id}.md",
            detail.updated_at,
            detail.created_at,
            detail.updated_at,
          ),
        )
        await conn.execute(
          """
          INSERT OR IGNORE INTO chapter_nodes (
            id, project_id, parent_id, type, title, chapter_id, order_index, created_at, updated_at
          )
          VALUES (?, ?, NULL, 'chapter', ?, ?, ?, ?, ?)
          """,
          (
            chapter.id,
            detail.id,
            chapter.title,
            chapter.id,
            chapter.order,
            detail.created_at,
            detail.updated_at,
          ),
        )
      for document in detail.documents:
        order_index = document_order(document.kind)
        await conn.execute(
          """
          INSERT OR IGNORE INTO document_nodes (
            id, project_id, parent_id, type, title, file_path, order_index, created_at, updated_at
          )
          VALUES (?, ?, NULL, 'markdown', ?, ?, ?, ?, ?)
          """,
          (
            document.kind,
            detail.id,
            document.title,
            document_filename(document.kind),
            order_index,
            detail.created_at,
            document.updated_at,
          ),
        )
      for perspective in perspectives:
        await conn.execute(
          """
          INSERT INTO perspectives (
            id, project_id, name, description, instructions, api_config_id,
            is_enabled, created_at, updated_at
          )
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
          """,
          (
            perspective["id"],
            detail.id,
            perspective["name"],
            perspective["description"],
            perspective["instructions"],
            perspective.get("api_config_id"),
            int(bool(perspective.get("is_enabled", True))),
            perspective.get("created_at", detail.created_at),
            perspective.get("updated_at", detail.updated_at),
          ),
        )

  async def list_chapters(
    self, project_id: str, include_deleted: bool = False
  ) -> list[ChapterSummary]:
    await self.get_project_summary(project_id, include_deleted=include_deleted)
    rows = await self._db.fetch_all(
      """
      SELECT id, title, order_index, word_count
      FROM chapters
      WHERE project_id = ?
      ORDER BY order_index ASC
      """,
      (project_id,),
    )
    return [
      ChapterSummary(
        id=row["id"],
        title=row["title"],
        order=row["order_index"],
        word_count=row["word_count"],
      )
      for row in rows
    ]

  async def list_documents(
    self, project_id: str, include_deleted: bool = False
  ) -> list[WorkspaceDocument]:
    await self.get_project_summary(project_id, include_deleted=include_deleted)
    rows = await self._db.fetch_all(
      """
      SELECT id AS kind, title, updated_at
      FROM document_nodes
      WHERE project_id = ?
        AND type = 'markdown'
        AND id IN ('outline', 'design', 'note')
      ORDER BY CASE id WHEN 'outline' THEN 1 WHEN 'design' THEN 2 ELSE 3 END
      """,
      (project_id,),
    )
    return [WorkspaceDocument.model_validate(row) for row in rows]


def _project_summary_query(where: list[str]) -> str:
  clause = f"WHERE {' AND '.join(where)}" if where else ""
  return f"""
    SELECT
      p.*,
      COUNT(c.id) AS chapter_count,
      COALESCE(SUM(c.word_count), 0) AS word_count
    FROM projects p
    LEFT JOIN chapters c ON c.project_id = p.id
    {clause}
    GROUP BY p.id
    ORDER BY COALESCE(p.last_opened_at, p.updated_at) DESC, p.updated_at DESC
  """


def summary_from_row(row: dict[str, object]) -> ProjectSummary:
  return ProjectSummary(
    id=str(row["id"]),
    title=str(row["title"]),
    subtitle=str(row["subtitle"] or ""),
    description=str(row["description"] or ""),
    genre=str(row["genre"] or ""),
    status=row["status"],  # type: ignore[arg-type]
    created_at=str(row["created_at"]),
    updated_at=str(row["updated_at"]),
    last_opened_at=row["last_opened_at"],  # type: ignore[arg-type]
    deleted_at=row["deleted_at"],  # type: ignore[arg-type]
    chapter_count=int(row["chapter_count"] or 0),
    word_count=int(row["word_count"] or 0),
  )


def document_filename(kind: str) -> str:
  return {
    "outline": "docs/outline.md",
    "design": "docs/design.md",
    "note": "docs/notes.md",
  }[kind]


def document_order(kind: str) -> int:
  return {
    "outline": 1,
    "design": 2,
    "note": 3,
  }.get(kind, 10)
