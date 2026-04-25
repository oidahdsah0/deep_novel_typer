from __future__ import annotations

from pathlib import Path

from app.Services.chapters.repository import ChapterRepository
from app.Utils.errors import EntityNotFoundError
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Utils.text import count_words
from app.Schemas.chapters import ChapterDetail


class ChapterContent:
  def __init__(
    self,
    store: AsyncFileStore,
    paths: PathResolver,
    repository: ChapterRepository,
  ) -> None:
    self._store = store
    self._paths = paths
    self._repository = repository

  async def prepare_write(self, project_id: str, file_path: str, content: str) -> Path:
    return await self._store.write_text_temp(
      self._content_path(project_id, file_path), content
    )

  async def commit_prepared_write(
    self, project_id: str, file_path: str, tmp_path: Path
  ) -> None:
    await self._store.commit_text_temp(tmp_path, self._content_path(project_id, file_path))

  async def discard_prepared_write(self, tmp_path: Path) -> None:
    await self._store.discard_file(tmp_path)

  async def read(self, project_id: str, chapter_id: str) -> str:
    row = await self._repository.chapter_row(project_id, chapter_id)
    content_path = self._content_path(project_id, str(row["file_path"]))
    if not await self._store.exists(content_path):
      raise EntityNotFoundError(f"Chapter file not found: {chapter_id}")
    return await self._store.read_text(content_path)

  async def detail(self, project_id: str, chapter_id: str) -> ChapterDetail:
    row = await self._repository.chapter_row(project_id, chapter_id)
    content_path = self._content_path(project_id, str(row["file_path"]))
    if not await self._store.exists(content_path):
      raise EntityNotFoundError(f"Chapter file not found: {chapter_id}")

    content = await self._store.read_text(content_path)
    return ChapterDetail(
      id=str(row["id"]),
      title=str(row["title"]),
      order=int(row["order_index"]),
      content=content,
      word_count=count_words(content),
      writing_synopsis=str(row["writing_synopsis"] or ""),
      writing_synopsis_updated_at=str(
        row["writing_synopsis_updated_at"] or row["updated_at"]
      ),
      updated_at=str(row["updated_at"]),
    )

  def _content_path(self, project_id: str, file_path: str) -> Path:
    return self._paths.project(project_id).root / file_path
