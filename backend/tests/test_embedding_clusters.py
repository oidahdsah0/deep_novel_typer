import pytest

from app.Schemas.chapters import UpdateChapterRequest
from app.Schemas.documents import UpdateDocumentRequest
from app.Schemas.embeddings import ClusterRequest, CreateEmbeddingTagRequest
from app.Schemas.projects import CreateProjectRequest
from tests.test_embedding_service import _build_embedding_services, _create_embedding_config


@pytest.mark.asyncio
async def test_embedding_clusters_assigns_points_and_persists_run(tmp_path) -> None:
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
    danger = await embedding_service.create_tag(
      project.id,
      CreateEmbeddingTagRequest(name="危险", description="威胁、失控、追逐"),
    )
    clue = await embedding_service.create_tag(
      project.id,
      CreateEmbeddingTagRequest(name="线索", description="证词、录音、调查"),
    )
    content = "码头升起海雾，蓝色证词留在门缝里。"
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      UpdateChapterRequest(content=content).content,
    )

    response = await embedding_service.build_clusters(
      project.id,
      ClusterRequest(
        resource_type="chapter",
        resource_id="chapter-001",
        api_config_id=config.id,
        segmentation_mode="word",
      ),
    )

    assert response.status == "success"
    assert response.cluster_mode == "fixed_tag_centers"
    assert response.projection == "pca"
    assert len(response.tag_anchors) == 2
    assert {cluster.tag_id for cluster in response.clusters} == {danger.id, clue.id}
    assert sum(cluster.point_count for cluster in response.clusters) == len(response.points)
    assert all(content[point.start_offset : point.end_offset] == point.text for point in response.points)
    assert all(point.cluster_id == point.tag_id for point in response.points)
    assert all(-1.0 <= point.x <= 1.0 and -1.0 <= point.y <= 1.0 for point in response.points)
    assert [call[2] for call in runtime.calls] == [
      "embedding_clusters_tags",
      "embedding_clusters_tokens",
    ]

    run = await db.fetch_one(
      """
      SELECT tool_type, status, segmentation_mode, algorithm, params_json
      FROM embedding_analysis_runs
      WHERE id = ?
      """,
      (response.run_id,),
    )
    item_rows = await db.fetch_all(
      """
      SELECT token_index, tag_id, cluster_id, x, y
      FROM embedding_analysis_items
      WHERE run_id = ?
      """,
      (response.run_id,),
    )
    assert run is not None
    assert run["tool_type"] == "clusters"
    assert run["status"] == "success"
    assert run["segmentation_mode"] == "word"
    assert run["algorithm"] == "cosine"
    assert '"cluster_mode": "fixed_tag_centers"' in run["params_json"]
    assert len(item_rows) == len(response.points)
    assert all(row["cluster_id"] == row["tag_id"] for row in item_rows)
    assert all(row["x"] is not None and row["y"] is not None for row in item_rows)
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_embedding_clusters_reuses_cached_vectors_when_algorithm_changes(tmp_path) -> None:
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
    await embedding_service.create_tag(project.id, CreateEmbeddingTagRequest(name="海雾"))
    await embedding_service.create_tag(project.id, CreateEmbeddingTagRequest(name="证词"))
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      UpdateChapterRequest(content="海雾压低灯光，证词仍在桌上。").content,
    )

    first = await embedding_service.build_clusters(
      project.id,
      ClusterRequest(resource_type="chapter", resource_id="chapter-001", api_config_id=config.id),
    )
    call_count = len(runtime.calls)
    second = await embedding_service.build_clusters(
      project.id,
      ClusterRequest(
        resource_type="chapter",
        resource_id="chapter-001",
        api_config_id=config.id,
        algorithm="manhattan",
      ),
    )

    assert first.algorithm == "cosine"
    assert second.algorithm == "manhattan"
    assert len(runtime.calls) == call_count
    assert second.tag_cache.cache_hit_count == 2
    assert second.token_cache.cache_miss_count == 0
    assert all(point.raw_distance is not None and point.raw_score is None for point in second.points)
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_embedding_clusters_supports_document_range_and_shortage_warnings(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    document_service,
    embedding_service,
    _db,
    runtime,
    api_config_service,
  ) = await _build_embedding_services(tmp_path)
  try:
    config = await _create_embedding_config(api_config_service)
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await embedding_service.create_tag(project.id, CreateEmbeddingTagRequest(name="线索"))
    content = "第一句无关。第二句记录蓝色证词。第三句收束。"
    await document_service.update_document(
      project.id,
      "outline",
      UpdateDocumentRequest(content=content).content,
    )
    start = len("第一句无关。")
    end = start + len("第二句记录蓝色证词。")

    response = await embedding_service.build_clusters(
      project.id,
      ClusterRequest(
        resource_type="document",
        resource_id="outline",
        api_config_id=config.id,
        segmentation_mode="sentence",
        range={"start_offset": start, "end_offset": end},
      ),
    )

    assert response.resource_type == "document"
    assert response.warnings == ["语言簇至少需要 2 个标签才能形成对比；当前仅显示单簇归属。"]
    assert [point.text for point in response.points] == ["第二句记录蓝色证词。"]
    assert response.points[0].start_offset == start
    assert response.points[0].end_offset == end
    assert sum(cluster.point_count for cluster in response.clusters) == 1
    assert [call[2] for call in runtime.calls] == [
      "embedding_clusters_tags",
      "embedding_clusters_tokens",
    ]
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_embedding_clusters_empty_text_returns_stable_projection(tmp_path) -> None:
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
    await embedding_service.create_tag(project.id, CreateEmbeddingTagRequest(name="危险"))
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      UpdateChapterRequest(content="   \n  ").content,
    )

    response = await embedding_service.build_clusters(
      project.id,
      ClusterRequest(resource_type="chapter", resource_id="chapter-001", api_config_id=config.id),
    )

    item_rows = await db.fetch_all(
      "SELECT token_index FROM embedding_analysis_items WHERE run_id = ?",
      (response.run_id,),
    )
    assert response.points == []
    assert response.token_cache.requested_count == 0
    assert response.clusters[0].point_count == 0
    assert response.clusters[0].average_closeness is None
    assert response.tag_anchors[0].x == 0.0
    assert response.tag_anchors[0].y == 0.0
    assert response.warnings == [
      "语言簇至少需要 2 个标签才能形成对比；当前仅显示单簇归属。",
      "分析范围内没有可用于 Embedding 的分词。",
    ]
    assert [call[2] for call in runtime.calls] == ["embedding_clusters_tags"]
    assert item_rows == []
  finally:
    await store.shutdown()
