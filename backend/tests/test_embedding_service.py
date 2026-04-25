import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.chapters import UpdateChapterRequest
from app.Schemas.documents import UpdateDocumentRequest
from app.Schemas.embeddings import (
  CreateEmbeddingTagRequest,
  HeatmapRequest,
  UpdateEmbeddingTagRequest,
)
from app.Schemas.projects import CreateProjectRequest
from app.Services.api_configs import APIConfigService
from app.Services.chapter_service import ChapterService
from app.Services.document_service import DocumentService
from app.Services.embeddings import EmbeddingService, segment_text
from app.Services.project_service import ProjectService
from app.Utils.config import _load_llm_settings
from app.Utils.db import AsyncDatabase
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from tests.fakes import FakeEmbeddingRuntime


@pytest.mark.asyncio
async def test_embedding_tag_crud_resets_stale_vector_metadata(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    _document_service,
    embedding_service,
    db,
    _runtime,
    _api_config_service,
  ) = await _build_embedding_services(tmp_path)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    config = await _create_embedding_config(_api_config_service)

    tag = await embedding_service.create_tag(
      project.id,
      CreateEmbeddingTagRequest(
        name="危险",
        description="威胁、失控、死亡风险",
        color="#d94841",
      ),
    )
    assert tag.name == "危险"
    assert tag.is_enabled is True
    assert await embedding_service.list_tags(project.id) == [tag]

    await db.execute(
      """
      UPDATE embedding_tags
      SET embedding_config_id = ?,
          embedding_model_signature = 'old-signature',
          embedding_vector_ref = 'old-vector'
      WHERE project_id = ? AND id = ?
      """,
      (config.id, project.id, tag.id),
    )

    updated = await embedding_service.update_tag(
      project.id,
      tag.id,
      UpdateEmbeddingTagRequest(description="新的危险描述", is_enabled=False),
    )

    assert updated.description == "新的危险描述"
    assert updated.is_enabled is False
    assert updated.embedding_config_id is None
    assert updated.embedding_model_signature is None
    assert updated.embedding_vector_ref is None

    await embedding_service.delete_tag(project.id, tag.id)
    assert await embedding_service.list_tags(project.id) == []
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_embedding_cache_batches_misses_and_reuses_chroma(tmp_path) -> None:
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
    project = await project_service.create_project(CreateProjectRequest(title="Cache Book"))

    first = await embedding_service.cache_text_embeddings(
      project_id=project.id,
      api_config_id=config.id,
      segmentation_mode="word",
      texts=["码头", "海雾", "码头", "  "],
    )
    second = await embedding_service.cache_text_embeddings(
      project_id=project.id,
      api_config_id=config.id,
      segmentation_mode="word",
      texts=["海雾", "新词"],
    )

    assert first.requested_count == 4
    assert first.unique_count == 2
    assert first.cache_hit_count == 0
    assert first.cache_miss_count == 2
    assert second.requested_count == 2
    assert second.unique_count == 2
    assert second.cache_hit_count == 1
    assert second.cache_miss_count == 1
    assert [call[1] for call in runtime.calls] == [["码头", "海雾"], ["新词"]]
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_embedding_cache_separates_model_signatures(tmp_path) -> None:
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
    first_config = await _create_embedding_config(api_config_service, name="Embed One")
    second_config = await _create_embedding_config(
      api_config_service,
      name="Embed Two",
      model="text-embedding-two",
    )
    project = await project_service.create_project(CreateProjectRequest(title="Signature Book"))

    await embedding_service.cache_text_embeddings(
      project_id=project.id,
      api_config_id=first_config.id,
      segmentation_mode="word",
      texts=["同一个词"],
    )
    await embedding_service.cache_text_embeddings(
      project_id=project.id,
      api_config_id=second_config.id,
      segmentation_mode="word",
      texts=["同一个词"],
    )

    assert [call[0].config.id for call in runtime.calls] == [first_config.id, second_config.id]
    assert [call[1] for call in runtime.calls] == [["同一个词"], ["同一个词"]]
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_embedding_heatmap_builds_items_and_persists_run(tmp_path) -> None:
  (
    store,
    project_service,
    chapter_service,
    _document_service,
    embedding_service,
    db,
    runtime,
    api_config_service,
  ) = await _build_embedding_services(tmp_path)
  try:
    config = await _create_embedding_config(api_config_service)
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    danger_tag = await embedding_service.create_tag(
      project.id,
      CreateEmbeddingTagRequest(name="危险", description="威胁和失控"),
    )
    mist_tag = await embedding_service.create_tag(
      project.id,
      CreateEmbeddingTagRequest(name="海雾", description="潮湿、港口、遮蔽"),
    )
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      UpdateChapterRequest(content="码头升起海雾，码头边的人停住。").content,
    )

    response = await embedding_service.build_heatmap(
      project.id,
      HeatmapRequest(
        resource_type="chapter",
        resource_id="chapter-001",
        api_config_id=config.id,
        segmentation_mode="word",
        algorithm="cosine",
      ),
    )

    assert response.status == "success"
    assert response.resource_type == "chapter"
    assert response.token_cache.requested_count == len(response.items)
    assert response.token_cache.unique_count < response.token_cache.requested_count
    assert response.tag_cache.unique_count == 2
    assert {tag.embedding_vector_ref for tag in response.tags}
    tag_ids = {danger_tag.id, mist_tag.id}
    assert all(set(item.scores.keys()) == tag_ids for item in response.items)
    assert all(item.nearest_tag_id in tag_ids for item in response.items)
    assert [call[2] for call in runtime.calls] == [
      "embedding_heatmap_tags",
      "embedding_heatmap_tokens",
    ]

    run = await db.fetch_one(
      """
      SELECT tool_type, status, segmentation_mode, algorithm
      FROM embedding_analysis_runs
      WHERE id = ?
      """,
      (response.run_id,),
    )
    item_rows = await db.fetch_all(
      "SELECT token_index, tag_id FROM embedding_analysis_items WHERE run_id = ?",
      (response.run_id,),
    )
    assert run == {
      "tool_type": "heatmap",
      "status": "success",
      "segmentation_mode": "word",
      "algorithm": "cosine",
    }
    assert len(item_rows) == len(response.items) * len(response.tags)
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_embedding_heatmap_supports_documents_and_ranges(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    document_service,
    embedding_service,
    _db,
    _runtime,
    api_config_service,
  ) = await _build_embedding_services(tmp_path)
  try:
    config = await _create_embedding_config(api_config_service)
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await embedding_service.create_tag(
      project.id,
      CreateEmbeddingTagRequest(name="线索", description="证词、录音、调查"),
    )
    await document_service.update_document(
      project.id,
      "outline",
      UpdateDocumentRequest(content="第一句无关。第二句记录蓝色证词。第三句收束。").content,
    )

    start = len("第一句无关。")
    end = start + len("第二句记录蓝色证词。")
    response = await embedding_service.build_heatmap(
      project.id,
      HeatmapRequest(
        resource_type="document",
        resource_id="outline",
        api_config_id=config.id,
        segmentation_mode="sentence",
        algorithm="euclidean",
        range={"start_offset": start, "end_offset": end},
      ),
    )

    assert response.resource_type == "document"
    assert response.algorithm == "euclidean"
    assert [item.text for item in response.items] == ["第二句记录蓝色证词。"]
    assert response.items[0].start_offset == start
    assert response.items[0].end_offset == end
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_embedding_heatmap_algorithm_switch_reuses_cached_vectors(tmp_path) -> None:
  (
    store,
    project_service,
    chapter_service,
    _document_service,
    embedding_service,
    _db,
    runtime,
    api_config_service,
  ) = await _build_embedding_services(tmp_path)
  try:
    config = await _create_embedding_config(api_config_service)
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await embedding_service.create_tag(
      project.id,
      CreateEmbeddingTagRequest(name="海雾", description="潮湿和港口"),
    )
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      UpdateChapterRequest(content="码头升起海雾，码头边的人停住。").content,
    )

    first = await embedding_service.build_heatmap(
      project.id,
      HeatmapRequest(
        resource_type="chapter",
        resource_id="chapter-001",
        api_config_id=config.id,
        algorithm="cosine",
      ),
    )
    call_count = len(runtime.calls)
    second = await embedding_service.build_heatmap(
      project.id,
      HeatmapRequest(
        resource_type="chapter",
        resource_id="chapter-001",
        api_config_id=config.id,
        algorithm="manhattan",
      ),
    )

    assert first.algorithm == "cosine"
    assert second.algorithm == "manhattan"
    assert len(runtime.calls) == call_count
    assert second.tag_cache.cache_hit_count == 1
    assert second.token_cache.cache_miss_count == 0
    assert all(
      score.raw_distance is not None and score.raw_score is None
      for item in second.items
      for score in item.scores.values()
    )
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_embedding_heatmap_empty_text_returns_warning(tmp_path) -> None:
  (
    store,
    project_service,
    chapter_service,
    _document_service,
    embedding_service,
    db,
    runtime,
    api_config_service,
  ) = await _build_embedding_services(tmp_path)
  try:
    config = await _create_embedding_config(api_config_service)
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await embedding_service.create_tag(
      project.id,
      CreateEmbeddingTagRequest(name="危险", description="威胁和失控"),
    )
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      UpdateChapterRequest(content="   \n  ").content,
    )

    response = await embedding_service.build_heatmap(
      project.id,
      HeatmapRequest(
        resource_type="chapter",
        resource_id="chapter-001",
        api_config_id=config.id,
      ),
    )

    item_rows = await db.fetch_all(
      "SELECT token_index FROM embedding_analysis_items WHERE run_id = ?",
      (response.run_id,),
    )
    assert response.items == []
    assert response.token_cache.requested_count == 0
    assert response.token_cache.cache_miss_count == 0
    assert response.warnings == ["分析范围内没有可用于 Embedding 的分词。"]
    assert [call[2] for call in runtime.calls] == ["embedding_heatmap_tags"]
    assert item_rows == []
  finally:
    await store.shutdown()


def test_embedding_segmentation_offsets_round_trip() -> None:
  text = "林澈在旧码头找到蓝色证词，潮水把海雾推上岸。第二句来了！"
  word_segments = segment_text(text, "word")
  paired_word_segments = segment_text(text, "word", segment_size=2)
  sentence_segments = segment_text(text, "sentence")
  paired_sentence_segments = segment_text(text, "sentence", segment_size=2)

  assert [segment.text for segment in word_segments[:4]] == ["林澈", "在", "旧", "码头"]
  assert [segment.text for segment in paired_word_segments[:2]] == ["林澈在", "旧码头"]
  assert all(
    text[segment.start_offset : segment.end_offset] == segment.text
    for segment in [*word_segments, *paired_word_segments, *paired_sentence_segments]
  )
  assert [segment.text for segment in sentence_segments] == [
    "林澈在旧码头找到蓝色证词，潮水把海雾推上岸。",
    "第二句来了！",
  ]
  assert [segment.text for segment in paired_sentence_segments] == [text]


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


async def _create_embedding_config(
  api_config_service: APIConfigService,
  *,
  name: str = "Embedding Config",
  model: str = "text-embedding-test",
):
  return await api_config_service.create_config(
    CreateAPIConfigRequest(
      name=name,
      provider="siliconflow",
      kind="embedding",
      api_key="embedding-secret",
      api_key_required=True,
      base_url="https://api.siliconflow.cn/v1",
      mode="non_stream",
      model=model,
      thinking_enabled=False,
      max_tokens=1024,
      temperature=None,
      top_p=None,
      top_k=None,
      dimensions=4096,
    )
  )
