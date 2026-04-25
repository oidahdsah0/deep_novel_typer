from __future__ import annotations

import pytest

from app.Services.api_configs import APIConfigService
from app.Services.chapter_service import ChapterService
from app.Services.document_service import DocumentService
from app.Services.generation_service import GenerationService
from app.Services.prompt_profiles import PromptProfileService
from app.Services.project_service import ProjectService
from app.Services.search import ProjectSearchService
from app.Services.version_service import VersionService
from app.Utils.config import _load_llm_settings
from app.Utils.db import AsyncDatabase
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from app.Schemas.chapters import CreateChapterNodeRequest
from app.Schemas.documents import CreateDocumentNodeRequest
from app.Schemas.generation import CreateGenerationPresetRequest
from app.Schemas.projects import CreateProjectRequest
from app.Schemas.prompt_profiles import UpdatePromptProfileRequest
from tests.fakes import FakeLLMClient, GENERATION_DEFAULTS


@pytest.mark.asyncio
async def test_project_search_finds_all_project_resource_types(tmp_path) -> None:
  stack = await _build_search_stack(tmp_path)
  try:
    project = await stack.project_service.create_project(
      CreateProjectRequest(title="Search Book")
    )
    folder = await stack.chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(type="folder", title="第一卷"),
    )
    chapter = await stack.chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(
        type="chapter",
        title="港口证词",
        parent_id=folder.id,
        content="林澈在旧码头找到蓝色证词。",
      ),
    )
    document = await stack.document_service.create_node(
      project.id,
      CreateDocumentNodeRequest(
        type="markdown",
        title="调查资料",
        content="# 调查资料\n\n蓝色证词来自港口仓库。",
      ),
    )
    await stack.prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(
        name="蓝色证词续写模板",
        system_template="系统需要追踪蓝色证词。",
        user_template="用户提示蓝色证词。",
      ),
    )
    await stack.generation_service.create_preset(
      project.id,
      CreateGenerationPresetRequest(
        kind="writing_mode",
        name="蓝色证词写作法",
        content="围绕蓝色证词推进。",
      ),
    )
    await stack.version_service.create_current_version(
      project.id,
      "document",
      document.id,
      label="蓝色证词资料版本",
      note="版本说明含蓝色证词。",
    )

    response = await stack.search_service.search_project(project.id, "蓝色证词")
    resource_types = {result.resource_type for result in response.results}

    assert "chapter" in resource_types
    assert "document" in resource_types
    assert "prompt_profile" in resource_types
    assert "prompt_profile_version" in resource_types
    assert "generation_preset" in resource_types
    assert "resource_version" in resource_types
    assert any(result.path == ["第一卷"] for result in response.results)
    assert any(result.resource_id == chapter.chapter_id for result in response.results)

    document_response = await stack.search_service.search_project(
      project.id,
      "仓库",
      scope="documents",
    )
    assert [result.resource_type for result in document_response.results] == ["document"]
  finally:
    await stack.store.shutdown()


@pytest.mark.asyncio
async def test_project_search_updates_and_cleans_deleted_resources(tmp_path) -> None:
  stack = await _build_search_stack(tmp_path)
  try:
    project = await stack.project_service.create_project(
      CreateProjectRequest(title="Search Book")
    )
    chapter = await stack.chapter_service.create_node(
      project.id,
      CreateChapterNodeRequest(
        type="chapter",
        title="临时线索",
        content="旧词只会出现一次。",
      ),
    )
    await stack.search_service.search_project(project.id, "旧词")

    await stack.chapter_service.update_chapter(project.id, chapter.chapter_id or "", "新词已经替换旧线索。")
    updated = await stack.search_service.search_project(project.id, "新词")
    removed = await stack.search_service.search_project(project.id, "旧词只会")

    assert updated.results[0].resource_type == "chapter"
    assert removed.results == []

    await stack.chapter_service.delete_node(project.id, chapter.id)
    deleted = await stack.search_service.search_project(project.id, "新词")
    assert deleted.results == []
  finally:
    await stack.store.shutdown()


class _SearchStack:
  def __init__(
    self,
    db: AsyncDatabase,
    store: AsyncFileStore,
    project_service: ProjectService,
    chapter_service: ChapterService,
    document_service: DocumentService,
    prompt_profile_service: PromptProfileService,
    generation_service: GenerationService,
    version_service: VersionService,
    search_service: ProjectSearchService,
  ) -> None:
    self.db = db
    self.store = store
    self.project_service = project_service
    self.chapter_service = chapter_service
    self.document_service = document_service
    self.prompt_profile_service = prompt_profile_service
    self.generation_service = generation_service
    self.version_service = version_service
    self.search_service = search_service


async def _build_search_stack(tmp_path) -> _SearchStack:
  projects_dir = tmp_path / "projects"
  trash_dir = tmp_path / "trash"
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  store = AsyncFileStore(projects_dir, max_workers=2)
  paths = PathResolver(projects_dir, trash_dir)
  locks = AsyncLockRegistry()
  project_service = ProjectService(db, store, paths, locks)
  chapter_service = ChapterService(db, store, paths, locks, project_service)
  document_service = DocumentService(db, store, paths, locks, project_service)
  prompt_profile_service = PromptProfileService(
    db,
    locks,
    project_service,
    chapter_service,
    document_service,
  )
  api_config_service = APIConfigService(db, locks, _load_llm_settings())
  await api_config_service.ensure_default_config()
  generation_service = GenerationService(
    db,
    locks,
    project_service,
    chapter_service,
    document_service,
    prompt_profile_service,
    api_config_service,
    FakeLLMClient('{"text": ""}'),
    GENERATION_DEFAULTS,
  )
  version_service = VersionService(
    db,
    store,
    paths,
    locks,
    project_service,
    chapter_service,
    document_service,
  )
  search_service = ProjectSearchService(
    db,
    store,
    paths,
    project_service,
    GENERATION_DEFAULTS,
  )
  return _SearchStack(
    db,
    store,
    project_service,
    chapter_service,
    document_service,
    prompt_profile_service,
    generation_service,
    version_service,
    search_service,
  )
