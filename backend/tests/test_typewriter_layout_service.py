import aiosqlite
import pytest

from app.Schemas.typewriter_layout import UpdateTypewriterLayoutSettingsRequest
from app.Services.typewriter_layout import TypewriterLayoutService
from app.Utils.db import AsyncDatabase
from app.Utils.locks import AsyncLockRegistry


@pytest.mark.asyncio
async def test_typewriter_layout_settings_are_global_singleton(tmp_path) -> None:
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  service = TypewriterLayoutService(db, AsyncLockRegistry())

  defaults = await service.get_settings()
  assert defaults.first_line_indent_chars == 0
  assert defaults.font_size_px == 20
  assert defaults.paragraph_gap_lines == 0
  assert defaults.line_height_multiplier == 2.9
  assert defaults.updated_at is None

  updated = await service.update_settings(
    UpdateTypewriterLayoutSettingsRequest(
      first_line_indent_chars=2.5,
      font_size_px=24,
      paragraph_gap_lines=1.2,
      line_height_multiplier=1.8,
    )
  )

  assert updated.first_line_indent_chars == 2.5
  assert updated.font_size_px == 24
  assert updated.paragraph_gap_lines == 1.2
  assert updated.line_height_multiplier == 1.8
  assert updated.updated_at is not None

  restored = await service.update_settings(
    UpdateTypewriterLayoutSettingsRequest(
      first_line_indent_chars=0,
      font_size_px=20,
      paragraph_gap_lines=0,
      line_height_multiplier=2.9,
    )
  )
  rows = await db.fetch_all("SELECT id FROM typewriter_layout_settings")

  assert restored.first_line_indent_chars == 0
  assert restored.font_size_px == 20
  assert restored.paragraph_gap_lines == 0
  assert restored.line_height_multiplier == 2.9
  assert rows == [{"id": 1}]


@pytest.mark.asyncio
async def test_typewriter_layout_migration_adds_newer_columns_to_existing_table(tmp_path) -> None:
  db_path = tmp_path / "novel.db"
  async with aiosqlite.connect(db_path) as conn:
    await conn.execute(
      """
      CREATE TABLE typewriter_layout_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        first_line_indent_chars REAL NOT NULL DEFAULT 0,
        paragraph_gap_lines REAL NOT NULL DEFAULT 0,
        updated_at TEXT
      )
      """
    )
    await conn.execute(
      """
      INSERT INTO typewriter_layout_settings (
        id, first_line_indent_chars, paragraph_gap_lines, updated_at
      )
      VALUES (1, 2.5, 1.2, '2026-01-01T00:00:00+00:00')
      """
    )
    await conn.commit()

  db = AsyncDatabase(db_path)
  await db.initialize()
  service = TypewriterLayoutService(db, AsyncLockRegistry())

  settings = await service.get_settings()

  assert settings.first_line_indent_chars == 2.5
  assert settings.font_size_px == 20
  assert settings.paragraph_gap_lines == 1.2
  assert settings.line_height_multiplier == 2.9
