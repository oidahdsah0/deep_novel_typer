from __future__ import annotations

import json
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, Protocol

from app.Schemas.api_configs import APIConfigHealthCheckResult
from app.Services.api_configs.runtime import EffectiveAPIConfig, build_llm_overrides
from app.Services.model_request_queue_service import (
  ModelRequestPriority,
  ModelRequestQueueService,
)
from app.Utils.llm import LLMMessage, OpenAIChatClient
from app.Utils.openai_client_cache import get_cached_openai_client


class APIConfigHealthChecker(Protocol):
  async def check_llm(self, effective_config: EffectiveAPIConfig) -> APIConfigHealthCheckResult:
    ...

  async def check_embedding(
    self, effective_config: EffectiveAPIConfig
  ) -> APIConfigHealthCheckResult:
    ...


class OpenAIAPIConfigHealthChecker:
  def __init__(
    self,
    *,
    headers: dict[str, str],
    timeout_seconds: float,
    request_queue: ModelRequestQueueService | None = None,
  ) -> None:
    self._headers = headers
    self._timeout_seconds = timeout_seconds
    self._request_queue = request_queue or ModelRequestQueueService()
    self._owns_request_queue = request_queue is None

  async def check_llm(self, effective_config: EffectiveAPIConfig) -> APIConfigHealthCheckResult:
    config = effective_config.config
    cached_client = await get_cached_openai_client(
      api_key=effective_config.api_key or "unused",
      base_url=config.base_url,
      headers=self._headers,
      timeout_seconds=self._timeout_seconds,
    )
    client = OpenAIChatClient(
      api_key=effective_config.api_key,
      api_key_required=config.api_key_required,
      enabled=True,
      base_url=config.base_url,
      headers=self._headers,
      mode="non_stream",
      model=config.model,
      non_stream_request_options={},
      timeout_seconds=self._timeout_seconds,
      client=cached_client,
      close_client_on_shutdown=False,
    )
    messages = [
      LLMMessage(
        role="system",
        content="You are an API health-check responder. Return only a JSON object.",
      ),
      LLMMessage(role="user", content='Return exactly this JSON object: {"text":"ok"}'),
    ]
    start = perf_counter()
    try:
      response = await self._run_provider_request(
        "api_config_health_llm",
        lambda: client.complete_non_stream(
          messages,
          build_llm_overrides(effective_config),
        ),
        kind="llm",
        model=config.model,
      )
      latency_ms = _latency_ms(start)
      try:
        payload = json.loads(response.content)
      except json.JSONDecodeError:
        return health_result(
          effective_config,
          ok=False,
          latency_ms=latency_ms,
          json_mode_supported=False,
          error_code="invalid_json_response",
          error_message="模型返回内容不是合法 JSON object。",
        )
      if not isinstance(payload, dict):
        return health_result(
          effective_config,
          ok=False,
          latency_ms=latency_ms,
          json_mode_supported=False,
          error_code="invalid_json_response",
          error_message="模型返回的是 JSON，但不是 object。",
        )
      if not isinstance(payload.get("text"), str):
        return health_result(
          effective_config,
          ok=False,
          latency_ms=latency_ms,
          json_mode_supported=True,
          error_code="invalid_health_payload",
          error_message="模型返回了 JSON object，但没有按健康检查要求返回 text 字段。",
        )
      return health_result(
        effective_config,
        ok=True,
        latency_ms=latency_ms,
        json_mode_supported=True,
      )
    except Exception as exc:
      return health_result(
        effective_config,
        ok=False,
        latency_ms=_latency_ms(start),
        json_mode_supported=False if _looks_like_json_mode_error(exc) else None,
        error_code=_error_code(exc),
        error_message=_sanitize_error_message(exc, effective_config.api_key),
      )

  async def check_embedding(
    self, effective_config: EffectiveAPIConfig
  ) -> APIConfigHealthCheckResult:
    config = effective_config.config
    client = await get_cached_openai_client(
      api_key=effective_config.api_key or "unused",
      base_url=config.base_url,
      headers=self._headers,
      timeout_seconds=self._timeout_seconds,
    )
    request_body: dict[str, object] = {
      "model": config.model,
      "input": "ping",
    }
    if config.dimensions is not None:
      request_body["dimensions"] = config.dimensions
    start = perf_counter()
    try:
      response = await self._run_provider_request(
        "api_config_health_embedding",
        lambda: client.embeddings.create(**request_body),
        kind="embedding",
        model=config.model,
      )
      latency_ms = _latency_ms(start)
      embedding = _embedding_from_response(response)
      if not embedding:
        return health_result(
          effective_config,
          ok=False,
          latency_ms=latency_ms,
          error_code="invalid_embedding_response",
          error_message="Embedding 接口没有返回有效向量。",
        )
      actual_dimensions = len(embedding)
      if config.dimensions is not None and actual_dimensions != config.dimensions:
        return health_result(
          effective_config,
          ok=False,
          latency_ms=latency_ms,
          embedding_dimensions=actual_dimensions,
          error_code="embedding_dimensions_mismatch",
          error_message=(
            f"Embedding 实际维度为 {actual_dimensions}，与配置的 {config.dimensions} 不一致。"
          ),
        )
      return health_result(
        effective_config,
        ok=True,
        latency_ms=latency_ms,
        embedding_dimensions=actual_dimensions,
      )
    except Exception as exc:
      return health_result(
        effective_config,
        ok=False,
        latency_ms=_latency_ms(start),
        error_code=_error_code(exc),
        error_message=_sanitize_error_message(exc, effective_config.api_key),
      )

  async def _run_provider_request(self, label: str, factory, *, kind: str, model: str):
    return await self._request_queue.run(
      label,
      factory,
      kind=kind,
      model=model,
      priority=ModelRequestPriority.manual,
    )

  async def shutdown(self) -> None:
    if self._owns_request_queue:
      await self._request_queue.shutdown()


def is_configured(effective_config: EffectiveAPIConfig) -> bool:
  config = effective_config.config
  has_auth = bool(effective_config.api_key) or not config.api_key_required
  return has_auth and bool(config.base_url and config.model)


def health_result(
  effective_config: EffectiveAPIConfig,
  *,
  ok: bool,
  latency_ms: int | None = None,
  json_mode_supported: bool | None = None,
  embedding_dimensions: int | None = None,
  error_code: str | None = None,
  error_message: str | None = None,
) -> APIConfigHealthCheckResult:
  config = effective_config.config
  return APIConfigHealthCheckResult(
    ok=ok,
    config_id=config.id,
    kind=config.kind,
    provider=config.provider,
    model=config.model,
    mode=config.mode,
    latency_ms=latency_ms,
    checked_at=_now(),
    json_mode_supported=json_mode_supported,
    embedding_dimensions=embedding_dimensions,
    error_code=error_code,
    error_message=error_message,
  )


def _latency_ms(start: float) -> int:
  return max(0, round((perf_counter() - start) * 1000))


def _embedding_from_response(response: Any) -> list[float]:
  data = _get_field(response, "data") or []
  if not data:
    return []
  first = data[0]
  embedding = _get_field(first, "embedding")
  if not isinstance(embedding, list):
    return []
  result: list[float] = []
  for item in embedding:
    if not isinstance(item, (int, float)):
      return []
    result.append(float(item))
  return result


def _get_field(value: Any, key: str) -> Any:
  if isinstance(value, dict):
    return value.get(key)
  return getattr(value, key, None)


def _looks_like_json_mode_error(exc: Exception) -> bool:
  message = str(exc).lower()
  return (
    ("response_format" in message or "json_object" in message or "json mode" in message)
    and (
      "not support" in message
      or "unsupported" in message
      or "invalid" in message
      or "不支持" in message
    )
  )


def _error_code(exc: Exception) -> str:
  code = getattr(exc, "code", None)
  if code:
    return str(code)
  status_code = getattr(exc, "status_code", None)
  if status_code:
    return f"http_{status_code}"
  if _looks_like_json_mode_error(exc):
    return "json_mode_unsupported"
  return "request_failed"


def _sanitize_error_message(exc: Exception, api_key: str) -> str:
  message = str(exc) or exc.__class__.__name__
  if api_key:
    message = message.replace(api_key, "[redacted]")
  if len(message) > 500:
    message = f"{message[:497]}..."
  return message


def _now() -> str:
  return datetime.now(tz=UTC).isoformat()
