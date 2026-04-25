from __future__ import annotations

from datetime import UTC, datetime

from app.Schemas.chapters import ChapterSummary
from app.Schemas.documents import WorkspaceDocument
from app.Schemas.projects import (
  CreateProjectRequest,
  ProjectDetail,
  ProjectSummary,
  UpdateProjectRequest,
)
from app.Services.projects.lifecycle import ProjectLifecycle
from app.Services.projects.repository import ProjectRepository
from app.Services.projects.trash import ProjectTrashManager
from app.Utils.db import AsyncDatabase
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore


class ProjectService:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
    locks: AsyncLockRegistry,
  ) -> None:
    self._db = db
    self._store = store
    self._paths = paths
    self._locks = locks
    self._repository = ProjectRepository(db)
    self._lifecycle = ProjectLifecycle(self._repository, store, paths, locks)
    self._trash = ProjectTrashManager(self._repository, store, paths, locks)

  async def bootstrap(self) -> None:
    await self._lifecycle.bootstrap()

  async def import_legacy_projects(self) -> None:
    await self._lifecycle.import_legacy_projects()

  async def create_project(self, request: CreateProjectRequest) -> ProjectDetail:
    return await self._lifecycle.create_project(request)

  async def list_projects(
    self,
    include_deleted: bool = False,
    status: str | None = None,
    q: str | None = None,
  ) -> list[ProjectSummary]:
    return await self._repository.list_projects(include_deleted, status, q)

  async def get_manifest(
    self, project_id: str, include_deleted: bool = False
  ) -> ProjectDetail:
    return await self._repository.get_manifest(
      project_id, include_deleted=include_deleted
    )

  async def update_project(
    self, project_id: str, request: UpdateProjectRequest
  ) -> ProjectDetail:
    await self._repository.get_project_summary(project_id)
    updates = request.model_dump(exclude_unset=True)
    if not updates:
      return await self.get_manifest(project_id)
    await self._repository.update_project_fields(project_id, updates, _now())
    return await self.get_manifest(project_id)

  async def mark_opened(self, project_id: str) -> ProjectSummary:
    await self._repository.get_project_summary(project_id)
    now = _now()
    await self._repository.mark_opened(project_id, now)
    return await self._repository.get_project_summary(project_id)

  async def trash_project(self, project_id: str) -> ProjectSummary:
    return await self._trash.trash_project(project_id)

  async def restore_project(self, project_id: str) -> ProjectSummary:
    return await self._trash.restore_project(project_id)

  async def list_chapters(self, project_id: str) -> list[ChapterSummary]:
    return await self._repository.list_chapters(project_id)

  async def list_documents(self, project_id: str) -> list[WorkspaceDocument]:
    return await self._repository.list_documents(project_id)

  async def touch_project(self, project_id: str, updated_at: str | None = None) -> None:
    await self._repository.touch_project(project_id, updated_at or _now())


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()
