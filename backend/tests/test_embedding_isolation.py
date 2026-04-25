import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.embeddings import UpdateEmbeddingProjectSettingsRequest
from app.Schemas.projects import CreateProjectRequest
from app.Services.api_configs import APIConfigService
from app.Services.chapter_service import ChapterService
from app.Services.document_service import DocumentService
from app.Services.embeddings import EmbeddingService
from app.Services.project_service import ProjectService
from app.Utils.config import _load_llm_settings
from app.Utils.db import AsyncDatabase
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from tests.fakes import FakeEmbeddingRuntime


@pytest.mark.asyncio
async def test_embedding_cache_isolated_by_project(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    _document_service,
    embedding_service,
    _db,
    runtime,
    api_config_service,
  ) = await _build_embedding_services(tmp_path)
  try:
    config = await _create_embedding_config(api_config_service)
    first_project = await project_service.create_project(CreateProjectRequest(title="Book One"))
    second_project = await project_service.create_project(CreateProjectRequest(title="Book Two"))

    await embedding_service.cache_text_embeddings(
      project_id=first_project.id,
      api_config_id=config.id,
      segmentation_mode="word",
      texts=["同一个词"],
    )
    await embedding_service.cache_text_embeddings(
      project_id=second_project.id,
      api_config_id=config.id,
      segmentation_mode="word",
      texts=["同一个词"],
    )
    again = await embedding_service.cache_text_embeddings(
      project_id=first_project.id,
      api_config_id=config.id,
      segmentation_mode="word",
      texts=["同一个词"],
    )

    assert [call[1] for call in runtime.calls] == [["同一个词"], ["同一个词"]]
    assert again.cache_hit_count == 1
    assert again.cache_miss_count == 0
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_embedding_project_settings_are_isolated(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    _document_service,
    embedding_service,
    _db,
    _runtime,
    api_config_service,
  ) = await _build_embedding_services(tmp_path)
  try:
    config = await _create_embedding_config(api_config_service)
    first_project = await project_service.create_project(CreateProjectRequest(title="Book One"))
    second_project = await project_service.create_project(CreateProjectRequest(title="Book Two"))

    saved = await embedding_service.update_settings(
      first_project.id,
      UpdateEmbeddingProjectSettingsRequest(
        api_config_id=config.id,
        segmentation_mode="sentence",
        segment_size=3,
        algorithm="manhattan",
      ),
    )

    first_settings = await embedding_service.get_settings(first_project.id)
    second_settings = await embedding_service.get_settings(second_project.id)
    assert saved.api_config_id == config.id
    assert first_settings.api_config_id == config.id
    assert first_settings.segmentation_mode == "sentence"
    assert first_settings.segment_size == 3
    assert first_settings.algorithm == "manhattan"
    assert second_settings.api_config_id is None
    assert second_settings.segmentation_mode == "word"
    assert second_settings.segment_size == 1
    assert second_settings.algorithm == "cosine"
  finally:
    await store.shutdown()


async def _build_embedding_services(tmp_path):
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
  api_config_service = APIConfigService(db, locks, _load_llm_settings())
  runtime = FakeEmbeddingRuntime()
  embedding_service = EmbeddingService(
    db,
    locks,
    project_service,
    chapter_service,
    document_service,
    api_config_service,
    runtime,
    chroma_path=tmp_path / "chroma",
  )
  return (
    store,
    project_service,
    chapter_service,
    document_service,
    embedding_service,
    db,
    runtime,
    api_config_service,
  )


async def _create_embedding_config(api_config_service: APIConfigService):
  return await api_config_service.create_config(
    CreateAPIConfigRequest(
      name="Embedding Config",
      provider="siliconflow",
      kind="embedding",
      api_key="embedding-secret",
      api_key_required=True,
      base_url="https://api.siliconflow.cn/v1",
      mode="non_stream",
      model="text-embedding-test",
      thinking_enabled=False,
      max_tokens=1024,
      temperature=None,
      top_p=None,
      top_k=None,
      dimensions=4096,
    )
  )
