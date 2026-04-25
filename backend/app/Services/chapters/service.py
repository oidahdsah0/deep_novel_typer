from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.Services.chapters.content import ChapterContent
from app.Services.chapters.deletion import ChapterDeletion
from app.Services.chapters.metadata_recovery import ChapterMetadataRecovery
from app.Services.chapters.repository import ChapterRepository, next_id
from app.Services.chapters.search_index import ChapterSearchIndex
from app.Services.chapters.synopsis import ChapterSynopsis
from app.Services.chapters.tree import chapter_order_updates
from app.Services.project_service import ProjectService
from app.Services.tree_movement import plan_tree_move, rows_with_updates
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityConflictError
from app.Utils.ids import slugify
from app.Utils.locks import AsyncLockRegistry
from app.Schemas.chapters import (
  ChapterDetail,
  ChapterNode,
  ChapterSearchResponse,
  ChapterSummary,
  CreateChapterNodeRequest,
  CreateChapterRequest,
  MoveChapterNodeRequest,
  MoveChapterNodeResponse,
  UpdateChapterNodeRequest,
)
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Utils.text import count_words


logger = logging.getLogger(__name__)


class ChapterService:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
    locks: AsyncLockRegistry,
    project_service: ProjectService,
  ) -> None:
    self._db = db
    self._store = store
    self._paths = paths
    self._locks = locks
    self._project_service = project_service
    self._repository = ChapterRepository(db)
    self._content = ChapterContent(store, paths, self._repository)
    self._search_index = ChapterSearchIndex(db, store, paths, self._repository)
    self._recovery = ChapterMetadataRecovery(db, self._search_index)
    self._synopsis = ChapterSynopsis(
      db, locks, project_service, self._repository, self._content
    )
    self._deletion = ChapterDeletion(
      db, store, paths, locks, project_service, self._repository, self._search_index
    )

  async def list_chapters(self, project_id: str) -> list[ChapterSummary]:
    return await self._project_service.list_chapters(project_id)

  async def list_chapter_tree(self, project_id: str) -> list[ChapterNode]:
    await self._project_service.get_manifest(project_id)
    return await self._repository.list_tree(project_id)

  async def create_node(
    self, project_id: str, request: CreateChapterNodeRequest
  ) -> ChapterNode:
    if request.type == "chapter":
      chapter = await self.create_chapter(
        project_id,
        CreateChapterRequest(
          title=request.title,
          content=request.content,
          parent_id=request.parent_id,
        ),
      )
      return await self._repository.node_detail(project_id, chapter.id)

    await self._project_service.get_manifest(project_id)
    async with self._locks.get(f"{project_id}:chapter-nodes"):
      if request.parent_id is not None:
        parent = await self._repository.node_row(project_id, request.parent_id)
        if str(parent["type"]) != "folder":
          raise EntityConflictError("Chapter nodes cannot contain child nodes")

      now = _now()
      node_id = await self._repository.next_node_id(project_id, request.title)
      order_index = await self._repository.next_order(project_id, request.parent_id)
      await self._db.execute(
        """
        INSERT INTO chapter_nodes (
          id, project_id, parent_id, type, title, chapter_id, order_index, created_at, updated_at
        )
        VALUES (?, ?, ?, 'folder', ?, NULL, ?, ?, ?)
        """,
        (
          node_id,
          project_id,
          request.parent_id,
          request.title,
          order_index,
          now,
          now,
        ),
      )
      await self._project_service.touch_project(project_id, now)
    return await self._repository.node_detail(project_id, node_id)

  async def update_node(
    self, project_id: str, node_id: str, request: UpdateChapterNodeRequest
  ) -> ChapterNode:
    await self._project_service.get_manifest(project_id)
    if request.title is None:
      await self._repository.node_row(project_id, node_id)
      return await self._repository.node_detail(project_id, node_id)

    async with self._locks.get(f"{project_id}:chapter-nodes"):
      row = await self._repository.node_row(project_id, node_id)
      if str(row["type"]) == "chapter" and row["chapter_id"]:
        async with self._locks.get(f"{project_id}:{row['chapter_id']}"):
          return await self._update_node_locked(project_id, node_id, request, row)
      return await self._update_node_locked(project_id, node_id, request, row)

  async def move_node(
    self, project_id: str, node_id: str, request: MoveChapterNodeRequest
  ) -> MoveChapterNodeResponse:
    await self._project_service.get_manifest(project_id)
    async with self._locks.get(f"{project_id}:chapter-nodes"):
      rows = await self._repository.flat_node_rows(project_id)
      updates = plan_tree_move(
        rows,
        node_id=node_id,
        parent_id=request.parent_id,
        before_node_id=request.before_node_id,
        not_found_label="Chapter node",
      )
      if updates:
        now = _now()
        next_rows = rows_with_updates(rows, updates)
        chapter_updates = chapter_order_updates(next_rows)
        async with self._db.transaction() as conn:
          for update in updates:
            await conn.execute(
              """
              UPDATE chapter_nodes
              SET parent_id = ?, order_index = ?, updated_at = ?
              WHERE project_id = ? AND id = ?
              """,
              (update.parent_id, update.order_index, now, project_id, update.node_id),
            )
          for chapter_id, order_index in chapter_updates:
            await conn.execute(
              """
              UPDATE chapters
              SET order_index = ?, updated_at = ?
              WHERE project_id = ? AND id = ?
              """,
              (order_index, now, project_id, chapter_id),
            )
          await conn.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (now, project_id),
          )
    return MoveChapterNodeResponse(
      chapter_tree=await self.list_chapter_tree(project_id),
      chapters=await self.list_chapters(project_id),
    )

  async def delete_node(self, project_id: str, node_id: str) -> None:
    await self._deletion.delete_node(project_id, node_id, _now())

  async def create_chapter(
    self, project_id: str, request: CreateChapterRequest
  ) -> ChapterDetail:
    async with self._locks.get(f"{project_id}:chapters"):
      project = await self._project_service.get_manifest(project_id)
      chapters = await self.list_chapters(project_id)
      if request.parent_id is not None:
        parent = await self._repository.node_row(project_id, request.parent_id)
        if str(parent["type"]) != "folder":
          raise EntityConflictError("Chapter nodes cannot contain child nodes")
      next_order = await self._repository.next_order(project_id, request.parent_id)
      chapter_id = next_id(
        slugify(request.title, fallback_prefix=f"chapter-{len(chapters) + 1:03d}"),
        {chapter.id for chapter in chapters} | await self._repository.existing_node_ids(project_id),
      )
      now = _now()
      word_count = count_words(request.content)
      file_path = f"chapters/{chapter_id}.md"

      tmp_path = await self._content.prepare_write(project_id, file_path, request.content)
      db_committed = False
      try:
        async with self._db.transaction() as conn:
          await conn.execute(
            """
            INSERT INTO chapters (
              id, project_id, title, order_index, word_count, file_path,
              writing_synopsis, writing_synopsis_updated_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, '', ?, ?, ?)
            """,
            (
              chapter_id,
              project_id,
              request.title,
              next_order,
              word_count,
              file_path,
              now,
              now,
              now,
            ),
          )
          await conn.execute(
            """
            INSERT INTO chapter_nodes (
              id, project_id, parent_id, type, title, chapter_id, order_index, created_at, updated_at
            )
            VALUES (?, ?, ?, 'chapter', ?, ?, ?, ?, ?)
            """,
            (
              chapter_id,
              project_id,
              request.parent_id,
              request.title,
              chapter_id,
              next_order,
              now,
              now,
            ),
          )
          await self._search_index.upsert(
            conn, project_id, chapter_id, request.title, request.content, now
          )
          await conn.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (now, project_id),
          )
        db_committed = True
        await self._content.commit_prepared_write(project_id, file_path, tmp_path)
      except Exception:
        try:
          await self._content.discard_prepared_write(tmp_path)
        except Exception:
          logger.exception("Failed to discard temp file for chapter %s", chapter_id)
        if db_committed:
          try:
            await self._recovery.rollback_created_chapter(
              project_id, chapter_id, project.updated_at
            )
          except Exception:
            logger.exception("Failed to roll back created chapter %s", chapter_id)
        raise

      return ChapterDetail(
        id=chapter_id,
        title=request.title,
        order=next_order,
        content=request.content,
        word_count=word_count,
        writing_synopsis="",
        writing_synopsis_updated_at=now,
        updated_at=now,
      )

  async def get_chapter(self, project_id: str, chapter_id: str) -> ChapterDetail:
    await self._project_service.get_manifest(project_id)
    return await self._content.detail(project_id, chapter_id)

  async def update_chapter(
    self,
    project_id: str,
    chapter_id: str,
    content: str,
    base_updated_at: str | None = None,
  ) -> ChapterDetail:
    async with self._locks.get(f"{project_id}:{chapter_id}"):
      project = await self._project_service.get_manifest(project_id)
      row = await self._repository.chapter_row(project_id, chapter_id)
      # base_updated_at is an opaque optimistic-lock token; clients must echo
      # updated_at exactly as received, so string comparison is intentional.
      if base_updated_at is not None and base_updated_at != str(row["updated_at"]):
        raise EntityConflictError(
          "Chapter has changed since it was opened; refresh before saving again."
        )
      previous_content = await self._content.read(project_id, chapter_id)
      previous_updated_at = str(row["updated_at"])
      previous_word_count = int(row["word_count"] or count_words(previous_content))
      now = _now()
      word_count = count_words(content)
      file_path = str(row["file_path"])

      tmp_path = await self._content.prepare_write(project_id, file_path, content)
      db_committed = False
      try:
        async with self._db.transaction() as conn:
          await conn.execute(
            """
            UPDATE chapters
            SET word_count = ?, updated_at = ?
            WHERE project_id = ? AND id = ?
            """,
            (word_count, now, project_id, chapter_id),
          )
          await conn.execute(
            """
            UPDATE chapter_nodes
            SET updated_at = ?
            WHERE project_id = ? AND chapter_id = ?
            """,
            (now, project_id, chapter_id),
          )
          await self._search_index.upsert(
            conn, project_id, chapter_id, str(row["title"]), content, now
          )
          await conn.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (now, project_id),
          )
        db_committed = True
        await self._content.commit_prepared_write(project_id, file_path, tmp_path)
      except Exception:
        try:
          await self._content.discard_prepared_write(tmp_path)
        except Exception:
          logger.exception("Failed to discard temp file for chapter %s", chapter_id)
        if db_committed:
          try:
            await self._recovery.restore_chapter_metadata(
              project_id=project_id,
              chapter_id=chapter_id,
              title=str(row["title"]),
              content=previous_content,
              word_count=previous_word_count,
              updated_at=previous_updated_at,
              project_updated_at=project.updated_at,
            )
          except Exception:
            logger.exception("Failed to restore chapter metadata for %s", chapter_id)
        raise

      return ChapterDetail(
        id=str(row["id"]),
        title=str(row["title"]),
        order=int(row["order_index"]),
        content=content,
        word_count=word_count,
        writing_synopsis=str(row["writing_synopsis"] or ""),
        writing_synopsis_updated_at=str(
          row["writing_synopsis_updated_at"] or row["updated_at"]
        ),
        updated_at=now,
      )

  async def update_chapter_writing_synopsis(
    self,
    project_id: str,
    chapter_id: str,
    writing_synopsis: str,
    base_updated_at: str | None = None,
  ) -> ChapterDetail:
    return await self._synopsis.update(
      project_id, chapter_id, writing_synopsis, base_updated_at
    )

  async def _update_node_locked(
    self,
    project_id: str,
    node_id: str,
    request: UpdateChapterNodeRequest,
    row: dict[str, object],
  ) -> ChapterNode:
    now = _now()
    title = request.title or ""
    async with self._db.transaction() as conn:
      await conn.execute(
        """
        UPDATE chapter_nodes
        SET title = ?, updated_at = ?
        WHERE project_id = ? AND id = ?
        """,
        (title, now, project_id, node_id),
      )
      if str(row["type"]) == "chapter" and row["chapter_id"]:
        chapter_id = str(row["chapter_id"])
        await conn.execute(
          """
          UPDATE chapters
          SET title = ?, updated_at = ?
          WHERE project_id = ? AND id = ?
          """,
          (title, now, project_id, chapter_id),
        )
        content = await self._content.read(project_id, chapter_id)
        await self._search_index.upsert(conn, project_id, chapter_id, title, content, now)
      await conn.execute(
        "UPDATE projects SET updated_at = ? WHERE id = ?",
        (now, project_id),
      )
    return await self._repository.node_detail(project_id, node_id)

  async def search_chapters(
    self,
    project_id: str,
    query: str,
    scope_node_id: str | None = None,
    limit: int = 30,
  ) -> ChapterSearchResponse:
    await self._project_service.get_manifest(project_id)
    return await self._search_index.search(project_id, query, scope_node_id, limit)


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()
