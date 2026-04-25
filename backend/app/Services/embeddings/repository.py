from __future__ import annotations

from collections.abc import Sequence
import json

from app.Schemas.common import EmbeddingAnalysisStatus, EmbeddingResourceType, EmbeddingToolType
from app.Schemas.embeddings import EmbeddingProjectSettings, EmbeddingTag
from app.Utils.db import AsyncDatabase, AsyncDBConnection


class EmbeddingRepository:
  def __init__(self, db: AsyncDatabase) -> None:
    self._db = db

  async def list_tags(self, project_id: str) -> list[EmbeddingTag]:
    rows = await self._db.fetch_all(
      """
      SELECT
        id, project_id, name, description, color, is_enabled,
        embedding_config_id, embedding_model_signature, embedding_vector_ref,
        created_at, updated_at
      FROM embedding_tags
      WHERE project_id = ?
      ORDER BY created_at ASC, name ASC
      """,
      (project_id,),
    )
    return [_tag_from_row(row) for row in rows]

  async def fetch_tag_row(self, project_id: str, tag_id: str) -> dict[str, object] | None:
    return await self._db.fetch_one(
      """
      SELECT
        id, project_id, name, description, color, is_enabled,
        embedding_config_id, embedding_model_signature, embedding_vector_ref,
        created_at, updated_at
      FROM embedding_tags
      WHERE project_id = ? AND id = ?
      """,
      (project_id, tag_id),
    )

  async def tag_exists(self, project_id: str, tag_id: str) -> bool:
    return await self.fetch_tag_row(project_id, tag_id) is not None

  async def fetch_project_settings_row(self, project_id: str) -> dict[str, object] | None:
    return await self._db.fetch_one(
      """
      SELECT project_id, embedding_config_id, segmentation_mode, segment_size, algorithm, updated_at
      FROM embedding_project_settings
      WHERE project_id = ?
      """,
      (project_id,),
    )

  async def upsert_project_settings(
    self,
    conn: AsyncDBConnection,
    *,
    project_id: str,
    api_config_id: str | None,
    segmentation_mode: str,
    segment_size: int,
    algorithm: str,
    now: str,
  ) -> None:
    await conn.execute(
      """
      INSERT INTO embedding_project_settings (
        project_id, embedding_config_id, segmentation_mode, segment_size, algorithm, updated_at
      )
      VALUES (?, ?, ?, ?, ?, ?)
      ON CONFLICT(project_id) DO UPDATE SET
        embedding_config_id = excluded.embedding_config_id,
        segmentation_mode = excluded.segmentation_mode,
        segment_size = excluded.segment_size,
        algorithm = excluded.algorithm,
        updated_at = excluded.updated_at
      """,
      (project_id, api_config_id, segmentation_mode, segment_size, algorithm, now),
    )

  async def insert_tag(
    self,
    conn: AsyncDBConnection,
    *,
    project_id: str,
    tag_id: str,
    name: str,
    description: str,
    color: str,
    is_enabled: bool,
    now: str,
  ) -> None:
    await conn.execute(
      """
      INSERT INTO embedding_tags (
        id, project_id, name, description, color, is_enabled, created_at, updated_at
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      """,
      (tag_id, project_id, name, description, color, int(is_enabled), now, now),
    )

  async def update_tag(
    self,
    conn: AsyncDBConnection,
    *,
    project_id: str,
    tag_id: str,
    assignments: Sequence[str],
    params: Sequence[object],
  ) -> None:
    await conn.execute(
      f"""
      UPDATE embedding_tags
      SET {', '.join(assignments)}
      WHERE project_id = ? AND id = ?
      """,
      (*params, project_id, tag_id),
    )

  async def delete_tag(
    self, conn: AsyncDBConnection, *, project_id: str, tag_id: str
  ) -> None:
    await conn.execute(
      "DELETE FROM embedding_tags WHERE project_id = ? AND id = ?",
      (project_id, tag_id),
    )

  async def update_tag_embedding_ref(
    self,
    conn: AsyncDBConnection,
    *,
    project_id: str,
    tag_id: str,
    embedding_config_id: str,
    model_signature: str,
    vector_ref: str,
    now: str,
  ) -> None:
    await conn.execute(
      """
      UPDATE embedding_tags
      SET embedding_config_id = ?,
          embedding_model_signature = ?,
          embedding_vector_ref = ?,
          updated_at = ?
      WHERE project_id = ? AND id = ?
      """,
      (embedding_config_id, model_signature, vector_ref, now, project_id, tag_id),
    )

  async def insert_run(
    self,
    conn: AsyncDBConnection,
    *,
    run_id: str,
    project_id: str,
    resource_type: EmbeddingResourceType,
    resource_id: str,
    tool_type: EmbeddingToolType,
    status: EmbeddingAnalysisStatus,
    embedding_config_id: str,
    model_signature: str,
    segmentation_mode: str,
    algorithm: str,
    params: dict[str, object],
    source_content_hash: str,
    error_message: str | None,
    now: str,
  ) -> None:
    await conn.execute(
      """
      INSERT INTO embedding_analysis_runs (
        id, project_id, resource_type, resource_id, tool_type, status,
        embedding_config_id, model_signature, segmentation_mode, algorithm,
        params_json, source_content_hash, error_message, created_at, updated_at
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """,
      (
        run_id,
        project_id,
        resource_type,
        resource_id,
        tool_type,
        status,
        embedding_config_id,
        model_signature,
        segmentation_mode,
        algorithm,
        json.dumps(params, ensure_ascii=False, sort_keys=True),
        source_content_hash,
        error_message,
        now,
        now,
      ),
    )

  async def insert_items(
    self,
    conn: AsyncDBConnection,
    *,
    run_id: str,
    rows: Sequence[tuple[object, ...]],
  ) -> None:
    if not rows:
      return
    await conn.executemany(
      """
      INSERT INTO embedding_analysis_items (
        run_id, token_index, text, normalized_text, start_offset, end_offset,
        vector_ref, tag_id, raw_score, raw_distance, closeness, cluster_id, x, y,
        metadata_json
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      """,
      rows,
    )


def _tag_from_row(row: dict[str, object]) -> EmbeddingTag:
  return EmbeddingTag(
    id=str(row["id"]),
    project_id=str(row["project_id"]),
    name=str(row["name"]),
    description=str(row["description"] or ""),
    color=str(row["color"] or "#d94841"),
    is_enabled=bool(row["is_enabled"]),
    embedding_config_id=(
      str(row["embedding_config_id"]) if row["embedding_config_id"] is not None else None
    ),
    embedding_model_signature=(
      str(row["embedding_model_signature"])
      if row["embedding_model_signature"] is not None
      else None
    ),
    embedding_vector_ref=(
      str(row["embedding_vector_ref"]) if row["embedding_vector_ref"] is not None else None
    ),
    created_at=str(row["created_at"]),
    updated_at=str(row["updated_at"]),
  )


def settings_from_row(row: dict[str, object]) -> EmbeddingProjectSettings:
  return EmbeddingProjectSettings(
    project_id=str(row["project_id"]),
    api_config_id=(
      str(row["embedding_config_id"]) if row["embedding_config_id"] is not None else None
    ),
    segmentation_mode=str(row["segmentation_mode"]),  # type: ignore[arg-type]
    segment_size=int(row["segment_size"] or 1),
    algorithm=str(row["algorithm"]),  # type: ignore[arg-type]
    updated_at=str(row["updated_at"]) if row["updated_at"] is not None else None,
  )
