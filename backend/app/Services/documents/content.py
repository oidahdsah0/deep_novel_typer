from __future__ import annotations

import logging

from app.Services.documents.repository import DocumentRepository
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityConflictError, EntityNotFoundError
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Schemas.documents import MarkdownDocumentDetail


logger = logging.getLogger(__name__)


class DocumentContent:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
    repository: DocumentRepository,
  ) -> None:
    self._db = db
    self._store = store
    self._paths = paths
    self._repository = repository

  async def get_document(
    self, project_id: str, document_id: str
  ) -> MarkdownDocumentDetail:
    row = await self._repository.node_row(project_id, document_id)
    if str(row["type"]) != "markdown":
      raise EntityConflictError("Folders do not have markdown content")
    document_path = self._document_path(project_id, document_id, row)
    return MarkdownDocumentDetail(
      id=str(row["id"]),
      parent_id=row["parent_id"],  # type: ignore[arg-type]
      type="markdown",
      title=str(row["title"]),
      updated_at=str(row["updated_at"]),
      content=await self._store.read_text(document_path),
    )

  async def update_document(
    self,
    project_id: str,
    document_id: str,
    content: str,
    now: str,
    project_updated_at: str,
    base_updated_at: str | None = None,
  ) -> MarkdownDocumentDetail:
    row = await self._repository.node_row(project_id, document_id)
    if str(row["type"]) != "markdown":
      raise EntityConflictError("Folders do not have markdown content")
    document_path = self._document_path(project_id, document_id, row)
    previous_updated_at = str(row["updated_at"])
    # base_updated_at is an opaque optimistic-lock token; clients must echo
    # updated_at exactly as received, so string comparison is intentional.
    if base_updated_at is not None and base_updated_at != previous_updated_at:
      raise EntityConflictError(
        "Document has changed since it was opened; refresh before saving again."
      )

    tmp_path = await self._store.write_text_temp(document_path, content)
    db_committed = False
    try:
      async with self._db.transaction() as conn:
        await conn.execute(
          """
          UPDATE document_nodes
          SET updated_at = ?
          WHERE project_id = ? AND id = ?
          """,
          (now, project_id, document_id),
        )
        await conn.execute(
          "UPDATE projects SET updated_at = ? WHERE id = ?",
          (now, project_id),
        )
      db_committed = True
      await self._store.commit_text_temp(tmp_path, document_path)
    except Exception:
      try:
        await self._store.discard_file(tmp_path)
      except Exception:
        logger.exception("Failed to discard temp file for document %s", document_id)
      if db_committed:
        try:
          await self._restore_document_metadata(
            project_id=project_id,
            document_id=document_id,
            updated_at=previous_updated_at,
            project_updated_at=project_updated_at,
          )
        except Exception:
          logger.exception("Failed to restore document metadata for %s", document_id)
      raise

    return MarkdownDocumentDetail(
      id=str(row["id"]),
      parent_id=row["parent_id"],  # type: ignore[arg-type]
      type="markdown",
      title=str(row["title"]),
      updated_at=now,
      content=content,
    )

  async def _restore_document_metadata(
    self,
    *,
    project_id: str,
    document_id: str,
    updated_at: str,
    project_updated_at: str,
  ) -> None:
    async with self._db.transaction() as conn:
      await conn.execute(
        """
        UPDATE document_nodes
        SET updated_at = ?
        WHERE project_id = ? AND id = ?
        """,
        (updated_at, project_id, document_id),
      )
      await conn.execute(
        "UPDATE projects SET updated_at = ? WHERE id = ?",
        (project_updated_at, project_id),
      )

  def _document_path(self, project_id: str, document_id: str, row: dict[str, object]):
    file_path = row["file_path"]
    if not file_path:
      raise EntityNotFoundError(f"Document file not found: {document_id}")
    return self._paths.project(project_id).root / str(file_path)
