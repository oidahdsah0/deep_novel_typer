from __future__ import annotations

from typing import Any

from app.Schemas.api_configs import APIConfig, CreateAPIConfigRequest, UpdateAPIConfigRequest
from app.Schemas.common import APIConfigKind
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityNotFoundError


CONFIG_COLUMNS = """
  id, name, provider, kind, protocol, api_key, api_key_required, base_url,
  mode, model, thinking_enabled, reasoning_effort, max_tokens, context_window_tokens,
  temperature, top_p, top_k, dimensions, is_default, created_at, updated_at
"""


class APIConfigRepository:
  def __init__(self, db: AsyncDatabase) -> None:
    self._db = db

  async def count_by_kind(self, kind: APIConfigKind) -> int:
    row = await self._db.fetch_one(
      "SELECT COUNT(*) AS count FROM api_configs WHERE kind = ?",
      (kind,),
    )
    return int(row["count"] or 0) if row is not None else 0

  async def list_configs(self, kind: APIConfigKind | None = None) -> list[APIConfig]:
    params: tuple[str, ...] = (kind,) if kind else ()
    where = "WHERE kind = ?" if kind else ""
    rows = await self._db.fetch_all(
      f"""
      SELECT
        {CONFIG_COLUMNS}
      FROM api_configs
      {where}
      ORDER BY kind ASC, is_default DESC, updated_at DESC, name ASC
      """,
      params,
    )
    return [config_from_row(row) for row in rows]

  async def fetch_config_row(
    self, config_id: str | None, kind: APIConfigKind | None = None
  ) -> dict[str, object] | None:
    query = f"""
      SELECT
        {CONFIG_COLUMNS}
      FROM api_configs
    """
    if config_id:
      if kind is not None:
        return await self._db.fetch_one(
          f"{query} WHERE id = ? AND kind = ?",
          (config_id, kind),
        )
      return await self._db.fetch_one(f"{query} WHERE id = ?", (config_id,))
    if kind is None:
      return None
    return await self._db.fetch_one(
      f"{query} WHERE kind = ? AND is_default = 1 ORDER BY updated_at DESC",
      (kind,),
    )

  async def require_config_row(self, config_id: str) -> dict[str, object]:
    row = await self.fetch_config_row(config_id)
    if row is None:
      raise EntityNotFoundError(f"API config not found: {config_id}")
    return row

  async def config_exists(self, config_id: str) -> bool:
    row = await self._db.fetch_one("SELECT id FROM api_configs WHERE id = ?", (config_id,))
    return row is not None

  async def has_configs(self, kind: APIConfigKind) -> bool:
    return await self.count_by_kind(kind) > 0

  async def perspective_link_count(self, config_id: str) -> int:
    row = await self._db.fetch_one(
      "SELECT COUNT(*) AS count FROM perspectives WHERE api_config_id = ?",
      (config_id,),
    )
    return int(row["count"] or 0) if row is not None else 0

  async def insert_config(
    self,
    config_id: str,
    request: CreateAPIConfigRequest,
    *,
    api_key: str | None,
    is_default: bool,
    now: str,
  ) -> None:
    async with self._db.transaction() as conn:
      if is_default:
        await conn.execute(
          "UPDATE api_configs SET is_default = 0 WHERE kind = ?",
          (request.kind,),
        )
      await conn.execute(
        """
        INSERT INTO api_configs (
          id, name, provider, kind, protocol, api_key, api_key_required, base_url,
          mode, model, thinking_enabled, reasoning_effort, max_tokens,
          context_window_tokens, temperature, top_p, top_k, dimensions, is_default,
          created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
          config_id,
          request.name,
          request.provider,
          request.kind,
          request.protocol,
          api_key,
          int(request.api_key_required),
          request.base_url,
          "non_stream",
          request.model,
          int(request.thinking_enabled),
          request.reasoning_effort,
          request.max_tokens,
          request.context_window_tokens,
          request.temperature,
          request.top_p,
          request.top_k,
          request.dimensions,
          int(is_default),
          now,
          now,
        ),
      )

  async def update_config(
    self,
    config_id: str,
    request: UpdateAPIConfigRequest,
    *,
    api_key: str | None,
    is_default: bool,
    now: str,
  ) -> None:
    async with self._db.transaction() as conn:
      if request.is_default:
        await conn.execute(
          "UPDATE api_configs SET is_default = 0 WHERE kind = ?",
          (request.kind,),
        )
      await conn.execute(
        """
        UPDATE api_configs
        SET
          name = ?,
          provider = ?,
          kind = ?,
          protocol = ?,
          api_key = ?,
          api_key_required = ?,
          base_url = ?,
          mode = ?,
          model = ?,
          thinking_enabled = ?,
          reasoning_effort = ?,
          max_tokens = ?,
          context_window_tokens = ?,
          temperature = ?,
          top_p = ?,
          top_k = ?,
          dimensions = ?,
          is_default = ?,
          updated_at = ?
        WHERE id = ?
        """,
        (
          request.name,
          request.provider,
          request.kind,
          request.protocol,
          api_key,
          int(request.api_key_required),
          request.base_url,
          "non_stream",
          request.model,
          int(request.thinking_enabled),
          request.reasoning_effort,
          request.max_tokens,
          request.context_window_tokens,
          request.temperature,
          request.top_p,
          request.top_k,
          request.dimensions,
          int(is_default),
          now,
          config_id,
        ),
      )

  async def delete_config(
    self,
    config_id: str,
    *,
    kind: APIConfigKind,
    was_default: bool,
    now: str,
  ) -> None:
    async with self._db.transaction() as conn:
      await self.delete_config_with_connection(
        conn,
        config_id,
        kind=kind,
        was_default=was_default,
        now=now,
      )

  async def delete_config_with_connection(
    self,
    conn: Any,
    config_id: str,
    *,
    kind: APIConfigKind,
    was_default: bool,
    now: str,
  ) -> None:
    await conn.execute("DELETE FROM api_configs WHERE id = ?", (config_id,))
    if was_default:
      await conn.execute(
        """
        UPDATE api_configs
        SET is_default = 1, updated_at = ?
        WHERE id = (
          SELECT id FROM api_configs
          WHERE kind = ?
          ORDER BY updated_at DESC, name ASC
          LIMIT 1
        )
        """,
        (now, kind),
      )

  async def set_default(self, config_id: str, *, kind: APIConfigKind, now: str) -> None:
    async with self._db.transaction() as conn:
      await conn.execute(
        "UPDATE api_configs SET is_default = 0 WHERE kind = ?",
        (kind,),
      )
      await conn.execute(
        "UPDATE api_configs SET is_default = 1, updated_at = ? WHERE id = ?",
        (now, config_id),
      )


def config_from_row(row: dict[str, object]) -> APIConfig:
  return APIConfig(
    id=str(row["id"]),
    name=str(row["name"]),
    provider=row["provider"],  # type: ignore[arg-type]
    kind=row["kind"],  # type: ignore[arg-type]
    protocol=row["protocol"],  # type: ignore[arg-type]
    base_url=str(row["base_url"]),
    api_key_required=bool(row["api_key_required"]),
    api_key_configured=bool(row["api_key"]),
    mode="non_stream",
    model=str(row["model"]),
    thinking_enabled=bool(row["thinking_enabled"]),
    reasoning_effort=row["reasoning_effort"],  # type: ignore[arg-type]
    max_tokens=int(row["max_tokens"]),
    context_window_tokens=int(row["context_window_tokens"]),
    temperature=float(row["temperature"]) if row["temperature"] is not None else None,
    top_p=float(row["top_p"]) if row["top_p"] is not None else None,
    top_k=int(row["top_k"]) if row["top_k"] is not None else None,
    dimensions=int(row["dimensions"]) if row["dimensions"] is not None else None,
    is_default=bool(row["is_default"]),
    created_at=str(row["created_at"]),
    updated_at=str(row["updated_at"]),
  )
