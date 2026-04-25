from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.Schemas.common import (
  APIConfigKind,
  APIProtocol,
  APIProvider,
  LLMMode,
  LLMReasoningEffort,
)

API_CONFIG_MIN_TOKENS = 256
API_CONFIG_MAX_TOKENS = 10_000_000
API_CONFIG_MIN_CONTEXT_WINDOW_TOKENS = 1_024
API_CONFIG_MAX_CONTEXT_WINDOW_TOKENS = 10_000_000
API_CONFIG_DEFAULT_CONTEXT_WINDOW_TOKENS = 1_000_000


class APIConfig(BaseModel):
  id: str
  name: str
  provider: APIProvider = "deepseek"
  kind: APIConfigKind = "llm"
  protocol: APIProtocol = "openai_compatible"
  base_url: str = Field(min_length=1, max_length=240)
  api_key_required: bool = True
  api_key_configured: bool = False
  mode: LLMMode = "non_stream"
  model: str = Field(min_length=1, max_length=120)
  thinking_enabled: bool = True
  reasoning_effort: LLMReasoningEffort = "high"
  max_tokens: int = Field(
    default=4096,
    ge=API_CONFIG_MIN_TOKENS,
    le=API_CONFIG_MAX_TOKENS,
  )
  context_window_tokens: int = Field(
    default=API_CONFIG_DEFAULT_CONTEXT_WINDOW_TOKENS,
    ge=API_CONFIG_MIN_CONTEXT_WINDOW_TOKENS,
    le=API_CONFIG_MAX_CONTEXT_WINDOW_TOKENS,
  )
  temperature: float | None = Field(default=None, ge=0, le=2)
  top_p: float | None = Field(default=None, ge=0, le=1)
  top_k: int | None = Field(default=None, ge=1, le=1000)
  dimensions: int | None = Field(default=None, ge=1, le=32768)
  is_default: bool = False
  created_at: str | None = None
  updated_at: str | None = None


class APIConfigTemplate(BaseModel):
  provider: APIProvider
  provider_label: str
  kind: APIConfigKind
  protocol: APIProtocol = "openai_compatible"
  name: str
  base_url: str
  model: str
  api_key_required: bool = True
  mode: LLMMode = "non_stream"
  thinking_enabled: bool = False
  reasoning_effort: LLMReasoningEffort = "high"
  max_tokens: int = Field(
    default=4096,
    ge=API_CONFIG_MIN_TOKENS,
    le=API_CONFIG_MAX_TOKENS,
  )
  context_window_tokens: int = Field(
    default=API_CONFIG_DEFAULT_CONTEXT_WINDOW_TOKENS,
    ge=API_CONFIG_MIN_CONTEXT_WINDOW_TOKENS,
    le=API_CONFIG_MAX_CONTEXT_WINDOW_TOKENS,
  )
  temperature: float | None = Field(default=None, ge=0, le=2)
  top_p: float | None = Field(default=None, ge=0, le=1)
  top_k: int | None = Field(default=None, ge=1, le=1000)
  dimensions: int | None = Field(default=None, ge=1, le=32768)
  supports_streaming: bool = False
  supports_thinking: bool = False
  supports_embeddings: bool = False


class APIConfigHealthCheckResult(BaseModel):
  ok: bool
  config_id: str
  kind: APIConfigKind
  provider: APIProvider
  model: str
  mode: LLMMode = "non_stream"
  latency_ms: int | None = None
  checked_at: str
  json_mode_supported: bool | None = None
  embedding_dimensions: int | None = None
  error_code: str | None = None
  error_message: str | None = None


class CreateAPIConfigRequest(BaseModel):
  name: str = Field(min_length=1, max_length=80)
  provider: APIProvider = "deepseek"
  kind: APIConfigKind = "llm"
  protocol: APIProtocol = "openai_compatible"
  api_key: str | None = Field(default=None, max_length=500)
  api_key_required: bool = True
  base_url: str = Field(min_length=1, max_length=240)
  mode: LLMMode = "non_stream"
  model: str = Field(min_length=1, max_length=120)
  thinking_enabled: bool = True
  reasoning_effort: LLMReasoningEffort = "high"
  max_tokens: int = Field(
    default=4096,
    ge=API_CONFIG_MIN_TOKENS,
    le=API_CONFIG_MAX_TOKENS,
  )
  context_window_tokens: int = Field(
    default=API_CONFIG_DEFAULT_CONTEXT_WINDOW_TOKENS,
    ge=API_CONFIG_MIN_CONTEXT_WINDOW_TOKENS,
    le=API_CONFIG_MAX_CONTEXT_WINDOW_TOKENS,
  )
  temperature: float | None = Field(default=None, ge=0, le=2)
  top_p: float | None = Field(default=None, ge=0, le=1)
  top_k: int | None = Field(default=None, ge=1, le=1000)
  dimensions: int | None = Field(default=None, ge=1, le=32768)
  is_default: bool = False

  @field_validator("name", "api_key", "base_url", "model", mode="before")
  @classmethod
  def strip_string_fields(cls, value: object) -> object:
    if isinstance(value, str):
      return value.strip()
    return value


class UpdateAPIConfigRequest(CreateAPIConfigRequest):
  clear_api_key: bool = False
