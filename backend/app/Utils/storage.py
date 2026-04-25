from __future__ import annotations

import asyncio
import json
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any
from uuid import uuid4


class AsyncFileStore:
  def __init__(self, root: Path, max_workers: int) -> None:
    self.root = root
    self.root.mkdir(parents=True, exist_ok=True)
    self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="novel-io")

  async def exists(self, path: Path) -> bool:
    return await self._run(path.exists)

  async def ensure_dir(self, path: Path) -> None:
    await self._run(path.mkdir, parents=True, exist_ok=True)

  async def list_dirs(self, path: Path) -> list[Path]:
    def _list() -> list[Path]:
      if not path.exists():
        return []
      return sorted([item for item in path.iterdir() if item.is_dir()])

    return await self._run(_list)

  async def list_files(self, path: Path, pattern: str = "*") -> list[Path]:
    def _list() -> list[Path]:
      if not path.exists():
        return []
      return sorted([item for item in path.glob(pattern) if item.is_file()])

    return await self._run(_list)

  async def read_text(self, path: Path) -> str:
    return await self._run(path.read_text, encoding="utf-8")

  async def write_text(self, path: Path, content: str) -> None:
    await self.ensure_dir(path.parent)
    await self._run(_atomic_write_text, path, content)

  async def write_text_temp(self, path: Path, content: str) -> Path:
    await self.ensure_dir(path.parent)
    return await self._run(_write_text_temp, path, content)

  async def commit_text_temp(self, tmp_path: Path, target_path: Path) -> None:
    await self.ensure_dir(target_path.parent)
    await self._run(os.replace, tmp_path, target_path)

  async def discard_file(self, path: Path) -> None:
    await self._run(_discard_file, path)

  async def read_json(self, path: Path) -> dict[str, Any]:
    content = await self.read_text(path)
    return json.loads(content)

  async def write_json(self, path: Path, payload: dict[str, Any]) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    await self.write_text(path, content)

  async def move_path(self, source: Path, target: Path) -> None:
    await self.ensure_dir(target.parent)
    await self._run(shutil.move, str(source), str(target))

  async def move_dir(self, source: Path, target: Path) -> None:
    await self.move_path(source, target)

  async def remove_tree(self, path: Path) -> None:
    await self._run(shutil.rmtree, path, ignore_errors=True)

  async def shutdown(self) -> None:
    self._executor.shutdown(wait=True, cancel_futures=False)

  async def _run(self, func: Any, *args: Any, **kwargs: Any) -> Any:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(self._executor, partial(func, *args, **kwargs))


def _atomic_write_text(path: Path, content: str) -> None:
  tmp_path = path.with_suffix(f"{path.suffix}.tmp")
  tmp_path.write_text(content, encoding="utf-8")
  os.replace(tmp_path, path)


def _write_text_temp(path: Path, content: str) -> Path:
  tmp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
  tmp_path.write_text(content, encoding="utf-8")
  return tmp_path


def _discard_file(path: Path) -> None:
  try:
    path.unlink()
  except FileNotFoundError:
    return
