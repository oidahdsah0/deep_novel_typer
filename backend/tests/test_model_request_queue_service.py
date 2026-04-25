import asyncio

import pytest

from app.Services.model_request_queue_service import (
  ModelRequestPriority,
  ModelRequestQueueService,
  QueuedCompletionClient,
)
from app.Utils.llm import LLMMessage, LLMRequestOverrides
from tests.fakes import FakeLLMClient


@pytest.mark.asyncio
async def test_model_request_queue_prioritizes_manual_before_auto() -> None:
  queue = ModelRequestQueueService(worker_count=1)
  events: list[str] = []

  async def run(label: str, delay: float = 0) -> str:
    if delay:
      await asyncio.sleep(delay)
    events.append(label)
    return label

  try:
    blocker = asyncio.create_task(
      queue.run("blocker", lambda: run("blocker", 0.05), priority=ModelRequestPriority.manual)
    )
    await asyncio.sleep(0)
    auto = asyncio.create_task(
      queue.run("auto", lambda: run("auto"), priority=ModelRequestPriority.auto)
    )
    manual = asyncio.create_task(
      queue.run("manual", lambda: run("manual"), priority=ModelRequestPriority.manual)
    )

    assert await asyncio.gather(blocker, auto, manual) == ["blocker", "auto", "manual"]
    assert events == ["blocker", "manual", "auto"]
  finally:
    await queue.shutdown()


@pytest.mark.asyncio
async def test_model_request_queue_snapshot_shows_running_and_queued_items() -> None:
  queue = ModelRequestQueueService(worker_count=1)
  started = asyncio.Event()
  release = asyncio.Event()

  async def block() -> str:
    started.set()
    await release.wait()
    return "done"

  async def later() -> str:
    return "later"

  try:
    running_task = asyncio.create_task(
      queue.run(
        "generate_next_paragraph",
        block,
        model="writer-model",
        priority=ModelRequestPriority.manual,
      )
    )
    await started.wait()
    queued_task = asyncio.create_task(
      queue.run(
        "api_config_health_embedding",
        later,
        kind="embedding",
        model="embed-model",
        priority=ModelRequestPriority.batch,
      )
    )
    await asyncio.sleep(0)

    snapshot = await queue.snapshot()

    assert snapshot.worker_count == 1
    assert snapshot.running_count == 1
    assert snapshot.queued_count == 1
    assert [(item.label, item.kind, item.status, item.model) for item in snapshot.items] == [
      ("generate_next_paragraph", "llm", "running", "writer-model"),
      ("api_config_health_embedding", "embedding", "queued", "embed-model"),
    ]

    release.set()
    assert await asyncio.gather(running_task, queued_task) == ["done", "later"]
  finally:
    release.set()
    await queue.shutdown()


@pytest.mark.asyncio
async def test_queued_completion_client_routes_completion_through_queue() -> None:
  queue = ModelRequestQueueService(worker_count=1)
  raw_client = FakeLLMClient('{"text": "ok"}')
  client = QueuedCompletionClient(raw_client, queue)

  try:
    response = await client.complete(
      [LLMMessage(role="user", content="ping")],
      LLMRequestOverrides(api_key="secret", model="queued-model"),
    )

    assert response.content == '{"text": "ok"}'
    assert response.model == "queued-model"
    assert len(raw_client.calls) == 1
  finally:
    await queue.shutdown()
