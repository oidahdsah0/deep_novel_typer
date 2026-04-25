from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from app.Utils.db import AsyncDatabase
from app.Utils.locks import AsyncLockRegistry
from app.Services.debug_readable import build_debug_readable_view
from app.Schemas.common import ModelRequestKind
from app.Schemas.debug import DebugRequestLog, DebugSnapshot, DebugTokenUsage
from app.Schemas.prompt_context import PromptContextPack

_MAX_REQUEST_LOGS = 50
_REQUEST_LOG_CLEANUP_INTERVAL = 5


@dataclass(frozen=True)
class LLMDebugContext:
  project_id: str | None
  request_type: str
  api_config_id: str | None = None
  provider: str = ""
  model: str = ""


@dataclass(frozen=True)
class EmbeddingDebugContext:
  project_id: str | None
  request_type: str
  api_config_id: str | None = None
  provider: str = ""
  model: str = ""
  tool_type: str = ""
  resource_type: str = ""
  resource_id: str = ""
  run_id: str = ""
  algorithm: str = ""
  batch_label: str = ""


class DebugLogService:
  def __init__(self, db: AsyncDatabase, locks: AsyncLockRegistry) -> None:
    self._db = db
    self._locks = locks
    self._writes_since_cleanup: dict[str, int] = {}

  async def snapshot(self, project_id: str | None = None) -> DebugSnapshot:
    return DebugSnapshot(
      token_usage=await self.token_usage(project_id),
      request_logs=await self.request_logs(project_id=project_id, limit=_MAX_REQUEST_LOGS),
    )

  async def token_usage(self, project_id: str | None = None) -> DebugTokenUsage:
    today = _today()
    return DebugTokenUsage(
      today=await self._sum_tokens(today, today, project_id),
      last_7_days=await self._sum_tokens(_date_days_ago(6), today, project_id),
      last_30_days=await self._sum_tokens(_date_days_ago(29), today, project_id),
      total=await self._sum_tokens(None, None, project_id),
      unknown_usage_requests=await self._sum_unknown_usage(project_id),
    )

  async def request_logs(
    self, *, project_id: str | None = None, limit: int = _MAX_REQUEST_LOGS
  ) -> list[DebugRequestLog]:
    limit = max(1, min(limit, _MAX_REQUEST_LOGS))
    where = "WHERE project_id = ?" if project_id else ""
    params: tuple[object, ...] = (project_id, limit) if project_id else (limit,)
    rows = await self._db.fetch_all(
      f"""
      SELECT id, project_id, model_kind, request_type, api_config_id, provider,
             model, status, created_at, request_body_json, response_body_json, error_message,
             prompt_tokens, completion_tokens, total_tokens, duration_ms,
             context_pack_json
      FROM model_request_logs
      {where}
      ORDER BY created_at DESC, id DESC
      LIMIT ?
      """,
      params,
    )
    return [_log_from_row(row) for row in rows]

  async def record_llm_request(
    self,
    *,
    context: LLMDebugContext,
    request_body: dict[str, Any],
    response_body: dict[str, Any],
    status: str,
    error_message: str | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    duration_ms: int | None = None,
    context_pack: PromptContextPack | None = None,
  ) -> None:
    await self._record_model_request(
      model_kind="llm",
      project_id=context.project_id,
      request_type=context.request_type,
      api_config_id=context.api_config_id,
      provider=context.provider,
      model=context.model,
      request_body=request_body,
      response_body=response_body,
      status=status,
      error_message=error_message,
      prompt_tokens=prompt_tokens,
      completion_tokens=completion_tokens,
      total_tokens=total_tokens,
      duration_ms=duration_ms,
      context_pack=context_pack,
    )

  async def record_embedding_request(
    self,
    *,
    context: EmbeddingDebugContext,
    request_body: dict[str, Any],
    response_body: dict[str, Any],
    status: str,
    error_message: str | None = None,
    prompt_tokens: int | None = None,
    total_tokens: int | None = None,
    duration_ms: int | None = None,
  ) -> None:
    await self._record_model_request(
      model_kind="embedding",
      project_id=context.project_id,
      request_type=context.request_type,
      api_config_id=context.api_config_id,
      provider=context.provider,
      model=context.model,
      request_body=request_body,
      response_body=response_body,
      status=status,
      error_message=error_message,
      prompt_tokens=prompt_tokens,
      completion_tokens=0 if total_tokens is not None else None,
      total_tokens=total_tokens,
      duration_ms=duration_ms,
      context_pack=None,
    )

  async def _record_model_request(
    self,
    *,
    model_kind: ModelRequestKind,
    project_id: str | None,
    request_type: str,
    api_config_id: str | None,
    provider: str,
    model: str,
    request_body: dict[str, Any],
    response_body: dict[str, Any],
    status: str,
    error_message: str | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    duration_ms: int | None = None,
    context_pack: PromptContextPack | None = None,
  ) -> None:
    now = _now()
    token_date = _today()
    prompt_value = max(0, prompt_tokens or 0)
    completion_value = max(0, completion_tokens or 0)
    total_value = max(0, total_tokens or 0)
    unknown_usage = 1 if total_tokens is None else 0
    project_key = project_id or ""
    provider_value = provider or ""
    model_value = model or ""

    cleanup_key = project_id or "__global__"
    async with self._locks.get(f"debug-model-logs:{cleanup_key}"):
      should_cleanup = self._should_cleanup_request_logs(cleanup_key)
      async with self._db.transaction() as conn:
        await conn.execute(
          """
          INSERT INTO model_request_logs (
            id, project_id, model_kind, request_type, api_config_id, provider, model, status,
            created_at, request_body_json, response_body_json, error_message,
            prompt_tokens, completion_tokens, total_tokens, duration_ms, context_pack_json
          )
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          """,
          (
            uuid4().hex,
            project_id,
            model_kind,
            request_type,
            api_config_id,
            provider_value,
            model_value,
            status,
            now,
            _json_dumps(request_body),
            _json_dumps(response_body),
            error_message,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            duration_ms,
            _json_dumps(context_pack.model_dump(mode="json")) if context_pack else "{}",
          ),
        )
        await conn.execute(
          """
          INSERT INTO model_token_usage_daily (
            date, project_id, model_kind, request_type, provider, model,
            prompt_tokens, completion_tokens, total_tokens, request_count,
            unknown_usage_count, updated_at
          )
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
          ON CONFLICT(date, project_id, model_kind, request_type, provider, model) DO UPDATE SET
            prompt_tokens = prompt_tokens + excluded.prompt_tokens,
            completion_tokens = completion_tokens + excluded.completion_tokens,
            total_tokens = total_tokens + excluded.total_tokens,
            request_count = request_count + 1,
            unknown_usage_count = unknown_usage_count + excluded.unknown_usage_count,
            updated_at = excluded.updated_at
          """,
          (
            token_date,
            project_key,
            model_kind,
            request_type,
            provider_value,
            model_value,
            prompt_value,
            completion_value,
            total_value,
            unknown_usage,
            now,
          ),
        )
        if should_cleanup:
          await self._cleanup_request_logs(conn)

  async def clear_token_usage(self, project_id: str | None = None) -> None:
    if project_id:
      await self._db.execute("DELETE FROM model_token_usage_daily WHERE project_id = ?", (project_id,))
      return
    await self._db.execute("DELETE FROM model_token_usage_daily")

  async def clear_request_logs(self, project_id: str | None = None) -> None:
    if project_id:
      await self._db.execute("DELETE FROM model_request_logs WHERE project_id = ?", (project_id,))
      return
    await self._db.execute("DELETE FROM model_request_logs")

  async def clear_all(self, project_id: str | None = None) -> None:
    await self.clear_request_logs(project_id)
    await self.clear_token_usage(project_id)

  def _should_cleanup_request_logs(self, cleanup_key: str) -> bool:
    count = self._writes_since_cleanup.get(cleanup_key, 0) + 1
    if count < _REQUEST_LOG_CLEANUP_INTERVAL:
      self._writes_since_cleanup[cleanup_key] = count
      return False
    self._writes_since_cleanup[cleanup_key] = 0
    return True

  async def _cleanup_request_logs(self, conn) -> None:
    await conn.execute(
      """
      DELETE FROM model_request_logs
      WHERE id NOT IN (
        SELECT id
        FROM model_request_logs
        ORDER BY created_at DESC, id DESC
        LIMIT ?
      )
      """,
      (_MAX_REQUEST_LOGS,),
    )

  async def _sum_tokens(
    self, start_date: str | None, end_date: str | None, project_id: str | None
  ) -> int:
    clauses: list[str] = []
    params: list[object] = []
    if project_id:
      clauses.append("project_id = ?")
      params.append(project_id)
    if start_date and end_date:
      clauses.append("date BETWEEN ? AND ?")
      params.extend([start_date, end_date])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    row = await self._db.fetch_one(
      f"SELECT COALESCE(SUM(total_tokens), 0) AS total FROM model_token_usage_daily {where}",
      tuple(params),
    )
    return int(row["total"]) if row else 0

  async def _sum_unknown_usage(self, project_id: str | None) -> int:
    where = "WHERE project_id = ?" if project_id else ""
    params: tuple[object, ...] = (project_id,) if project_id else ()
    row = await self._db.fetch_one(
      f"""
      SELECT COALESCE(SUM(unknown_usage_count), 0) AS total
      FROM model_token_usage_daily
      {where}
      """,
      params,
    )
    return int(row["total"]) if row else 0


def _log_from_row(row: dict[str, object]) -> DebugRequestLog:
  request_body = _json_loads(row["request_body_json"])
  response_body = _json_loads(row["response_body_json"])
  context_pack = _json_loads(row.get("context_pack_json"))
  error_message = str(row["error_message"]) if row["error_message"] else None
  model_kind = str(row.get("model_kind") or "llm")
  return DebugRequestLog(
    id=str(row["id"]),
    project_id=str(row["project_id"]) if row["project_id"] else None,
    model_kind=model_kind,  # type: ignore[arg-type]
    request_type=str(row["request_type"]),
    api_config_id=str(row["api_config_id"]) if row["api_config_id"] else None,
    provider=str(row["provider"] or ""),
    model=str(row["model"] or ""),
    status=str(row["status"]),  # type: ignore[arg-type]
    created_at=str(row["created_at"]),
    request_body=request_body,
    response_body=response_body,
    debug_readable=build_debug_readable_view(
      request_body=request_body,
      response_body=response_body,
      context_pack=context_pack,
      error_message=error_message,
      request_type=str(row.get("request_type") or ""),
      model_kind=model_kind,
    ),
    error_message=error_message,
    prompt_tokens=_optional_int(row["prompt_tokens"]),
    completion_tokens=_optional_int(row["completion_tokens"]),
    total_tokens=_optional_int(row["total_tokens"]),
    duration_ms=_optional_int(row["duration_ms"]),
  )


def _optional_int(value: object) -> int | None:
  return int(value) if value is not None else None


def _json_dumps(value: dict[str, Any]) -> str:
  return json.dumps(_json_safe(value), ensure_ascii=False)


def _json_loads(value: object) -> dict[str, Any]:
  try:
    payload = json.loads(str(value))
  except json.JSONDecodeError:
    return {}
  return payload if isinstance(payload, dict) else {}


def _json_safe(value: Any) -> Any:
  if value is None or isinstance(value, (str, int, float, bool)):
    return value
  if isinstance(value, dict):
    return {str(key): _json_safe(item) for key, item in value.items()}
  if isinstance(value, list):
    return [_json_safe(item) for item in value]
  return str(value)


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()


def _today() -> str:
  return datetime.now().astimezone().date().isoformat()


def _date_days_ago(days: int) -> str:
  return (datetime.now().astimezone().date() - timedelta(days=days)).isoformat()
