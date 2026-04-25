from __future__ import annotations

import aiosqlite


async def _run_migrations(conn: aiosqlite.Connection) -> None:
  await _add_column_if_missing(conn, "perspectives", "api_config_id", "TEXT")
  await _add_column_if_missing(conn, "api_configs", "provider", "TEXT NOT NULL DEFAULT 'deepseek'")
  await _add_column_if_missing(conn, "api_configs", "kind", "TEXT NOT NULL DEFAULT 'llm'")
  await _add_column_if_missing(
    conn, "api_configs", "protocol", "TEXT NOT NULL DEFAULT 'openai_compatible'"
  )
  await _add_column_if_missing(
    conn, "api_configs", "api_key_required", "INTEGER NOT NULL DEFAULT 1"
  )
  await _add_column_if_missing(conn, "api_configs", "top_p", "REAL")
  await _add_column_if_missing(conn, "api_configs", "top_k", "INTEGER")
  await _add_column_if_missing(conn, "api_configs", "dimensions", "INTEGER")
  await _add_column_if_missing(
    conn,
    "api_configs",
    "context_window_tokens",
    "INTEGER NOT NULL DEFAULT 1000000",
  )
  await conn.execute("UPDATE api_configs SET mode = 'non_stream' WHERE mode != 'non_stream'")
  await conn.execute("DROP INDEX IF EXISTS idx_api_configs_default")
  await conn.execute(
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_api_configs_default_kind
    ON api_configs(kind)
    WHERE is_default = 1
    """
  )
  await conn.execute("DROP TABLE IF EXISTS llm_request_settings")
  await conn.execute("DROP TABLE IF EXISTS llm_request_logs")
  await conn.execute("DROP TABLE IF EXISTS llm_token_usage_daily")
  await _add_column_if_missing(
    conn,
    "prompt_profiles",
    "output_contract",
    "TEXT NOT NULL DEFAULT ''",
  )
  await _add_column_if_missing(
    conn,
    "chapters",
    "writing_synopsis",
    "TEXT NOT NULL DEFAULT ''",
  )
  await _add_column_if_missing(
    conn,
    "chapters",
    "writing_synopsis_updated_at",
    "TEXT NOT NULL DEFAULT ''",
  )
  await conn.execute(
    """
    UPDATE chapters
    SET writing_synopsis_updated_at = updated_at
    WHERE writing_synopsis_updated_at = ''
    """
  )
  await _migrate_chapter_nodes(conn)
  await conn.execute("DROP TABLE IF EXISTS documents")
  await _create_embedding_project_settings(conn)
  await _create_typewriter_layout_settings(conn)
  await _remove_legacy_default_perspectives(conn)


async def _add_column_if_missing(
  conn: aiosqlite.Connection, table: str, column: str, definition: str
) -> None:
  cursor = await conn.execute(f"PRAGMA table_info({table})")
  rows = await cursor.fetchall()
  await cursor.close()
  if any(str(row["name"]) == column for row in rows):
    return
  await conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


async def _migrate_chapter_nodes(conn: aiosqlite.Connection) -> None:
  await conn.execute(
    """
    INSERT OR IGNORE INTO chapter_nodes (
      id, project_id, parent_id, type, title, chapter_id, order_index, created_at, updated_at
    )
    SELECT
      id,
      project_id,
      NULL,
      'chapter',
      title,
      id,
      order_index,
      created_at,
      updated_at
    FROM chapters
    """
  )


async def _create_embedding_project_settings(conn: aiosqlite.Connection) -> None:
  await conn.execute(
    """
    CREATE TABLE IF NOT EXISTS embedding_project_settings (
      project_id TEXT PRIMARY KEY,
      embedding_config_id TEXT,
      segmentation_mode TEXT NOT NULL DEFAULT 'word',
      segment_size INTEGER NOT NULL DEFAULT 1,
      algorithm TEXT NOT NULL DEFAULT 'cosine',
      updated_at TEXT NOT NULL,
      FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
      FOREIGN KEY (embedding_config_id) REFERENCES api_configs(id) ON DELETE SET NULL
    )
    """
  )


async def _create_typewriter_layout_settings(conn: aiosqlite.Connection) -> None:
  await conn.execute(
    """
    CREATE TABLE IF NOT EXISTS typewriter_layout_settings (
      id INTEGER PRIMARY KEY CHECK (id = 1),
      first_line_indent_chars REAL NOT NULL DEFAULT 0,
      font_size_px INTEGER NOT NULL DEFAULT 20,
      paragraph_gap_lines REAL NOT NULL DEFAULT 0,
      line_height_multiplier REAL NOT NULL DEFAULT 2.9,
      updated_at TEXT
    )
    """
  )
  await _add_column_if_missing(
    conn,
    "typewriter_layout_settings",
    "line_height_multiplier",
    "REAL NOT NULL DEFAULT 2.9",
  )
  await _add_column_if_missing(
    conn,
    "typewriter_layout_settings",
    "font_size_px",
    "INTEGER NOT NULL DEFAULT 20",
  )


async def _remove_legacy_default_perspectives(conn: aiosqlite.Connection) -> None:
  migration_id = "remove-legacy-default-perspectives-v1"
  cursor = await conn.execute("SELECT id FROM schema_migrations WHERE id = ?", (migration_id,))
  row = await cursor.fetchone()
  await cursor.close()
  if row is not None:
    return

  await conn.execute(
    """
    DELETE FROM perspectives
    WHERE id IN ('pace-editor', 'character-critic', 'continuity')
    """
  )
  await conn.execute("INSERT INTO schema_migrations (id) VALUES (?)", (migration_id,))
