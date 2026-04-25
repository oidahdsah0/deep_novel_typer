from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.Schemas.common import DebugRequestStatus, ModelRequestKind
from app.Schemas.prompt_context import PromptContextPack


class DebugTokenUsage(BaseModel):
  today: int = 0
  last_7_days: int = 0
  last_30_days: int = 0
  total: int = 0
  unknown_usage_requests: int = 0


class DebugReadableMessage(BaseModel):
  role: str
  content: str


class DebugReadableView(BaseModel):
  system_messages: list[DebugReadableMessage] = Field(default_factory=list)
  user_messages: list[DebugReadableMessage] = Field(default_factory=list)
  request_options: dict[str, Any] = Field(default_factory=dict)
  context_pack: PromptContextPack | None = None
  context_budget: dict[str, Any] | None = None
  context_materials: list[dict[str, Any]] = Field(default_factory=list)
  raw_content: str | None = None
  parsed_payload: dict[str, Any] | None = None
  schema_error: str | None = None
  embedding_summary: dict[str, Any] = Field(default_factory=dict)


class DebugRequestLog(BaseModel):
  id: str
  project_id: str | None = None
  model_kind: ModelRequestKind = "llm"
  request_type: str
  api_config_id: str | None = None
  provider: str
  model: str
  status: DebugRequestStatus
  created_at: str
  request_body: dict[str, Any] = Field(default_factory=dict)
  response_body: dict[str, Any] = Field(default_factory=dict)
  debug_readable: DebugReadableView = Field(default_factory=DebugReadableView)
  error_message: str | None = None
  prompt_tokens: int | None = None
  completion_tokens: int | None = None
  total_tokens: int | None = None
  duration_ms: int | None = None


class DebugSnapshot(BaseModel):
  token_usage: DebugTokenUsage = Field(default_factory=DebugTokenUsage)
  request_logs: list[DebugRequestLog] = Field(default_factory=list)
