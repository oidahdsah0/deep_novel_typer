import asyncio

import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
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
async def test_embedding_cache_single_flight_reuses_concurrent_miss(tmp_path) -> None:
  runtime = SlowFakeEmbeddingRuntime()
  (
    store,
    project_service,
    embedding_service,
    api_config_service,
  ) = await _build_embedding_services(tmp_path, runtime)
  try:
    config = await _create_embedding_config(api_config_service)
    project = await project_service.create_project(CreateProjectRequest(title="Race Book"))

    await asyncio.gather(
      embedding_service.cache_text_embeddings(
        project_id=project.id,
        api_config_id=config.id,
        segmentation_mode="word",
        texts=["码头", "海雾"],
      ),
      embedding_service.cache_text_embeddings(
        project_id=project.id,
        api_config_id=config.id,
        segmentation_mode="word",
        texts=["码头", "海雾"],
      ),
    )

    assert [call[1] for call in runtime.calls] == [["码头", "海雾"]]
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_embedding_cache_single_flight_allows_partial_overlap(tmp_path) -> None:
  runtime = SlowFakeEmbeddingRuntime()
  (
    store,
    project_service,
    embedding_service,
    api_config_service,
  ) = await _build_embedding_services(tmp_path, runtime)
  try:
    config = await _create_embedding_config(api_config_service)
    project = await project_service.create_project(CreateProjectRequest(title="Overlap Book"))

    await asyncio.gather(
      embedding_service.cache_text_embeddings(
        project_id=project.id,
        api_config_id=config.id,
        segmentation_mode="word",
        texts=["码头", "海雾"],
      ),
      embedding_service.cache_text_embeddings(
        project_id=project.id,
        api_config_id=config.id,
        segmentation_mode="word",
        texts=["海雾", "钟声"],
      ),
    )

    embedded_texts = [text for _config, texts, _label in runtime.calls for text in texts]
    assert sorted(embedded_texts) == ["海雾", "码头", "钟声"]
    assert embedded_texts.count("海雾") == 1
  finally:
    await store.shutdown()


class SlowFakeEmbeddingRuntime(FakeEmbeddingRuntime):
  async def embed_texts(self, effective_config, texts, *, label="embedding_batch"):
    await asyncio.sleep(0.05)
    return await super().embed_texts(effective_config, texts, label=label)


async def _build_embedding_services(tmp_path, runtime):
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
  return store, project_service, embedding_service, api_config_service


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
