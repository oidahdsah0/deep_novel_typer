from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.Schemas.chapters import ChapterSummary
from app.Schemas.documents import WorkspaceDocument
from app.Schemas.projects import CreateProjectRequest, ProjectDetail
from app.Services.projects.repository import ProjectRepository
from app.Utils.errors import EntityConflictError
from app.Utils.ids import slugify
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver, ProjectPaths
from app.Utils.storage import AsyncFileStore


class ProjectLifecycle:
  def __init__(
    self,
    repository: ProjectRepository,
    store: AsyncFileStore,
    paths: PathResolver,
    locks: AsyncLockRegistry,
  ) -> None:
    self._repository = repository
    self._store = store
    self._paths = paths
    self._locks = locks

  async def bootstrap(self) -> None:
    await self.import_legacy_projects()

  async def import_legacy_projects(self) -> None:
    for project_dir in await self._store.list_dirs(self._paths.data_dir):
      manifest_path = project_dir / "manifest.json"
      if not await self._store.exists(manifest_path):
        continue

      payload = await self._store.read_json(manifest_path)
      project_id = str(payload["id"])
      if await self._repository.project_exists(project_id):
        continue

      now = payload.get("updated_at") or _now()
      chapters = [
        ChapterSummary.model_validate(chapter)
        for chapter in payload.get("chapters", [])
      ]
      documents = [
        WorkspaceDocument.model_validate(document)
        for document in payload.get("documents", [])
      ]
      detail = ProjectDetail(
        id=project_id,
        title=payload.get("title", project_id),
        subtitle=payload.get("subtitle", ""),
        description=payload.get("description", ""),
        genre=payload.get("genre", ""),
        status=payload.get("status", "drafting"),
        created_at=payload.get("created_at", now),
        updated_at=now,
        last_opened_at=payload.get("last_opened_at"),
        chapters=chapters,
        documents=documents,
        chapter_count=len(chapters),
        word_count=sum(chapter.word_count for chapter in chapters),
      )
      perspectives = await self._read_legacy_perspectives(project_dir / "perspectives", now)
      await self._repository.insert_project(detail, project_dir, perspectives)

  async def create_project(self, request: CreateProjectRequest) -> ProjectDetail:
    base_id = slugify(request.title, fallback_prefix="book")
    project_id = await self._next_project_id(base_id)

    async with self._locks.get(project_id):
      if await self._repository.project_exists(project_id):
        raise EntityConflictError(f"Project already exists: {project_id}")

      now = _now()
      detail = ProjectDetail(
        id=project_id,
        title=request.title,
        subtitle=request.subtitle,
        description=request.description,
        genre=request.genre,
        status=request.status,
        created_at=now,
        updated_at=now,
        chapter_count=1,
        word_count=0,
        chapters=[ChapterSummary(id="chapter-001", title="第一章", order=1, word_count=0)],
        documents=[
          WorkspaceDocument(kind="outline", title="基本蓝图", updated_at=now),
        ],
      )
      paths = self._paths.project(project_id)
      await self._write_project_defaults(paths, detail, first_chapter_content="")
      await self._repository.insert_project(detail, paths.root, perspectives=[])
      return await self._repository.get_manifest(project_id)

  async def _next_project_id(self, base_id: str) -> str:
    if not await self._repository.project_exists(base_id) and not await self._store.exists(
      self._paths.project(base_id).root
    ):
      return base_id

    suffix = 2
    while True:
      candidate = f"{base_id}-{suffix}"
      if not await self._repository.project_exists(candidate) and not await self._store.exists(
        self._paths.project(candidate).root
      ):
        return candidate
      suffix += 1

  async def _write_project_defaults(
    self, paths: ProjectPaths, detail: ProjectDetail, first_chapter_content: str
  ) -> None:
    await self._store.ensure_dir(paths.chapters_dir)
    await self._store.ensure_dir(paths.docs_dir)
    await self._store.ensure_dir(paths.perspectives_dir)
    await self._store.ensure_dir(paths.versions_dir)

    for index, chapter in enumerate(detail.chapters):
      chapter_path = paths.chapters_dir / f"{chapter.id}.md"
      if not await self._store.exists(chapter_path):
        await self._store.write_text(
          chapter_path, first_chapter_content if index == 0 else ""
        )

    await self._write_default_docs(paths.docs_dir)
    await self._store.write_json(paths.manifest, detail.model_dump(mode="json"))

  async def _write_default_docs(self, docs_dir: Path) -> None:
    docs = {
      "outline.md": (
        "# 基本蓝图\n\n"
        "## 核心概念\n\n"
        "## 主线方向\n\n"
        "## 角色与关系\n\n"
        "## 世界设定\n\n"
        "## 待补充\n"
      ),
    }
    for filename, content in docs.items():
      path = docs_dir / filename
      if not await self._store.exists(path):
        await self._store.write_text(path, content)

  async def _read_legacy_perspectives(
    self, perspectives_dir: Path, now: str
  ) -> list[dict[str, object]]:
    perspectives: list[dict[str, object]] = []
    for path in await self._store.list_files(perspectives_dir, "*.json"):
      item = await self._store.read_json(path)
      item.setdefault("created_at", now)
      item.setdefault("updated_at", now)
      perspectives.append(item)
    return perspectives


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()
