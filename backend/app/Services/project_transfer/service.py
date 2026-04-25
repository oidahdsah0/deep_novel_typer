from __future__ import annotations

from app.Services.project_transfer.exporter import ProjectExporter
from app.Services.project_transfer.importer import ProjectImporter
from app.Utils.db import AsyncDatabase
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Schemas.project_transfer import (
  ProjectExportOptions,
  ProjectImportResponse,
)


class ProjectTransferService:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
    locks: AsyncLockRegistry,
  ) -> None:
    self._locks = locks
    self._exporter = ProjectExporter(db, store, paths)
    self._importer = ProjectImporter(db, store, paths)

  async def export_project(self, project_id: str, options: ProjectExportOptions) -> bytes:
    async with self._locks.get(f"{project_id}:project-transfer"):
      return await self._exporter.export_project(project_id, options)

  async def import_project(self, raw: bytes) -> ProjectImportResponse:
    async with self._locks.get("project-transfer:import"):
      return await self._importer.import_project(raw)
