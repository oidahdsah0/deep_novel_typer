from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


ModelQueueRequestKind = Literal["llm", "embedding"]
ModelQueueRequestStatus = Literal["queued", "running"]
ModelQueueRequestPriority = Literal["manual", "batch", "auto"]


class ModelQueueItem(BaseModel):
  id: str
  kind: ModelQueueRequestKind
  label: str
  status: ModelQueueRequestStatus
  priority: ModelQueueRequestPriority
  model: str | None = None
  queued_at: str
  started_at: str | None = None


class ModelQueueSnapshot(BaseModel):
  worker_count: int
  queued_count: int
  running_count: int
  items: list[ModelQueueItem]
