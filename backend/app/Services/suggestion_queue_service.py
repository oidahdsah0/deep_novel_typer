from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from hashlib import sha1
from itertools import count

from app.Schemas.suggestions import (
  SuggestionCard,
  SuggestionRequestTrigger,
)
from app.Services.model_request_queue_service import (
  ModelRequestPriority,
  model_request_priority,
)
from app.Services.suggestion_service import SuggestionService
from app.Utils.errors import LLMContextWindowExceededError

_LOGGER = logging.getLogger(__name__)


@dataclass
class _QueuedSuggestion:
  sequence: int
  key: str
  target_key: str
  project_id: str
  chapter_id: str
  paragraph: str
  perspective_id: str
  trigger: SuggestionRequestTrigger
  future: asyncio.Future[list[SuggestionCard]]
  task: asyncio.Task[None] | None = None
  cancelled: bool = False
  started: bool = False


class SuggestionQueueService:
  def __init__(
    self,
    suggestion_service: SuggestionService,
  ) -> None:
    self._suggestion_service = suggestion_service
    self._lock = asyncio.Lock()
    self._sequence = count()
    self._pending_by_key: dict[str, _QueuedSuggestion] = {}
    self._latest_auto_by_target: dict[str, _QueuedSuggestion] = {}

  async def start(self) -> None:
    return None

  async def shutdown(self) -> None:
    async with self._lock:
      pending = list(self._pending_by_key.values())
      self._pending_by_key.clear()
      self._latest_auto_by_target.clear()

    tasks = [item.task for item in pending if item.task is not None]
    for item in pending:
      item.cancelled = True
      if not item.future.done():
        item.future.set_result([])
      if item.task and not item.task.done():
        item.task.cancel()

    if tasks:
      await asyncio.gather(*tasks, return_exceptions=True)

  async def request_suggestions(
    self,
    project_id: str,
    chapter_id: str,
    paragraph: str,
    *,
    perspective_id: str | None,
    trigger: SuggestionRequestTrigger,
  ) -> list[SuggestionCard]:
    normalized_paragraph = paragraph.strip()
    if not normalized_paragraph:
      return []

    perspective_ids = (
      [perspective_id]
      if perspective_id
      else await self._suggestion_service.list_enabled_perspective_ids(project_id)
    )
    if not perspective_ids:
      return []

    futures = [
      await self._enqueue(
        project_id=project_id,
        chapter_id=chapter_id,
        paragraph=normalized_paragraph,
        perspective_id=item,
        trigger=trigger,
      )
      for item in perspective_ids
    ]
    groups = await asyncio.gather(*futures, return_exceptions=True)
    for group in groups:
      if isinstance(group, LLMContextWindowExceededError):
        raise group
    for perspective, group in zip(perspective_ids, groups, strict=True):
      if isinstance(group, BaseException):
        _LOGGER.warning(
          "Suggestion request failed for perspective %s in project %s chapter %s: %s",
          perspective,
          project_id,
          chapter_id,
          group,
        )
    suggestions = [
      suggestion
      for group in groups
      if not isinstance(group, BaseException)
      for suggestion in group
    ]
    exceptions = [group for group in groups if isinstance(group, BaseException)]
    if exceptions and len(exceptions) == len(groups):
      raise exceptions[0]
    return suggestions

  async def _enqueue(
    self,
    *,
    project_id: str,
    chapter_id: str,
    paragraph: str,
    perspective_id: str,
    trigger: SuggestionRequestTrigger,
  ) -> asyncio.Future[list[SuggestionCard]]:
    key = _request_key(project_id, chapter_id, paragraph, perspective_id)
    target_key = _target_key(project_id, chapter_id, perspective_id)
    async with self._lock:
      existing = self._pending_by_key.get(key)
      if existing is not None and not existing.future.done():
        return existing.future

      if trigger == SuggestionRequestTrigger.auto:
        previous = self._latest_auto_by_target.get(target_key)
        if previous is not None and previous.key != key and not previous.future.done():
          previous.cancelled = True
          self._pending_by_key.pop(previous.key, None)
          if not previous.future.done():
            previous.future.set_result([])
          if previous.task and not previous.task.done():
            previous.task.cancel()

      future = asyncio.get_running_loop().create_future()
      item = _QueuedSuggestion(
        sequence=next(self._sequence),
        key=key,
        target_key=target_key,
        project_id=project_id,
        chapter_id=chapter_id,
        paragraph=paragraph,
        perspective_id=perspective_id,
        trigger=trigger,
        future=future,
      )
      task = asyncio.create_task(
        self._run_item(item),
        name=f"suggestion-request-{item.sequence}",
      )
      item.task = task
      future.add_done_callback(
        lambda done, queued=item: self._cancel_if_future_cancelled(queued, done)
      )
      self._pending_by_key[key] = item
      if trigger == SuggestionRequestTrigger.auto:
        self._latest_auto_by_target[target_key] = item
      return future

  def _cancel_if_future_cancelled(
    self,
    item: _QueuedSuggestion,
    future: asyncio.Future[list[SuggestionCard]],
  ) -> None:
    if not future.cancelled():
      return
    item.cancelled = True
    if item.task and not item.task.done():
      item.task.cancel()
    asyncio.create_task(self._cleanup(item))

  async def _run_item(self, item: _QueuedSuggestion) -> None:
    try:
      await asyncio.sleep(0)
      async with self._lock:
        if item.cancelled or item.future.done():
          return
        item.started = True

      try:
        with model_request_priority(_model_priority(item.trigger)):
          suggestions = await self._suggestion_service.suggest_for_perspective(
            item.project_id,
            item.chapter_id,
            item.paragraph,
            item.perspective_id,
          )
      except asyncio.CancelledError:
        if not item.future.done():
          item.future.set_result([])
      except Exception as exc:
        if not item.future.done():
          item.future.set_exception(exc)
      else:
        if not item.future.done():
          item.future.set_result(suggestions)
    finally:
      await self._cleanup(item)

  async def _cleanup(self, item: _QueuedSuggestion) -> None:
    async with self._lock:
      if self._pending_by_key.get(item.key) is item:
        self._pending_by_key.pop(item.key, None)
      if self._latest_auto_by_target.get(item.target_key) is item:
        self._latest_auto_by_target.pop(item.target_key, None)


def _model_priority(trigger: SuggestionRequestTrigger) -> ModelRequestPriority:
  return {
    SuggestionRequestTrigger.manual: ModelRequestPriority.manual,
    SuggestionRequestTrigger.batch: ModelRequestPriority.batch,
    SuggestionRequestTrigger.auto: ModelRequestPriority.auto,
  }[trigger]


def _target_key(project_id: str, chapter_id: str, perspective_id: str) -> str:
  return f"{project_id}:{chapter_id}:{perspective_id}"


def _request_key(
  project_id: str,
  chapter_id: str,
  paragraph: str,
  perspective_id: str,
) -> str:
  paragraph_hash = sha1(paragraph.encode("utf-8")).hexdigest()
  return f"{_target_key(project_id, chapter_id, perspective_id)}:{paragraph_hash}"
