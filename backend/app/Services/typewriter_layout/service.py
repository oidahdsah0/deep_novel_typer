from __future__ import annotations

from datetime import UTC, datetime

from app.Schemas.typewriter_layout import (
  TypewriterLayoutSettings,
  UpdateTypewriterLayoutSettingsRequest,
)
from app.Services.typewriter_layout.repository import (
  TypewriterLayoutRepository,
  settings_from_row,
)
from app.Utils.db import AsyncDatabase
from app.Utils.locks import AsyncLockRegistry


class TypewriterLayoutService:
  def __init__(self, db: AsyncDatabase, locks: AsyncLockRegistry) -> None:
    self._db = db
    self._locks = locks
    self._repository = TypewriterLayoutRepository(db)

  async def get_settings(self) -> TypewriterLayoutSettings:
    row = await self._repository.fetch_settings_row()
    if row is None:
      return TypewriterLayoutSettings()
    return settings_from_row(row)

  async def update_settings(
    self,
    request: UpdateTypewriterLayoutSettingsRequest,
  ) -> TypewriterLayoutSettings:
    now = _now()
    async with self._locks.get("typewriter-layout-settings"):
      async with self._db.transaction() as conn:
        await self._repository.upsert_settings(
          conn,
          first_line_indent_chars=request.first_line_indent_chars,
          font_size_px=request.font_size_px,
          paragraph_gap_lines=request.paragraph_gap_lines,
          line_height_multiplier=request.line_height_multiplier,
          updated_at=now,
        )
    return await self.get_settings()


def _now() -> str:
  return datetime.now(tz=UTC).replace(microsecond=0).isoformat()
