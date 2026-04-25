from __future__ import annotations

from app.Services.project_service import ProjectService
from app.Services.search.query import normalize_query, resource_types_for_scope
from app.Services.search.ranking import normalize_limit
from app.Services.search.repository import ProjectSearchRepository
from app.Services.search.resources import (
  ProjectSearchResourceBuilder,
  search_result_from_row,
  stale_resources,
)
from app.Utils.config import GenerationPresetDefault
from app.Utils.db import AsyncDatabase
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Schemas.search import (
  ProjectSearchResponse,
  ProjectSearchScope,
)


class ProjectSearchService:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
    project_service: ProjectService,
    generation_defaults: tuple[GenerationPresetDefault, ...],
  ) -> None:
    self._project_service = project_service
    self._repository = ProjectSearchRepository(db)
    self._resources = ProjectSearchResourceBuilder(
      db,
      store,
      paths,
      generation_defaults,
    )

  async def search_project(
    self,
    project_id: str,
    query: str,
    scope: ProjectSearchScope = "all",
    limit: int = 50,
  ) -> ProjectSearchResponse:
    normalized_query = normalize_query(query)
    if not normalized_query:
      return ProjectSearchResponse(query="", scope=scope, results=[])

    await self.ensure_project_index(project_id)
    rows = await self._repository.search(
      project_id,
      normalized_query,
      resource_types_for_scope(scope),
      normalize_limit(limit),
    )
    return ProjectSearchResponse(
      query=normalized_query,
      scope=scope,
      results=[search_result_from_row(row) for row in rows],
    )

  async def ensure_project_index(self, project_id: str) -> None:
    await self._project_service.get_manifest(project_id)
    meta_rows = await self._repository.meta_rows(project_id)
    meta = {
      (str(row["resource_type"]), str(row["resource_id"])): row
      for row in meta_rows
    }
    expected: set[tuple[str, str]] = set()

    for document in await self._resources.build_documents(project_id, meta, expected):
      await self._repository.upsert(document)

    await self._repository.delete_resources(
      project_id,
      stale_resources(meta_rows, expected),
    )
