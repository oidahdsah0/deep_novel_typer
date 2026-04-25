from __future__ import annotations

from app.Schemas.typewriter_layout import TypewriterLayoutSettings
from app.Utils.db import AsyncDatabase, AsyncDBConnection


SETTINGS_ROW_ID = 1


class TypewriterLayoutRepository:
  def __init__(self, db: AsyncDatabase) -> None:
    self._db = db

  async def fetch_settings_row(self) -> dict[str, object] | None:
    return await self._db.fetch_one(
      """
      SELECT
        first_line_indent_chars,
        font_size_px,
        paragraph_gap_lines,
        line_height_multiplier,
        updated_at
      FROM typewriter_layout_settings
      WHERE id = ?
      """,
      (SETTINGS_ROW_ID,),
    )

  async def upsert_settings(
    self,
    conn: AsyncDBConnection,
    *,
    first_line_indent_chars: float,
    font_size_px: int,
    paragraph_gap_lines: float,
    line_height_multiplier: float,
    updated_at: str,
  ) -> None:
    await conn.execute(
      """
      INSERT INTO typewriter_layout_settings (
        id,
        first_line_indent_chars,
        font_size_px,
        paragraph_gap_lines,
        line_height_multiplier,
        updated_at
      )
      VALUES (?, ?, ?, ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET
        first_line_indent_chars = excluded.first_line_indent_chars,
        font_size_px = excluded.font_size_px,
        paragraph_gap_lines = excluded.paragraph_gap_lines,
        line_height_multiplier = excluded.line_height_multiplier,
        updated_at = excluded.updated_at
      """,
      (
        SETTINGS_ROW_ID,
        first_line_indent_chars,
        font_size_px,
        paragraph_gap_lines,
        line_height_multiplier,
        updated_at,
      ),
    )


def settings_from_row(row: dict[str, object]) -> TypewriterLayoutSettings:
  return TypewriterLayoutSettings(
    first_line_indent_chars=float(row["first_line_indent_chars"]),
    font_size_px=int(row["font_size_px"]),
    paragraph_gap_lines=float(row["paragraph_gap_lines"]),
    line_height_multiplier=float(row["line_height_multiplier"]),
    updated_at=str(row["updated_at"]) if row["updated_at"] else None,
  )
