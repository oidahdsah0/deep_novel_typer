from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Protocol

import aiosqlite

from app.Utils.db_migrations import _run_migrations
from app.Utils.db_schema import _SCHEMA


class AsyncDBConnection(Protocol):
  async def execute(self, query: str, params: Sequence[Any] = ()) -> Any:
    ...

  async def executemany(self, query: str, params: Sequence[Sequence[Any]]) -> Any:
    ...

  async def executescript(self, script: str) -> Any:
    ...

  async def commit(self) -> None:
    ...

  async def rollback(self) -> None:
    ...


class AsyncDatabase:
  def __init__(self, path: Path) -> None:
    self.path = path
    self._write_lock = asyncio.Lock()

  async def initialize(self) -> None:
    self.path.parent.mkdir(parents=True, exist_ok=True)
    async with self._connect() as conn:
      await conn.execute("PRAGMA journal_mode=WAL")
      await conn.execute("PRAGMA foreign_keys=ON")
      await conn.executescript(_SCHEMA)
      await _run_migrations(conn)
      await conn.commit()

  async def fetch_one(self, query: str, params: Sequence[Any] = ()) -> dict[str, Any] | None:
    async with self._connect() as conn:
      cursor = await conn.execute(query, params)
      row = await cursor.fetchone()
      await cursor.close()
      return dict(row) if row else None

  async def fetch_all(self, query: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    async with self._connect() as conn:
      cursor = await conn.execute(query, params)
      rows = await cursor.fetchall()
      await cursor.close()
      return [dict(row) for row in rows]

  async def execute(self, query: str, params: Sequence[Any] = ()) -> None:
    async with self.transaction() as conn:
      await conn.execute(query, params)

  @asynccontextmanager
  async def transaction(self) -> AsyncIterator[AsyncDBConnection]:
    async with self._write_lock:
      async with self._connect() as conn:
        await conn.execute("BEGIN")
        try:
          yield conn
        except Exception:
          await conn.rollback()
          raise
        else:
          await conn.commit()

  @asynccontextmanager
  async def _connect(self) -> AsyncIterator[aiosqlite.Connection]:
    conn = await aiosqlite.connect(self.path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys=ON")
    try:
      yield conn
    finally:
      await conn.close()
