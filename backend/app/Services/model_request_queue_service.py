from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, AsyncIterable, Awaitable, Callable
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum
from itertools import count
from typing import TypeVar, cast

from app.Schemas.model_queue import (
  ModelQueueItem,
  ModelQueueRequestKind,
  ModelQueueRequestStatus,
  ModelQueueSnapshot,
)
from app.Utils.llm import (
  CompletionClient,
  LLMMessage,
  LLMRequestOverrides,
  LLMResponse,
  LLMStreamEvent,
)

_DEFAULT_WORKERS = 2
_T = TypeVar("_T")
_current_priority: ContextVar["ModelRequestPriority | None"] = ContextVar(
  "model_request_priority",
  default=None,
)
_current_label: ContextVar[str | None] = ContextVar("model_request_label", default=None)
_current_kind: ContextVar[ModelQueueRequestKind | None] = ContextVar(
  "model_request_kind",
  default=None,
)


class ModelRequestPriority(IntEnum):
  manual = 0
  batch = 1
  auto = 2


@dataclass(order=True)
class _QueuedModelRequest:
  priority: int
  sequence: int
  id: str = field(compare=False)
  kind: ModelQueueRequestKind = field(compare=False)
  label: str = field(compare=False)
  model: str | None = field(compare=False)
  status: ModelQueueRequestStatus = field(compare=False)
  queued_at: str = field(compare=False)
  started_at: str | None = field(compare=False)
  factory: Callable[[], Awaitable[object]] = field(compare=False)
  future: asyncio.Future[object] = field(compare=False)


class ModelRequestQueueService:
  def __init__(self, *, worker_count: int = _DEFAULT_WORKERS) -> None:
    self._worker_count = max(1, worker_count)
    self._queue: asyncio.PriorityQueue[_QueuedModelRequest] = asyncio.PriorityQueue()
    self._lock = asyncio.Lock()
    self._sequence = count()
    self._workers: list[asyncio.Task[None]] = []
    self._items: dict[str, _QueuedModelRequest] = {}

  async def start(self) -> None:
    async with self._lock:
      self._workers = [worker for worker in self._workers if not worker.done()]
      if self._workers:
        return
      self._workers = [
        asyncio.create_task(self._worker(), name=f"model-request-queue-{index}")
        for index in range(self._worker_count)
      ]

  async def shutdown(self) -> None:
    async with self._lock:
      workers = list(self._workers)
      self._workers = []
      items = list(self._items.values())
      self._items.clear()

    while True:
      try:
        item = self._queue.get_nowait()
      except asyncio.QueueEmpty:
        break
      if not item.future.done():
        item.future.cancel()
      self._queue.task_done()

    for item in items:
      if not item.future.done():
        item.future.cancel()

    for worker in workers:
      worker.cancel()
    if workers:
      await asyncio.gather(*workers, return_exceptions=True)

  async def run(
    self,
    label: str,
    factory: Callable[[], Awaitable[_T]],
    *,
    kind: ModelQueueRequestKind = "llm",
    model: str | None = None,
    priority: ModelRequestPriority = ModelRequestPriority.manual,
  ) -> _T:
    await self.start()
    future: asyncio.Future[object] = asyncio.get_running_loop().create_future()
    sequence = next(self._sequence)
    item = _QueuedModelRequest(
      priority=int(priority),
      sequence=sequence,
      id=f"model-request-{sequence}",
      kind=kind,
      label=label,
      model=model,
      status="queued",
      queued_at=_now(),
      started_at=None,
      factory=factory,
      future=future,
    )
    async with self._lock:
      self._items[item.id] = item
    await self._queue.put(item)
    return cast(_T, await future)

  async def snapshot(self) -> ModelQueueSnapshot:
    async with self._lock:
      items = list(self._items.values())
    return ModelQueueSnapshot(
      worker_count=self._worker_count,
      queued_count=sum(1 for item in items if item.status == "queued"),
      running_count=sum(1 for item in items if item.status == "running"),
      items=[
        ModelQueueItem(
          id=item.id,
          kind=item.kind,
          label=item.label,
          status=item.status,
          priority=_priority_label(item.priority),
          model=item.model,
          queued_at=item.queued_at,
          started_at=item.started_at,
        )
        for item in sorted(
          items,
          key=lambda item: (
            0 if item.status == "running" else 1,
            item.priority,
            item.sequence,
          ),
        )
      ],
    )

  async def run_stream(
    self,
    label: str,
    factory: Callable[[], AsyncIterator[_T]],
    *,
    kind: ModelQueueRequestKind = "llm",
    model: str | None = None,
    priority: ModelRequestPriority = ModelRequestPriority.manual,
  ) -> AsyncIterator[_T]:
    await self.start()
    channel: asyncio.Queue[object] = asyncio.Queue()
    sentinel = object()
    sequence = next(self._sequence)
    future: asyncio.Future[object] = asyncio.get_running_loop().create_future()

    async def wrapped() -> None:
      try:
        async for chunk in factory():
          await channel.put(chunk)
      except BaseException as exc:
        await channel.put(exc)
      finally:
        await channel.put(sentinel)

    item = _QueuedModelRequest(
      priority=int(priority),
      sequence=sequence,
      id=f"model-request-{sequence}",
      kind=kind,
      label=label,
      model=model,
      status="queued",
      queued_at=_now(),
      started_at=None,
      factory=wrapped,
      future=future,
    )
    async with self._lock:
      self._items[item.id] = item
    await self._queue.put(item)

    async def iterate() -> AsyncIterator[_T]:
      while True:
        value = await channel.get()
        if value is sentinel:
          break
        if isinstance(value, BaseException):
          raise value
        yield value

    return iterate()

  async def _worker(self) -> None:
    while True:
      item = await self._queue.get()
      try:
        if item.future.cancelled():
          continue
        async with self._lock:
          item.status = "running"
          item.started_at = _now()
        try:
          result = await item.factory()
        except Exception as exc:
          if not item.future.done():
            item.future.set_exception(exc)
        else:
          if not item.future.done():
            item.future.set_result(result)
      finally:
        async with self._lock:
          self._items.pop(item.id, None)
        self._queue.task_done()


class QueuedCompletionClient:
  def __init__(
    self,
    client: CompletionClient,
    queue: ModelRequestQueueService,
    *,
    priority: ModelRequestPriority = ModelRequestPriority.manual,
  ) -> None:
    self._client = client
    self._queue = queue
    self._priority = priority

  @property
  def model(self) -> str:
    return self._client.model

  @property
  def is_configured(self) -> bool:
    return self._client.is_configured

  def is_configured_for(self, overrides: LLMRequestOverrides | None = None) -> bool:
    return self._client.is_configured_for(overrides)

  async def complete(
    self,
    messages: list[LLMMessage],
    overrides: LLMRequestOverrides | None = None,
  ) -> LLMResponse:
    return await self.complete_non_stream(messages, overrides)

  async def complete_non_stream(
    self,
    messages: list[LLMMessage],
    overrides: LLMRequestOverrides | None = None,
  ) -> LLMResponse:
    return await self._queue.run(
      _current_label.get() or _label("chat", overrides),
      lambda: self._client.complete_non_stream(messages, overrides),
      kind=_current_kind.get() or "llm",
      model=_model(overrides, self._client.model),
      priority=_current_priority.get() or self._priority,
    )

  async def complete_stream(
    self,
    messages: list[LLMMessage],
    overrides: LLMRequestOverrides | None = None,
  ) -> AsyncIterator[LLMStreamEvent]:
    stream = await self._queue.run_stream(
      _current_label.get() or _label("chat", overrides),
      lambda: self._client.complete_stream(messages, overrides),
      kind=_current_kind.get() or "llm",
      model=_model(overrides, self._client.model),
      priority=_current_priority.get() or self._priority,
    )
    async for event in stream:
      yield event

  async def shutdown(self) -> None:
    shutdown = getattr(self._client, "shutdown", None)
    if callable(shutdown):
      await shutdown()


@contextmanager
def model_request_priority(priority: ModelRequestPriority):
  token = _current_priority.set(priority)
  try:
    yield
  finally:
    _current_priority.reset(token)


@contextmanager
def model_request_label(label: str, *, kind: ModelQueueRequestKind = "llm"):
  label_token = _current_label.set(label)
  kind_token = _current_kind.set(kind)
  try:
    yield
  finally:
    _current_label.reset(label_token)
    _current_kind.reset(kind_token)


def _label(kind: str, overrides: LLMRequestOverrides | None) -> str:
  model = overrides.model if overrides and overrides.model else ""
  return f"llm:{kind}:{model}"


def _model(overrides: LLMRequestOverrides | None, fallback: str) -> str:
  return overrides.model if overrides and overrides.model else fallback


def _priority_label(priority: int) -> ModelQueueRequestPriority:
  if priority == int(ModelRequestPriority.batch):
    return "batch"
  if priority == int(ModelRequestPriority.auto):
    return "auto"
  return "manual"


def _now() -> str:
  return datetime.now(UTC).isoformat()
