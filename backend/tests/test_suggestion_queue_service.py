import asyncio
import logging

import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.perspectives import CreatePerspectiveRequest, Perspective, UpdatePerspectiveRequest
from app.Schemas.projects import CreateProjectRequest
from app.Schemas.suggestions import SuggestionCard, SuggestionRequestTrigger
from app.Services.model_request_queue_service import (
  ModelRequestPriority,
  ModelRequestQueueService,
  QueuedCompletionClient,
)
from app.Services.suggestion_queue_service import SuggestionQueueService
from app.Utils.errors import LLMContextWindowExceededError
from app.Utils.llm import LLMMessage, LLMRequestOverrides, LLMResponse
from tests.fakes import FakeLLMClient
from tests.service_factories import build_suggestion_services


class SlowFakeLLMClient(FakeLLMClient):
  async def complete(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> LLMResponse:
    await asyncio.sleep(0.05)
    return await super().complete(messages, overrides)


class PartiallyFailingSuggestionService:
  async def list_enabled_perspective_ids(self, project_id: str) -> list[str]:
    return ["working-perspective", "broken-perspective"]

  async def suggest_for_perspective(
    self,
    project_id: str,
    chapter_id: str,
    paragraph: str,
    perspective_id: str,
  ) -> list[SuggestionCard]:
    if perspective_id == "broken-perspective":
      raise RuntimeError("suggestion failed")
    return [
      SuggestionCard(
        id="card-1",
        perspective_id=perspective_id,
        perspective_name="Working Perspective",
        title="可用建议",
        body="保留其它视角的结果。",
        severity="calm",
        source="local",
      )
    ]


@pytest.mark.asyncio
async def test_suggestion_queue_keeps_perspective_requests_independent(tmp_path) -> None:
  llm_client = FakeLLMClient('{"cards": []}')
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    api_config_service,
  ) = await build_suggestion_services(tmp_path, llm_client)
  queue = SuggestionQueueService(suggestion_service)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    pace = await _create_enabled_perspective(perspective_service, project.id, "Pace Editor")
    character = await _create_enabled_perspective(
      perspective_service, project.id, "Character Critic"
    )
    shared_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Shared Config",
        api_key="shared-secret",
        base_url="https://shared.example.test",
        mode="non_stream",
        model="shared-model",
      ),
    )
    for perspective in (pace, character):
      await perspective_service.update_perspective(
        project.id,
        perspective.id,
        UpdatePerspectiveRequest(api_config_id=shared_config.id),
      )
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在码头。")

    suggestions = await queue.request_suggestions(
      project.id,
      "chapter-001",
      "林澈停在码头。",
      perspective_id=None,
      trigger=SuggestionRequestTrigger.batch,
    )

    assert len(llm_client.calls) == 2
    user_messages = [call[0][1].content for call in llm_client.calls]
    assert sum(f'"id": "{pace.id}"' in content for content in user_messages) == 1
    assert sum(f'"id": "{character.id}"' in content for content in user_messages) == 1
    assert all(
      not (f'"id": "{pace.id}"' in content and f'"id": "{character.id}"' in content)
      for content in user_messages
    )
    assert {suggestion.perspective_id for suggestion in suggestions} == {
      pace.id,
      character.id,
    }
  finally:
    await queue.shutdown()
    await store.shutdown()


@pytest.mark.asyncio
async def test_suggestion_queue_logs_partial_failures_without_dropping_successes(caplog) -> None:
  queue = SuggestionQueueService(PartiallyFailingSuggestionService())  # type: ignore[arg-type]
  caplog.set_level(logging.WARNING, logger="app.Services.suggestion_queue_service")
  try:
    suggestions = await queue.request_suggestions(
      "project-1",
      "chapter-1",
      "有内容的段落。",
      perspective_id=None,
      trigger=SuggestionRequestTrigger.batch,
    )

    assert [suggestion.perspective_id for suggestion in suggestions] == [
      "working-perspective"
    ]
    assert "broken-perspective" in caplog.text
    assert "suggestion failed" in caplog.text
  finally:
    await queue.shutdown()


@pytest.mark.asyncio
async def test_suggestion_queue_deduplicates_same_pending_request(tmp_path) -> None:
  llm_client = SlowFakeLLMClient('{"cards": []}')
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    api_config_service,
  ) = await build_suggestion_services(tmp_path, llm_client)
  queue = SuggestionQueueService(suggestion_service)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    perspective = await _create_enabled_perspective(
      perspective_service, project.id, "Line Reader"
    )
    config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Line Config",
        api_key="line-secret",
        base_url="https://line.example.test",
        mode="non_stream",
        model="line-model",
      ),
    )
    await perspective_service.update_perspective(
      project.id,
      perspective.id,
      UpdatePerspectiveRequest(api_config_id=config.id),
    )
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在码头。")

    first, second = await asyncio.gather(
      queue.request_suggestions(
        project.id,
        "chapter-001",
        "林澈停在码头。",
        perspective_id=perspective.id,
        trigger=SuggestionRequestTrigger.manual,
      ),
      queue.request_suggestions(
        project.id,
        "chapter-001",
        "林澈停在码头。",
        perspective_id=perspective.id,
        trigger=SuggestionRequestTrigger.batch,
      ),
    )

    assert len(llm_client.calls) == 1
    assert [suggestion.perspective_id for suggestion in first] == [perspective.id]
    assert [suggestion.perspective_id for suggestion in second] == [perspective.id]
  finally:
    await queue.shutdown()
    await store.shutdown()


@pytest.mark.asyncio
async def test_suggestion_queue_replaces_unstarted_auto_request(tmp_path) -> None:
  model_queue = ModelRequestQueueService(worker_count=1)
  raw_llm_client = FakeLLMClient('{"cards": []}')
  llm_client = QueuedCompletionClient(raw_llm_client, model_queue)
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    api_config_service,
  ) = await build_suggestion_services(tmp_path, llm_client)
  queue = SuggestionQueueService(suggestion_service)
  release_blocker = asyncio.Event()
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    perspective = await _create_enabled_perspective(
      perspective_service, project.id, "Line Reader"
    )
    config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Line Config",
        api_key="line-secret",
        base_url="https://line.example.test",
        mode="non_stream",
        model="line-model",
      ),
    )
    await perspective_service.update_perspective(
      project.id,
      perspective.id,
      UpdatePerspectiveRequest(api_config_id=config.id),
    )
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在码头。")

    blocker_started = asyncio.Event()

    async def block_model_queue() -> str:
      blocker_started.set()
      await release_blocker.wait()
      return "blocker"

    blocker = asyncio.create_task(
      model_queue.run(
        "blocker",
        block_model_queue,
        priority=ModelRequestPriority.manual,
      )
    )
    await blocker_started.wait()
    stale_auto = asyncio.create_task(
      queue.request_suggestions(
        project.id,
        "chapter-001",
        "旧的自动建议段落。",
        perspective_id=perspective.id,
        trigger=SuggestionRequestTrigger.auto,
      )
    )
    await asyncio.sleep(0)
    fresh_auto = asyncio.create_task(
      queue.request_suggestions(
        project.id,
        "chapter-001",
        "新的自动建议段落。",
        perspective_id=perspective.id,
        trigger=SuggestionRequestTrigger.auto,
      )
    )

    stale_result = await asyncio.wait_for(stale_auto, timeout=1)
    release_blocker.set()
    blocker_result, fresh_result = await asyncio.gather(blocker, fresh_auto)

    assert stale_result == []
    assert blocker_result == "blocker"
    assert [suggestion.perspective_id for suggestion in fresh_result] == [perspective.id]
    assert len(raw_llm_client.calls) == 1
    user_messages = [call[0][1].content for call in raw_llm_client.calls]
    assert any("新的自动建议段落。" in content for content in user_messages)
    assert all("旧的自动建议段落。" not in content for content in user_messages)
  finally:
    release_blocker.set()
    await queue.shutdown()
    await model_queue.shutdown()
    await store.shutdown()


@pytest.mark.asyncio
async def test_suggestion_queue_lets_model_queue_prioritize_manual_requests(tmp_path) -> None:
  model_queue = ModelRequestQueueService(worker_count=1)
  raw_llm_client = FakeLLMClient('{"cards": []}')
  llm_client = QueuedCompletionClient(raw_llm_client, model_queue)
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    api_config_service,
  ) = await build_suggestion_services(tmp_path, llm_client)
  queue = SuggestionQueueService(suggestion_service)
  release_blocker = asyncio.Event()
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    perspective = await _create_enabled_perspective(
      perspective_service, project.id, "Line Reader"
    )
    config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Line Config",
        api_key="line-secret",
        base_url="https://line.example.test",
        mode="non_stream",
        model="line-model",
      ),
    )
    await perspective_service.update_perspective(
      project.id,
      perspective.id,
      UpdatePerspectiveRequest(api_config_id=config.id),
    )
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在码头。")

    blocker_started = asyncio.Event()

    async def block_model_queue() -> str:
      blocker_started.set()
      await release_blocker.wait()
      return "blocker"

    blocker = asyncio.create_task(
      model_queue.run(
        "blocker",
        block_model_queue,
        priority=ModelRequestPriority.manual,
      )
    )
    await blocker_started.wait()
    auto = asyncio.create_task(
      queue.request_suggestions(
        project.id,
        "chapter-001",
        "自动建议段落。",
        perspective_id=perspective.id,
        trigger=SuggestionRequestTrigger.auto,
      )
    )
    await asyncio.sleep(0)
    manual = asyncio.create_task(
      queue.request_suggestions(
        project.id,
        "chapter-001",
        "手动建议段落。",
        perspective_id=perspective.id,
        trigger=SuggestionRequestTrigger.manual,
      )
    )

    await _wait_for_queued_model_requests(model_queue, 2)
    release_blocker.set()
    await asyncio.gather(blocker, auto, manual)

    user_messages = [call[0][1].content for call in raw_llm_client.calls]
    assert len(user_messages) == 2
    assert "手动建议段落。" in user_messages[0]
    assert "自动建议段落。" in user_messages[1]
  finally:
    release_blocker.set()
    await queue.shutdown()
    await model_queue.shutdown()
    await store.shutdown()


@pytest.mark.asyncio
async def test_suggestion_queue_surfaces_context_window_overflow(tmp_path) -> None:
  llm_client = FakeLLMClient('{"cards": []}')
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    api_config_service,
  ) = await build_suggestion_services(tmp_path, llm_client)
  queue = SuggestionQueueService(suggestion_service)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    tiny = await _create_enabled_perspective(perspective_service, project.id, "Tiny Context")
    normal = await _create_enabled_perspective(perspective_service, project.id, "Normal Context")
    tiny_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Tiny Config",
        api_key="tiny-secret",
        base_url="https://tiny.example.test",
        mode="non_stream",
        model="tiny-model",
        max_tokens=4096,
        context_window_tokens=1024,
      ),
    )
    normal_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Normal Config",
        api_key="normal-secret",
        base_url="https://normal.example.test",
        mode="non_stream",
        model="normal-model",
      ),
    )
    await perspective_service.update_perspective(
      project.id,
      tiny.id,
      UpdatePerspectiveRequest(api_config_id=tiny_config.id),
    )
    await perspective_service.update_perspective(
      project.id,
      normal.id,
      UpdatePerspectiveRequest(api_config_id=normal_config.id),
    )
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在码头。")

    with pytest.raises(LLMContextWindowExceededError):
      await queue.request_suggestions(
        project.id,
        "chapter-001",
        "林澈停在码头。",
        perspective_id=None,
        trigger=SuggestionRequestTrigger.batch,
      )
  finally:
    await queue.shutdown()
    await store.shutdown()


async def _create_enabled_perspective(
  perspective_service,
  project_id: str,
  name: str,
) -> Perspective:
  perspective = await perspective_service.create_perspective(
    project_id,
    CreatePerspectiveRequest(
      name=name,
      description=f"{name} description",
      instructions=f"{name} instructions",
    ),
  )
  return await perspective_service.update_perspective(
    project_id,
    perspective.id,
    UpdatePerspectiveRequest(is_enabled=True),
  )


async def _wait_for_queued_model_requests(
  model_queue: ModelRequestQueueService,
  count: int,
) -> None:
  for _ in range(100):
    snapshot = await model_queue.snapshot()
    if snapshot.queued_count >= count:
      return
    await asyncio.sleep(0.01)
  snapshot = await model_queue.snapshot()
  raise AssertionError(
    f"Expected at least {count} queued model requests, got {snapshot.queued_count}"
  )
