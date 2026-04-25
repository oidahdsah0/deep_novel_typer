import json
import zipfile
from io import BytesIO

import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.chapters import UpdateChapterRequest
from app.Schemas.embeddings import CreateEmbeddingTagRequest, HeatmapRequest
from app.Schemas.project_transfer import ProjectExportOptions
from app.Schemas.projects import CreateProjectRequest
from app.Services.api_configs import APIConfigService
from app.Services.chapter_service import ChapterService
from app.Services.debug_log_service import DebugLogService
from app.Services.document_service import DocumentService
from app.Services.embeddings import EmbeddingService
from app.Services.project_service import ProjectService
from app.Services.project_transfer import ProjectTransferService
from app.Utils.config import _load_llm_settings
from app.Utils.db import AsyncDatabase
from app.Utils.locks import AsyncLockRegistry
from app.Utils.paths import PathResolver
from app.Utils.storage import AsyncFileStore
from tests.fakes import FakeEmbeddingRuntime


@pytest.mark.asyncio
async def test_embedding_heatmap_writes_sanitized_debug_logs_and_exports(tmp_path) -> None:
  stack = await _build_stack(tmp_path)
  secret_text = "绝密正文片段-Alpha"
  secret_tag = "绝密标签描述-Beta"
  try:
    config = await _create_embedding_config(stack.api_config_service)
    project = await stack.project_service.create_project(CreateProjectRequest(title="Test Book"))
    await stack.embedding_service.create_tag(
      project.id,
      CreateEmbeddingTagRequest(name="危险", description=secret_tag),
    )
    await stack.chapter_service.update_chapter(
      project.id,
      "chapter-001",
      UpdateChapterRequest(content=f"{secret_text} 在码头出现。").content,
    )

    first = await stack.embedding_service.build_heatmap(
      project.id,
      HeatmapRequest(
        resource_type="chapter",
        resource_id="chapter-001",
        api_config_id=config.id,
      ),
    )
    logs = await stack.debug_log_service.request_logs(project_id=project.id)

    assert {log.request_type for log in logs} == {
      "embedding_heatmap_tags",
      "embedding_heatmap_tokens",
    }
    assert all(log.model_kind == "embedding" for log in logs)
    assert all(log.debug_readable.embedding_summary["run_id"] == first.run_id for log in logs)
    assert all("input" not in log.request_body for log in logs)
    assert all("data" not in log.response_body for log in logs)
    assert all("input_hashes" in log.request_body for log in logs)
    assert (await stack.debug_log_service.token_usage(project.id)).unknown_usage_requests == 0

    debug_json = json.dumps([log.model_dump(mode="json") for log in logs], ensure_ascii=False)
    assert secret_text not in debug_json
    assert secret_tag not in debug_json
    assert "embedding-secret" not in debug_json
    assert "Authorization" not in debug_json
    assert '"vectors"' not in debug_json

    call_count = len(stack.runtime.calls)
    await stack.embedding_service.build_heatmap(
      project.id,
      HeatmapRequest(
        resource_type="chapter",
        resource_id="chapter-001",
        api_config_id=config.id,
      ),
    )
    assert len(stack.runtime.calls) == call_count
    assert len(await stack.debug_log_service.request_logs(project_id=project.id)) == len(logs)

    archive = await stack.transfer_service.export_project(
      project.id,
      ProjectExportOptions(include_debug_logs=True),
    )
    with zipfile.ZipFile(BytesIO(archive), "r") as zipped:
      debug_rows = json.loads(zipped.read("data/debug_logs.json"))["rows"]
      assert {row["model_kind"] for row in debug_rows} == {"embedding"}
      exported_debug = json.dumps(debug_rows, ensure_ascii=False)
      assert secret_text not in exported_debug
      assert secret_tag not in exported_debug
      assert "embedding-secret" not in exported_debug
  finally:
    await stack.store.shutdown()


@pytest.mark.asyncio
async def test_embedding_debug_logs_unknown_usage_and_errors(tmp_path) -> None:
  stack = await _build_stack(tmp_path)
  try:
    config = await _create_embedding_config(stack.api_config_service)
    project = await stack.project_service.create_project(CreateProjectRequest(title="Test Book"))
    await stack.embedding_service.create_tag(
      project.id,
      CreateEmbeddingTagRequest(name="线索", description="证据链"),
    )
    await stack.chapter_service.update_chapter(
      project.id,
      "chapter-001",
      UpdateChapterRequest(content="蓝色证词在码头留下。").content,
    )

    stack.runtime.omit_usage = True
    await stack.embedding_service.build_heatmap(
      project.id,
      HeatmapRequest(resource_type="chapter", resource_id="chapter-001", api_config_id=config.id),
    )
    usage = await stack.debug_log_service.token_usage(project.id)
    assert usage.total == 0
    assert usage.unknown_usage_requests == 2

    stack.runtime.omit_usage = False
    stack.runtime.fail_next = RuntimeError("embedding endpoint failed")
    await stack.embedding_service.create_tag(
      project.id,
      CreateEmbeddingTagRequest(name="风险", description="不能泄露的描述"),
    )
    with pytest.raises(RuntimeError):
      await stack.embedding_service.build_heatmap(
        project.id,
        HeatmapRequest(
          resource_type="chapter",
          resource_id="chapter-001",
          api_config_id=config.id,
          force_reembed=True,
        ),
      )

    logs = await stack.debug_log_service.request_logs(project_id=project.id)
    error_log = next(log for log in logs if log.status == "error")
    assert error_log.model_kind == "embedding"
    assert error_log.request_type == "embedding_heatmap_tags"
    assert error_log.debug_readable.embedding_summary["error_type"] == "RuntimeError"
    assert "不能泄露的描述" not in json.dumps(error_log.model_dump(mode="json"), ensure_ascii=False)
  finally:
    await stack.store.shutdown()


class _Stack:
  def __init__(
    self,
    *,
    db: AsyncDatabase,
    store: AsyncFileStore,
    project_service: ProjectService,
    chapter_service: ChapterService,
    api_config_service: APIConfigService,
    embedding_service: EmbeddingService,
    debug_log_service: DebugLogService,
    transfer_service: ProjectTransferService,
    runtime: FakeEmbeddingRuntime,
  ) -> None:
    self.db = db
    self.store = store
    self.project_service = project_service
    self.chapter_service = chapter_service
    self.api_config_service = api_config_service
    self.embedding_service = embedding_service
    self.debug_log_service = debug_log_service
    self.transfer_service = transfer_service
    self.runtime = runtime


async def _build_stack(tmp_path) -> _Stack:
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
  debug_log_service = DebugLogService(db, locks)
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
    debug_log_service=debug_log_service,
  )
  transfer_service = ProjectTransferService(db, store, paths, locks)
  return _Stack(
    db=db,
    store=store,
    project_service=project_service,
    chapter_service=chapter_service,
    api_config_service=api_config_service,
    embedding_service=embedding_service,
    debug_log_service=debug_log_service,
    transfer_service=transfer_service,
    runtime=runtime,
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
      model="Qwen3-Embedding-8B",
      thinking_enabled=False,
      max_tokens=1024,
      temperature=None,
      top_p=None,
      top_k=None,
      dimensions=4096,
    )
  )
