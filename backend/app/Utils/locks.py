from __future__ import annotations

import asyncio
import threading


class AsyncLockRegistry:
  def __init__(self) -> None:
    self._guard = threading.Lock()
    self._locks: dict[str, asyncio.Lock] = {}

  def get(self, key: str) -> asyncio.Lock:
    with self._guard:
      if key not in self._locks:
        self._locks[key] = asyncio.Lock()
      return self._locks[key]
