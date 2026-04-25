from __future__ import annotations

from app.Services.api_configs import APIConfigService
from app.Services.project_service import ProjectService
from app.Services.version_service import VersionService
from app.Utils.db import AsyncDatabase
from app.Schemas.workspace import LibrarySnapshot, LibraryStats


class LibraryService:
  def __init__(
    self,
    db: AsyncDatabase,
    project_service: ProjectService,
    api_config_service: APIConfigService,
    version_service: VersionService,
  ) -> None:
    self._db = db
    self._project_service = project_service
    self._api_config_service = api_config_service
    self._version_service = version_service

  async def get_library(self) -> LibrarySnapshot:
    projects = await self._project_service.list_projects()
    recent_projects = [
      project
      for project in sorted(
        projects,
        key=lambda item: item.last_opened_at or item.updated_at,
        reverse=True,
      )
      if project.last_opened_at is not None
    ][:5]
    stats = await self._stats()
    api_configs = await self._api_config_service.list_configs()
    version_settings = await self._version_service.get_settings()
    return LibrarySnapshot(
      projects=projects,
      recent_projects=recent_projects,
      stats=stats,
      api_configs=api_configs,
      api_config_templates=self._api_config_service.list_templates(),
      version_settings=version_settings,
    )

  async def _stats(self) -> LibraryStats:
    row = await self._db.fetch_one(
      """
      SELECT
        COUNT(DISTINCT CASE WHEN p.deleted_at IS NULL THEN p.id END) AS active_count,
        COUNT(DISTINCT CASE WHEN p.deleted_at IS NOT NULL THEN p.id END) AS trash_count,
        COALESCE(SUM(CASE WHEN p.deleted_at IS NULL THEN c.word_count ELSE 0 END), 0)
          AS total_words
      FROM projects p
      LEFT JOIN chapters c ON c.project_id = p.id
      """
    )
    if row is None:
      return LibraryStats(active_count=0, trash_count=0, total_words=0)
    return LibraryStats(
      active_count=int(row["active_count"] or 0),
      trash_count=int(row["trash_count"] or 0),
      total_words=int(row["total_words"] or 0),
    )
