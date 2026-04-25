from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.Services.documents.content import DocumentContent
from app.Services.documents.deletion import DocumentDeletion
from app.Services.documents.repository import DocumentRepository
from app.Services.project_service import ProjectService
from app.Services.tree_movement import plan_tree_move
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityConflictError
from app.Utils.locks import AsyncLockRegistry
from app.Schemas.documents import (
  CreateDocumentNodeRequest,
  DocumentNode,
  MarkdownDocumentDetail,
  MoveDocumentNodeRequest,
  MoveDocumentNodeResponse,
  UpdateDocumentNodeRequest,
  WorkspaceDocument,
)
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore


logger = logging.getLogger(__name__)


class DocumentService:
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
    self._repository = DocumentRepository(db)
    self._content = DocumentContent(db, store, paths, self._repository)
    self._deletion = DocumentDeletion(db, store, paths, locks, project_service, self._repository)

  async def list_documents(self, project_id: str) -> list[WorkspaceDocument]:
    return await self._project_service.list_documents(project_id)

  async def list_document_tree(self, project_id: str) -> list[DocumentNode]:
    await self._project_service.get_manifest(project_id)
    return await self._repository.list_tree(project_id)

  async def create_node(
    self, project_id: str, request: CreateDocumentNodeRequest
  ) -> DocumentNode:
    project = await self._project_service.get_manifest(project_id)
    async with self._locks.get(f"{project_id}:document-nodes"):
      if request.parent_id is not None:
        parent = await self._repository.node_row(project_id, request.parent_id)
        if str(parent["type"]) != "folder":
          raise EntityConflictError("Markdown documents cannot contain child documents")

      now = _now()
      node_id = await self._repository.next_node_id(project_id, request.title)
      order_index = await self._repository.next_order(project_id, request.parent_id)
      file_path = f"docs/{node_id}.md" if request.type == "markdown" else None
      tmp_path = None
      target_path = None
      if request.type == "markdown":
        content = request.content if request.content else f"# {request.title}\n\n"
        target_path = self._paths.project(project_id).root / str(file_path)
        tmp_path = await self._store.write_text_temp(target_path, content)

      db_committed = False
      try:
        async with self._db.transaction() as conn:
          await conn.execute(
            """
            INSERT INTO document_nodes (
              id, project_id, parent_id, type, title, file_path, order_index, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
              node_id,
              project_id,
              request.parent_id,
              request.type,
              request.title,
              file_path,
              order_index,
              now,
              now,
            ),
          )
          await conn.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (now, project_id),
          )
        db_committed = True
        if tmp_path is not None and target_path is not None:
          await self._store.commit_text_temp(tmp_path, target_path)
      except Exception:
        if tmp_path is not None:
          try:
            await self._store.discard_file(tmp_path)
          except Exception:
            logger.exception("Failed to discard temp file for node %s", node_id)
        if db_committed:
          try:
            await self._rollback_created_node(project_id, node_id, project.updated_at)
          except Exception:
            logger.exception("Failed to roll back created node %s", node_id)
        raise

    return await self._repository.node_detail(project_id, node_id)

  async def _rollback_created_node(
    self, project_id: str, node_id: str, project_updated_at: str
  ) -> None:
    async with self._db.transaction() as conn:
      await conn.execute(
        "DELETE FROM document_nodes WHERE project_id = ? AND id = ?",
        (project_id, node_id),
      )
      await conn.execute(
        "UPDATE projects SET updated_at = ? WHERE id = ?",
        (project_updated_at, project_id),
      )

  async def update_node(
    self, project_id: str, node_id: str, request: UpdateDocumentNodeRequest
  ) -> DocumentNode:
    await self._project_service.get_manifest(project_id)
    if request.title is None:
      await self._repository.node_row(project_id, node_id)
      return await self._repository.node_detail(project_id, node_id)

    async with self._locks.get(f"{project_id}:document-nodes"):
      row = await self._repository.node_row(project_id, node_id)
      if str(row["type"]) == "markdown":
        async with self._locks.get(f"{project_id}:documents:{node_id}"):
          return await self._update_node_locked(project_id, node_id, request)
      return await self._update_node_locked(project_id, node_id, request)

  async def _update_node_locked(
    self,
    project_id: str,
    node_id: str,
    request: UpdateDocumentNodeRequest,
  ) -> DocumentNode:
    now = _now()
    async with self._db.transaction() as conn:
      await conn.execute(
        """
        UPDATE document_nodes
        SET title = ?, updated_at = ?
        WHERE project_id = ? AND id = ?
        """,
        (request.title, now, project_id, node_id),
      )
      await conn.execute(
        "UPDATE projects SET updated_at = ? WHERE id = ?",
        (now, project_id),
      )
    return await self._repository.node_detail(project_id, node_id)

  async def move_node(
    self, project_id: str, node_id: str, request: MoveDocumentNodeRequest
  ) -> MoveDocumentNodeResponse:
    await self._project_service.get_manifest(project_id)
    async with self._locks.get(f"{project_id}:document-nodes"):
      rows = await self._repository.flat_node_rows(project_id)
      updates = plan_tree_move(
        rows,
        node_id=node_id,
        parent_id=request.parent_id,
        before_node_id=request.before_node_id,
        not_found_label="Document node",
      )
      if updates:
        now = _now()
        async with self._db.transaction() as conn:
          for update in updates:
            await conn.execute(
              """
              UPDATE document_nodes
              SET parent_id = ?, order_index = ?, updated_at = ?
              WHERE project_id = ? AND id = ?
              """,
              (update.parent_id, update.order_index, now, project_id, update.node_id),
            )
          await conn.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (now, project_id),
          )
    return MoveDocumentNodeResponse(
      document_tree=await self.list_document_tree(project_id),
    )

  async def delete_node(self, project_id: str, node_id: str) -> None:
    await self._deletion.delete_node(project_id, node_id, _now())

  async def get_document(
    self, project_id: str, document_id: str
  ) -> MarkdownDocumentDetail:
    await self._project_service.get_manifest(project_id)
    return await self._content.get_document(project_id, document_id)

  async def update_document(
    self,
    project_id: str,
    document_id: str,
    content: str,
    base_updated_at: str | None = None,
  ) -> MarkdownDocumentDetail:
    async with self._locks.get(f"{project_id}:documents:{document_id}"):
      project = await self._project_service.get_manifest(project_id)
      return await self._content.update_document(
        project_id, document_id, content, _now(), project.updated_at, base_updated_at
      )


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()
