import pytest

from app.Services.api_configs import APIConfigService
from app.Services.api_configs.health import OpenAIAPIConfigHealthChecker
from app.Services.model_request_queue_service import ModelRequestPriority
from app.Utils.config import _load_llm_settings
from app.Utils.db import AsyncDatabase
from app.Utils.errors import EntityConflictError, EntityNotFoundError
from app.Utils.locks import AsyncLockRegistry
from app.Schemas.api_configs import CreateAPIConfigRequest, UpdateAPIConfigRequest
from app.Schemas.perspectives import CreatePerspectiveRequest, UpdatePerspectiveRequest
from app.Schemas.projects import CreateProjectRequest
from tests.fakes import DisabledLLMClient, FakeAPIConfigHealthChecker
from tests.service_factories import build_suggestion_services


class RecordingModelRequestQueue:
  def __init__(self) -> None:
    self.calls = []

  async def run(self, label, factory, *, kind, model, priority):
    self.calls.append((label, kind, model, priority))
    return await factory()

@pytest.mark.asyncio
async def test_api_config_service_persists_global_configs(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    perspective_service,
    _suggestion_service,
    api_config_service,
  ) = await build_suggestion_services(tmp_path, DisabledLLMClient())
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    defaults = await api_config_service.list_configs()
    templates = api_config_service.list_templates()
    created = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="DB Config",
        api_key="db-secret",
        base_url="https://db.example.test",
        mode="non_stream",
        model="db-model",
        thinking_enabled=False,
        reasoning_effort="high",
        max_tokens=1024,
        context_window_tokens=512_000,
        temperature=0.8,
        top_p=0.92,
        top_k=40,
        is_default=True,
      ),
    )
    effective = await api_config_service.get_effective_config(created.id)

    assert len(defaults) == 1
    assert defaults[0].id == "default-api"
    assert defaults[0].provider == "deepseek"
    assert defaults[0].kind == "llm"
    assert defaults[0].model == "deepseek-v4-pro"
    assert defaults[0].api_key_configured is False
    assert {template.provider for template in templates} >= {"deepseek", "openai", "gemini", "grok"}
    assert {template.kind for template in templates} == {"llm", "embedding"}
    assert created.base_url == "https://db.example.test"
    assert created.provider == "deepseek"
    assert created.kind == "llm"
    assert created.api_key_configured is True
    assert created.mode == "non_stream"
    assert created.top_p == 0.92
    assert created.top_k == 40
    assert created.context_window_tokens == 512_000
    assert created.is_default is True
    assert "api_key" not in created.model_dump()
    assert effective is not None
    assert effective.api_key == "db-secret"

    updated = await api_config_service.update_config(
      created.id,
      UpdateAPIConfigRequest(
        name="DB Config Updated",
        api_key=None,
        base_url="https://db2.example.test",
        mode="non_stream",
        model="db-model-2",
        thinking_enabled=True,
        reasoning_effort="max",
        max_tokens=10_000_000,
        context_window_tokens=1_000_000,
        temperature=None,
        top_p=0.8,
        top_k=20,
      ),
    )
    preserved = await api_config_service.get_effective_config(created.id)
    assert preserved.api_key == "db-secret"
    assert updated.name == "DB Config Updated"
    assert updated.max_tokens == 10_000_000
    assert updated.context_window_tokens == 1_000_000
    assert updated.top_p == 0.8
    assert updated.top_k == 20
    assert preserved.config.base_url == "https://db2.example.test"

    cleared = await api_config_service.update_config(
      created.id,
      UpdateAPIConfigRequest(
        name="DB Config Updated",
        clear_api_key=True,
        base_url="https://db3.example.test",
        mode="non_stream",
        model="db-model-3",
        thinking_enabled=True,
        reasoning_effort="high",
        max_tokens=2048,
        temperature=None,
        top_p=None,
        top_k=None,
      ),
    )
    cleared_effective = await api_config_service.get_effective_config(created.id)
    assert cleared.api_key_configured is False
    assert cleared_effective.api_key == ""

    embedding = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Embedding Config",
        provider="openai",
        kind="embedding",
        api_key="embedding-secret",
        api_key_required=True,
        base_url="https://api.openai.com/v1",
        mode="non_stream",
        model="text-embedding-3-small",
        thinking_enabled=False,
        max_tokens=1024,
        temperature=None,
        top_p=None,
        top_k=None,
        dimensions=1536,
      )
    )
    assert embedding.is_default is True
    assert (await api_config_service.get_effective_config(None, kind="embedding")).config.id == embedding.id

    await project_service.get_manifest(project.id)
    await perspective_service.create_perspective(
      project.id,
      CreatePerspectiveRequest(
        name="Pace Editor",
        description="关注节奏。",
        instructions="检查节奏。",
      ),
    )
    with pytest.raises(EntityNotFoundError):
      await perspective_service.update_perspective(
        project.id,
        "pace-editor",
        UpdatePerspectiveRequest(api_config_id=embedding.id),
      )
    await perspective_service.update_perspective(
      project.id,
      "pace-editor",
      UpdatePerspectiveRequest(api_config_id=created.id),
    )
    with pytest.raises(EntityConflictError):
      await api_config_service.delete_config(created.id)
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_api_config_delete_protects_last_config_per_kind(tmp_path) -> None:
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  api_config_service = APIConfigService(
    db,
    AsyncLockRegistry(),
    _load_llm_settings(),
  )
  await api_config_service.ensure_default_config()

  embedding = await api_config_service.create_config(
    CreateAPIConfigRequest(
      name="Only Embedding",
      provider="openai",
      kind="embedding",
      api_key_required=True,
      api_key="embedding-secret",
      base_url="https://api.openai.com/v1",
      mode="non_stream",
      model="text-embedding-3-small",
      thinking_enabled=False,
      max_tokens=1024,
      temperature=None,
      top_p=None,
      top_k=None,
      dimensions=1536,
    )
  )

  with pytest.raises(EntityConflictError, match="last API config of this type"):
    await api_config_service.delete_config("default-api")
  with pytest.raises(EntityConflictError, match="last API config of this type"):
    await api_config_service.delete_config(embedding.id)

  default_llm = await api_config_service.get_effective_config(None, kind="llm")
  assert default_llm is not None
  assert default_llm.config.id == "default-api"

  second_llm = await api_config_service.create_config(
    CreateAPIConfigRequest(
      name="Second LLM",
      provider="deepseek",
      kind="llm",
      api_key_required=True,
      api_key="llm-secret",
      base_url="https://api.deepseek.com",
      mode="non_stream",
      model="deepseek-chat",
      thinking_enabled=False,
      max_tokens=1024,
      temperature=None,
      top_p=None,
      top_k=None,
      is_default=True,
    )
  )
  assert second_llm.is_default is True

  await api_config_service.delete_config(second_llm.id)
  fallback_llm = await api_config_service.get_effective_config(None, kind="llm")
  remaining_llms = await api_config_service.list_configs("llm")

  assert fallback_llm is not None
  assert fallback_llm.config.id == "default-api"
  assert len(remaining_llms) == 1
  assert remaining_llms[0].id == "default-api"
  assert remaining_llms[0].is_default is True


@pytest.mark.asyncio
async def test_api_config_update_rejects_kind_changes(tmp_path) -> None:
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  api_config_service = APIConfigService(
    db,
    AsyncLockRegistry(),
    _load_llm_settings(),
  )
  await api_config_service.ensure_default_config()

  embedding = await api_config_service.create_config(
    CreateAPIConfigRequest(
      name="Embedding Config",
      provider="openai",
      kind="embedding",
      api_key_required=True,
      api_key="embedding-secret",
      base_url="https://api.openai.com/v1",
      mode="non_stream",
      model="text-embedding-3-small",
      thinking_enabled=False,
      max_tokens=1024,
      temperature=None,
      top_p=None,
      top_k=None,
      dimensions=1536,
    )
  )

  with pytest.raises(EntityConflictError, match="kind cannot be changed"):
    await api_config_service.update_config(
      "default-api",
      UpdateAPIConfigRequest(
        name="Default As Embedding",
        provider="openai",
        kind="embedding",
        api_key_required=True,
        base_url="https://api.openai.com/v1",
        mode="non_stream",
        model="text-embedding-3-small",
        thinking_enabled=False,
        max_tokens=1024,
        temperature=None,
        top_p=None,
        top_k=None,
        dimensions=1536,
      ),
    )

  with pytest.raises(EntityConflictError, match="kind cannot be changed"):
    await api_config_service.update_config(
      embedding.id,
      UpdateAPIConfigRequest(
        name="Embedding As LLM",
        provider="deepseek",
        kind="llm",
        api_key_required=True,
        base_url="https://api.deepseek.com",
        mode="non_stream",
        model="deepseek-chat",
        thinking_enabled=False,
        max_tokens=1024,
        temperature=None,
        top_p=None,
        top_k=None,
      ),
    )

  updated = await api_config_service.update_config(
    "default-api",
    UpdateAPIConfigRequest(
      name="Default API Updated",
      provider="deepseek",
      kind="llm",
      api_key_required=True,
      base_url="https://api.deepseek.com",
      mode="non_stream",
      model="deepseek-chat",
      thinking_enabled=False,
      max_tokens=1024,
      temperature=None,
      top_p=None,
      top_k=None,
    ),
  )

  assert updated.kind == "llm"
  assert updated.name == "Default API Updated"
  assert updated.model == "deepseek-chat"


@pytest.mark.asyncio
async def test_api_config_health_check_allows_local_configs_without_key(tmp_path) -> None:
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  health_checker = FakeAPIConfigHealthChecker()
  api_config_service = APIConfigService(
    db,
    AsyncLockRegistry(),
    _load_llm_settings(),
    health_checker,
  )

  local_config = await api_config_service.create_config(
    CreateAPIConfigRequest(
      name="Local Ollama",
      provider="ollama",
      kind="llm",
      api_key_required=False,
      base_url="http://127.0.0.1:11434/v1",
      mode="non_stream",
      model="llama3.1",
      thinking_enabled=False,
      max_tokens=1024,
      temperature=0.2,
      top_p=0.9,
      top_k=20,
    )
  )
  result = await api_config_service.health_check(local_config.id)

  assert result.ok is True
  assert result.json_mode_supported is True
  assert result.latency_ms == 12
  assert len(health_checker.llm_calls) == 1
  assert health_checker.llm_calls[0].api_key == ""
  assert health_checker.llm_calls[0].config.api_key_required is False

  cloud_config = await api_config_service.create_config(
    CreateAPIConfigRequest(
      name="Missing Key",
      provider="openai",
      kind="llm",
      api_key_required=True,
      api_key=None,
      base_url="https://api.openai.com/v1",
      mode="non_stream",
      model="gpt-4.1-mini",
      thinking_enabled=False,
      max_tokens=1024,
      temperature=None,
      top_p=None,
      top_k=None,
    )
  )
  missing_key = await api_config_service.health_check(cloud_config.id)

  assert missing_key.ok is False
  assert missing_key.error_code == "missing_required_config"
  assert len(health_checker.llm_calls) == 1


@pytest.mark.asyncio
async def test_openai_health_checker_always_routes_provider_requests_through_queue() -> None:
  queue = RecordingModelRequestQueue()
  checker = OpenAIAPIConfigHealthChecker(
    headers={},
    timeout_seconds=1,
    request_queue=queue,  # type: ignore[arg-type]
  )

  result = await checker._run_provider_request(
    "health-test",
    lambda: _successful_health_factory(),
    kind="llm",
    model="test-model",
  )

  assert result == "ok"
  assert queue.calls == [
    ("health-test", "llm", "test-model", ModelRequestPriority.manual),
  ]


@pytest.mark.asyncio
async def test_api_config_service_default_health_checker_has_queue(tmp_path) -> None:
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  api_config_service = APIConfigService(db, AsyncLockRegistry(), _load_llm_settings())

  assert api_config_service._health_checker._request_queue is not None
  await api_config_service.shutdown()


async def _successful_health_factory() -> str:
  return "ok"


@pytest.mark.asyncio
async def test_api_config_health_check_routes_embedding_configs(tmp_path) -> None:
  db = AsyncDatabase(tmp_path / "novel.db")
  await db.initialize()
  health_checker = FakeAPIConfigHealthChecker()
  api_config_service = APIConfigService(
    db,
    AsyncLockRegistry(),
    _load_llm_settings(),
    health_checker,
  )

  embedding_config = await api_config_service.create_config(
    CreateAPIConfigRequest(
      name="Local Embedding",
      provider="lm_studio",
      kind="embedding",
      api_key_required=False,
      base_url="http://127.0.0.1:1234/v1",
      mode="non_stream",
      model="text-embedding-local",
      thinking_enabled=False,
      max_tokens=1024,
      temperature=None,
      top_p=None,
      top_k=None,
      dimensions=768,
    )
  )
  result = await api_config_service.health_check(embedding_config.id)

  assert result.ok is True
  assert result.kind == "embedding"
  assert result.embedding_dimensions == 768
  assert result.json_mode_supported is None
  assert len(health_checker.embedding_calls) == 1
  assert health_checker.embedding_calls[0].config.id == embedding_config.id
  assert health_checker.llm_calls == []
