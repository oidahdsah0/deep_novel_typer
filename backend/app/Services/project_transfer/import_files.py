from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from app.Services.project_transfer.archive import ProjectArchivePayload, safe_relative_path
from app.Utils.errors import DomainError
from app.Utils.storage import AsyncFileStore
from app.Utils.text import count_words


async def write_content_files(
  store: AsyncFileStore,
  target_root: Path,
  content_files: dict[str, bytes],
) -> None:
  for relative_path, raw in content_files.items():
    path = target_root / safe_relative_path(relative_path)
    try:
      content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
      raise DomainError(
        f"Project import archive content is not UTF-8: {relative_path}"
      ) from exc
    await store.write_text(path, content)


def content_text(payload: ProjectArchivePayload, relative_path: str) -> str:
  raw = payload.content_files.get(relative_path)
  if raw is None:
    raise DomainError(f"Project import archive is missing content file: {relative_path}")
  return raw.decode("utf-8")


def chapter_word_count(payload: ProjectArchivePayload, row: dict[str, object]) -> int:
  return count_words(content_text(payload, safe_relative_path(row["file_path"])))


def sha256_text(content: str) -> str:
  return sha256(content.encode("utf-8")).hexdigest()
