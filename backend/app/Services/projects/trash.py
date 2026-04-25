from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from app.Schemas.projects import ProjectSummary
from app.Services.projects.repository import ProjectRepository
from app.Utils.errors import EntityConflictError
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore


logger = logging.getLogger(__name__)


class ProjectTrashManager:
  def __init__(
    self,
    repository: ProjectRepository,
    store: AsyncFileStore,
    paths: PathResolver,
    locks: AsyncLockRegistry,
  ) -> None:
    self._repository = repository
    self._store = store
    self._paths = paths
    self._locks = locks

  async def trash_project(self, project_id: str) -> ProjectSummary:
    async with self._locks.get(project_id):
      await self._repository.get_project_summary(project_id)
      source = self._paths.project(project_id).root
      deleted_at = _now()
      trash_root = self._paths.trashed_project(project_id, _safe_timestamp(deleted_at))
      if await self._store.exists(trash_root):
        raise EntityConflictError(f"Trash target already exists: {trash_root.name}")

      await self._repository.mark_deleted(
        project_id, deleted_at=deleted_at, trash_root=trash_root
      )
      try:
        if await self._store.exists(source):
          await self._store.move_dir(source, trash_root)
      except Exception:
        try:
          await self._repository.mark_restored(
            project_id, root_path=source, updated_at=_now()
          )
        except Exception:
          logger.exception("Failed to roll back soft-delete for project %s", project_id)
        raise
      return (
        await self._repository.get_project_summary(project_id, include_deleted=True)
      ).model_copy(update={"deleted_at": deleted_at})

  async def restore_project(self, project_id: str) -> ProjectSummary:
    async with self._locks.get(project_id):
      project = await self._repository.get_project_summary(
        project_id, include_deleted=True
      )
      if project.deleted_at is None:
        return project

      row = await self._repository.get_project_row(project_id, include_deleted=True)
      source = Path(str(row["root_path"]))
      target = self._paths.project(project_id).root
      if await self._store.exists(target):
        raise EntityConflictError(f"Active project folder already exists: {project_id}")

      now = _now()
      await self._repository.mark_restored(project_id, root_path=target, updated_at=now)
      try:
        if await self._store.exists(source):
          await self._store.move_dir(source, target)
      except Exception:
        try:
          await self._repository.mark_deleted(
            project_id, deleted_at=project.deleted_at, trash_root=source
          )
        except Exception:
          logger.exception("Failed to roll back restore for project %s", project_id)
        raise
      return await self._repository.get_project_summary(project_id)


def _safe_timestamp(value: str) -> str:
  return value.replace(":", "").replace(".", "").replace("+", "-")


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()
