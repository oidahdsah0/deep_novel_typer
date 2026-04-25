from __future__ import annotations

from datetime import UTC, datetime

from app.Services.project_service import ProjectService
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityConflictError, EntityNotFoundError
from app.Utils.ids import slugify
from app.Utils.locks import AsyncLockRegistry
from app.Schemas.perspectives import CreatePerspectiveRequest, Perspective, UpdatePerspectiveRequest


class PerspectiveService:
  def __init__(
    self,
    db: AsyncDatabase,
    locks: AsyncLockRegistry,
    project_service: ProjectService,
  ) -> None:
    self._db = db
    self._locks = locks
    self._project_service = project_service

  async def list_perspectives(self, project_id: str) -> list[Perspective]:
    await self._project_service.get_manifest(project_id)
    rows = await self._db.fetch_all(
      """
      SELECT
        id, name, description, instructions, api_config_id, is_enabled, created_at, updated_at
      FROM perspectives
      WHERE project_id = ?
      ORDER BY created_at ASC, name ASC
      """,
      (project_id,),
    )
    return [_perspective_from_row(row) for row in rows]

  async def create_perspective(
    self, project_id: str, request: CreatePerspectiveRequest
  ) -> Perspective:
    await self._project_service.get_manifest(project_id)
    perspective_id = slugify(request.name, fallback_prefix="perspective")
    now = _now()

    async with self._locks.get(f"{project_id}:perspectives"):
      if await self._perspective_exists(project_id, perspective_id):
        raise EntityConflictError(f"Perspective already exists: {perspective_id}")
      await self._ensure_api_config_exists(request.api_config_id)

      await self._db.execute(
        """
        INSERT INTO perspectives (
          id, project_id, name, description, instructions,
          api_config_id, is_enabled, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
        """,
        (
          perspective_id,
          project_id,
          request.name,
          request.description,
          request.instructions,
          request.api_config_id,
          now,
          now,
        ),
      )
      await self._project_service.touch_project(project_id, now)
      return Perspective(
        id=perspective_id,
        name=request.name,
        description=request.description,
        instructions=request.instructions,
        api_config_id=request.api_config_id,
        is_enabled=False,
        created_at=now,
        updated_at=now,
      )

  async def update_perspective(
    self, project_id: str, perspective_id: str, request: UpdatePerspectiveRequest
  ) -> Perspective:
    await self._project_service.get_manifest(project_id)
    await self._perspective_row(project_id, perspective_id)
    updates = request.model_dump(exclude_unset=True)
    if not updates:
      return _perspective_from_row(await self._perspective_row(project_id, perspective_id))
    if "api_config_id" in updates:
      await self._ensure_api_config_exists(updates["api_config_id"])

    now = _now()
    assignments = []
    params: list[object] = []
    for field, value in updates.items():
      assignments.append(f"{field} = ?")
      params.append(int(value) if field == "is_enabled" else value)
    params.extend([now, project_id, perspective_id])
    await self._db.execute(
      f"""
      UPDATE perspectives
      SET {', '.join(assignments)}, updated_at = ?
      WHERE project_id = ? AND id = ?
      """,
      params,
    )
    await self._project_service.touch_project(project_id, now)
    return _perspective_from_row(await self._perspective_row(project_id, perspective_id))

  async def delete_perspective(self, project_id: str, perspective_id: str) -> None:
    await self._project_service.get_manifest(project_id)
    await self._perspective_row(project_id, perspective_id)
    now = _now()
    await self._db.execute(
      "DELETE FROM perspectives WHERE project_id = ? AND id = ?",
      (project_id, perspective_id),
    )
    await self._project_service.touch_project(project_id, now)

  async def _perspective_exists(self, project_id: str, perspective_id: str) -> bool:
    row = await self._db.fetch_one(
      "SELECT id FROM perspectives WHERE project_id = ? AND id = ?",
      (project_id, perspective_id),
    )
    return row is not None

  async def _perspective_row(self, project_id: str, perspective_id: str) -> dict[str, object]:
    row = await self._db.fetch_one(
      """
      SELECT
        id, name, description, instructions, api_config_id, is_enabled, created_at, updated_at
      FROM perspectives
      WHERE project_id = ? AND id = ?
      """,
      (project_id, perspective_id),
    )
    if row is None:
      raise EntityNotFoundError(f"Perspective not found: {perspective_id}")
    return row

  async def _ensure_api_config_exists(self, api_config_id: object) -> None:
    if api_config_id is None:
      return
    row = await self._db.fetch_one(
      "SELECT id FROM api_configs WHERE id = ? AND kind = 'llm'",
      (str(api_config_id),),
    )
    if row is None:
      raise EntityNotFoundError(f"API config not found: {api_config_id}")


def _perspective_from_row(row: dict[str, object]) -> Perspective:
  return Perspective(
    id=str(row["id"]),
    name=str(row["name"]),
    description=str(row["description"] or ""),
    instructions=str(row["instructions"]),
    api_config_id=str(row["api_config_id"]) if row["api_config_id"] else None,
    is_enabled=bool(row["is_enabled"]),
    created_at=str(row["created_at"]),
    updated_at=str(row["updated_at"]),
  )


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()
