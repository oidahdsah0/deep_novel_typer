from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.Services.project_transfer.archive import ProjectArchivePayload, safe_relative_path
from app.Services.project_transfer.import_files import (
  chapter_word_count,
  content_text,
  sha256_text,
)
from app.Services.project_transfer.import_validation import (
  import_value,
  rows,
  with_project_id,
)
from app.Utils.db import AsyncDatabase
from app.Utils.errors import DomainError
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Schemas.projects import ProjectSummary


class ProjectImportDatabaseWriter:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    paths: PathResolver,
  ) -> None:
    self._db = db
    self._store = store
    self._paths = paths

  async def next_project_id(self, base_id: str) -> str:
    candidate = base_id
    suffix = 2
    while await self._project_id_exists(candidate) or await self._store.exists(
      self._paths.project(candidate).root
    ):
      candidate = f"{base_id}-{suffix}"
      suffix += 1
    return candidate

  async def import_rows(
    self,
    *,
    payload: ProjectArchivePayload,
    source_project: dict[str, Any],
    target_project_id: str,
    target_title: str,
    target_root: Path,
    warnings: list[str],
  ) -> ProjectSummary:
    perspective_rows = rows(payload, "perspectives")
    api_config_map = await self._api_config_map(
      rows(payload, "api_config_refs"),
      perspective_rows,
      warnings,
    )
    async with self._db.transaction() as conn:
      now = _now()
      await conn.execute(
        """
        INSERT INTO projects (
          id, title, subtitle, description, genre, status, root_path,
          created_at, updated_at, last_opened_at, deleted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
        """,
        (
          target_project_id,
          target_title,
          str(source_project.get("subtitle") or ""),
          str(source_project.get("description") or ""),
          str(source_project.get("genre") or ""),
          str(source_project.get("status") or "drafting"),
          str(target_root),
          str(source_project.get("created_at") or now),
          now,
        ),
      )
      await self._insert_rows(
        conn,
        "chapters",
        [
          with_project_id(
            row,
            target_project_id,
            extra={
              "file_path": safe_relative_path(row["file_path"]),
              "word_count": chapter_word_count(payload, row),
            },
          )
          for row in rows(payload, "chapters")
        ],
        [
          "id",
          "project_id",
          "title",
          "order_index",
          "word_count",
          "file_path",
          "writing_synopsis",
          "writing_synopsis_updated_at",
          "created_at",
          "updated_at",
        ],
      )
      await self._insert_rows(
        conn,
        "chapter_nodes",
        [with_project_id(row, target_project_id) for row in rows(payload, "chapter_nodes")],
        [
          "id",
          "project_id",
          "parent_id",
          "type",
          "title",
          "chapter_id",
          "order_index",
          "created_at",
          "updated_at",
        ],
      )
      await self._insert_document_nodes(conn, payload, target_project_id)
      await self._insert_perspectives(
        conn, perspective_rows, target_project_id, api_config_map
      )
      await self._insert_project_rows(
        conn,
        "generation_presets",
        payload,
        target_project_id,
        [
          "project_id",
          "kind",
          "preset_id",
          "name",
          "content",
          "is_system",
          "is_hidden",
          "created_at",
          "updated_at",
        ],
      )
      await self._insert_project_rows(
        conn,
        "prompt_profiles",
        payload,
        target_project_id,
        [
          "project_id",
          "request_type",
          "name",
          "system_template",
          "user_template",
          "output_contract",
          "chapter_ids_json",
          "document_ids_json",
          "config_json",
          "is_system",
          "created_at",
          "updated_at",
        ],
      )
      await self._insert_project_rows(
        conn,
        "prompt_profile_versions",
        payload,
        target_project_id,
        [
          "id",
          "project_id",
          "request_type",
          "version_type",
          "label",
          "note",
          "snapshot_json",
          "created_at",
        ],
      )
      await self._insert_rows(
        conn,
        "resource_versions",
        [
          with_project_id(
            row,
            target_project_id,
            extra={"file_path": safe_relative_path(row["file_path"])},
          )
          for row in rows(payload, "resource_versions")
        ],
        [
          "id",
          "project_id",
          "resource_type",
          "resource_id",
          "resource_title",
          "version_type",
          "label",
          "note",
          "file_path",
          "content_hash",
          "word_count",
          "char_count",
          "created_at",
        ],
      )
      await self._rebuild_chapter_search(conn, target_project_id, payload)
    return await self.project_summary(target_project_id)

  async def project_summary(self, project_id: str) -> ProjectSummary:
    row = await self._db.fetch_one(
      """
      SELECT
        p.*,
        COUNT(c.id) AS chapter_count,
        COALESCE(SUM(c.word_count), 0) AS word_count
      FROM projects p
      LEFT JOIN chapters c ON c.project_id = p.id
      WHERE p.id = ?
      GROUP BY p.id
      """,
      (project_id,),
    )
    if row is None:
      raise DomainError(f"Imported project was not created: {project_id}")
    return ProjectSummary(
      id=str(row["id"]),
      title=str(row["title"]),
      subtitle=str(row["subtitle"] or ""),
      description=str(row["description"] or ""),
      genre=str(row["genre"] or ""),
      status=row["status"],  # type: ignore[arg-type]
      created_at=str(row["created_at"]),
      updated_at=str(row["updated_at"]),
      last_opened_at=row["last_opened_at"],  # type: ignore[arg-type]
      deleted_at=row["deleted_at"],  # type: ignore[arg-type]
      chapter_count=int(row["chapter_count"] or 0),
      word_count=int(row["word_count"] or 0),
    )

  async def _insert_document_nodes(self, conn, payload: ProjectArchivePayload, project_id: str) -> None:
    await self._insert_rows(
      conn,
      "document_nodes",
      [
        with_project_id(
          row,
          project_id,
          extra={
            "file_path": safe_relative_path(row["file_path"])
            if row.get("file_path")
            else None,
          },
        )
        for row in rows(payload, "document_nodes")
      ],
      [
        "id",
        "project_id",
        "parent_id",
        "type",
        "title",
        "file_path",
        "order_index",
        "created_at",
        "updated_at",
      ],
    )

  async def _insert_perspectives(
    self,
    conn,
    perspective_rows: list[dict[str, Any]],
    project_id: str,
    api_config_map: dict[str, str | None],
  ) -> None:
    await self._insert_rows(
      conn,
      "perspectives",
      [
        with_project_id(
          row,
          project_id,
          extra={"api_config_id": api_config_map.get(str(row["api_config_id"]))}
          if row.get("api_config_id")
          else {"api_config_id": None},
        )
        for row in perspective_rows
      ],
      [
        "id",
        "project_id",
        "name",
        "description",
        "instructions",
        "api_config_id",
        "is_enabled",
        "created_at",
        "updated_at",
      ],
    )

  async def _insert_project_rows(
    self,
    conn,
    table: str,
    payload: ProjectArchivePayload,
    project_id: str,
    columns: list[str],
  ) -> None:
    await self._insert_rows(
      conn,
      table,
      [with_project_id(row, project_id) for row in rows(payload, table)],
      columns,
    )

  async def _insert_rows(
    self, conn, table: str, row_values: list[dict[str, Any]], columns: list[str]
  ) -> None:
    if not row_values:
      return
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(columns)
    for row in row_values:
      await conn.execute(
        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})",
        tuple(import_value(table, row, column) for column in columns),
      )

  async def _api_config_map(
    self,
    refs: list[dict[str, Any]],
    perspectives: list[dict[str, Any]],
    warnings: list[str],
  ) -> dict[str, str | None]:
    ref_by_id = {str(row["id"]): row for row in refs if row.get("id")}
    result: dict[str, str | None] = {}
    source_ids = {
      str(row["api_config_id"])
      for row in perspectives
      if row.get("api_config_id")
    }
    for source_id in source_ids:
      if await self._api_config_exists(source_id):
        result[source_id] = source_id
        continue
      ref = ref_by_id.get(source_id)
      matched = await self._match_api_config(ref) if ref else None
      result[source_id] = matched
      if matched is None:
        warnings.append(
          f"原 API 配置 {source_id} 在本机不存在，相关视角已设为默认配置。"
        )
    return result

  async def _api_config_exists(self, config_id: str) -> bool:
    row = await self._db.fetch_one(
      "SELECT id FROM api_configs WHERE id = ? AND kind = 'llm'",
      (config_id,),
    )
    return row is not None

  async def _match_api_config(self, ref: dict[str, Any] | None) -> str | None:
    if not ref:
      return None
    row = await self._db.fetch_one(
      """
      SELECT id
      FROM api_configs
      WHERE kind = ? AND provider = ? AND base_url = ? AND model = ?
      ORDER BY is_default DESC, updated_at DESC
      LIMIT 1
      """,
      (
        ref.get("kind") or "llm",
        ref.get("provider") or "",
        ref.get("base_url") or "",
        ref.get("model") or "",
      ),
    )
    return str(row["id"]) if row else None

  async def _project_id_exists(self, project_id: str) -> bool:
    row = await self._db.fetch_one("SELECT id FROM projects WHERE id = ?", (project_id,))
    return row is not None

  async def _rebuild_chapter_search(
    self,
    conn,
    project_id: str,
    payload: ProjectArchivePayload,
  ) -> None:
    for row in rows(payload, "chapters"):
      chapter_id = str(row["id"])
      content = content_text(payload, safe_relative_path(row["file_path"]))
      cursor = await conn.execute(
        """
        INSERT INTO chapter_search_meta (project_id, chapter_id, content_hash, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (project_id, chapter_id, sha256_text(content), str(row["updated_at"])),
      )
      rowid = cursor.lastrowid
      await cursor.close()
      await conn.execute(
        """
        INSERT INTO chapter_search_fts (rowid, project_id, chapter_id, title, content)
        VALUES (?, ?, ?, ?, ?)
        """,
        (rowid, project_id, chapter_id, str(row["title"]), content),
      )


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()
