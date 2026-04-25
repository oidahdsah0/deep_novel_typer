from __future__ import annotations

from pathlib import Path

from app.Utils.storage import AsyncFileStore


async def cleanup_import_target(store: AsyncFileStore, target_root: Path) -> None:
  if await store.exists(target_root):
    await store.remove_tree(target_root)
