from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from app.Schemas.common import PromptProfileVersionType, PromptRequestType
from app.Schemas.prompt_profiles import (
  PromptProfile,
  PromptProfileVersion,
  PromptProfileVersionDetail,
)
from app.Services.prompt_profiles.config import (
  REQUEST_API_CONFIG_ID_KEY,
  api_config_id_from_config,
)
from app.Services.prompt_profiles.versions import (
  snapshot_from_profile,
  version_detail_from_row,
  version_detail_from_values,
  version_from_row,
)
from app.Utils.db import AsyncDatabase, AsyncDBConnection
from app.Utils.errors import EntityNotFoundError


PROFILE_COLUMNS = """
  project_id, request_type, name, system_template, user_template, output_contract,
  chapter_ids_json, document_ids_json, config_json, is_system, created_at, updated_at
"""

VERSION_COLUMNS = """
  id, project_id, request_type, version_type, label, note, snapshot_json, created_at
"""


class PromptProfileRepository:
  def __init__(self, db: AsyncDatabase) -> None:
    self._db = db

  @asynccontextmanager
  async def transaction(self) -> AsyncIterator[AsyncDBConnection]:
    async with self._db.transaction() as conn:
      yield conn

  async def list_profile_rows(self, project_id: str) -> list[dict[str, object]]:
    return await self._db.fetch_all(
      f"""
      SELECT {PROFILE_COLUMNS}
      FROM prompt_profiles
      WHERE project_id = ?
      """,
      (project_id,),
    )

  async def fetch_profile_row(
    self, project_id: str, request_type: PromptRequestType
  ) -> dict[str, object] | None:
    return await self._db.fetch_one(
      f"""
      SELECT {PROFILE_COLUMNS}
      FROM prompt_profiles
      WHERE project_id = ? AND request_type = ?
      """,
      (project_id, request_type),
    )

  async def api_config_reference_count(self, config_id: str) -> int:
    rows = await self._db.fetch_all(
      "SELECT config_json FROM prompt_profiles",
    )
    return sum(
      1
      for row in rows
      if api_config_id_from_config(_config_from_json(row["config_json"])) == config_id
    )

  async def clear_api_config_references(
    self,
    conn: AsyncDBConnection,
    config_id: str,
    *,
    now: str,
  ) -> int:
    cursor = await conn.execute(
      """
      SELECT project_id, request_type, config_json
      FROM prompt_profiles
      """
    )
    rows = await cursor.fetchall()
    await cursor.close()
    updated_count = 0
    for row in rows:
      config = _config_from_json(row["config_json"])
      if api_config_id_from_config(config) != config_id:
        continue
      config.pop(REQUEST_API_CONFIG_ID_KEY, None)
      await conn.execute(
        """
        UPDATE prompt_profiles
        SET config_json = ?, updated_at = ?
        WHERE project_id = ? AND request_type = ?
        """,
        (
          json.dumps(config, ensure_ascii=False),
          now,
          row["project_id"],
          row["request_type"],
        ),
      )
      updated_count += 1
    return updated_count

  async def save_profile(
    self,
    conn: AsyncDBConnection,
    project_id: str,
    profile: PromptProfile,
    *,
    now: str,
  ) -> None:
    await conn.execute(
      """
      INSERT INTO prompt_profiles (
        project_id, request_type, name, system_template, user_template, output_contract,
        chapter_ids_json, document_ids_json, config_json, is_system, created_at, updated_at
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
      ON CONFLICT(project_id, request_type) DO UPDATE SET
        name = excluded.name,
        system_template = excluded.system_template,
        user_template = excluded.user_template,
        output_contract = excluded.output_contract,
        chapter_ids_json = excluded.chapter_ids_json,
        document_ids_json = excluded.document_ids_json,
        config_json = excluded.config_json,
        is_system = 0,
        updated_at = excluded.updated_at
      """,
      (
        project_id,
        profile.request_type,
        profile.name,
        profile.system_template,
        profile.user_template,
        profile.output_contract,
        json.dumps(profile.chapter_ids, ensure_ascii=False),
        json.dumps(profile.document_ids, ensure_ascii=False),
        json.dumps(profile.config, ensure_ascii=False),
        profile.created_at or profile.updated_at or now,
        profile.updated_at or now,
      ),
    )

  async def has_versions(
    self,
    conn: AsyncDBConnection,
    project_id: str,
    request_type: PromptRequestType,
  ) -> bool:
    cursor = await conn.execute(
      """
      SELECT 1
      FROM prompt_profile_versions
      WHERE project_id = ? AND request_type = ?
      LIMIT 1
      """,
      (project_id, request_type),
    )
    row = await cursor.fetchone()
    await cursor.close()
    return row is not None

  async def list_versions(
    self, project_id: str, request_type: PromptRequestType
  ) -> list[PromptProfileVersion]:
    rows = await self._db.fetch_all(
      f"""
      SELECT {VERSION_COLUMNS}
      FROM prompt_profile_versions
      WHERE project_id = ? AND request_type = ?
      ORDER BY created_at DESC, id DESC
      """,
      (project_id, request_type),
    )
    return [version_from_row(row) for row in rows]

  async def get_version(
    self,
    project_id: str,
    request_type: PromptRequestType,
    version_id: str,
  ) -> PromptProfileVersionDetail:
    row = await self._db.fetch_one(
      f"""
      SELECT {VERSION_COLUMNS}
      FROM prompt_profile_versions
      WHERE project_id = ? AND request_type = ? AND id = ?
      """,
      (project_id, request_type, version_id),
    )
    if row is None:
      raise EntityNotFoundError(f"Prompt profile version not found: {version_id}")
    return version_detail_from_row(row)

  async def create_version(
    self,
    conn: AsyncDBConnection,
    project_id: str,
    profile: PromptProfile,
    version_type: PromptProfileVersionType,
    *,
    label: str | None = None,
    note: str = "",
    created_at: str,
  ) -> PromptProfileVersionDetail:
    version_id = f"prompt-{profile.request_type}-{version_type}-{uuid4().hex[:12]}"
    snapshot = snapshot_from_profile(profile)
    await conn.execute(
      """
      INSERT INTO prompt_profile_versions (
        id, project_id, request_type, version_type, label, note, snapshot_json, created_at
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      """,
      (
        version_id,
        project_id,
        profile.request_type,
        version_type,
        label,
        note,
        json.dumps(snapshot.model_dump(), ensure_ascii=False),
        created_at,
      ),
    )
    return version_detail_from_values(
      id=version_id,
      project_id=project_id,
      request_type=profile.request_type,
      version_type=version_type,
      label=label,
      note=note,
      snapshot=snapshot,
      created_at=created_at,
    )


def _config_from_json(value: object) -> dict[str, object]:
  try:
    payload = json.loads(str(value))
  except json.JSONDecodeError:
    return {}
  return payload if isinstance(payload, dict) else {}
