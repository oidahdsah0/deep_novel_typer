from __future__ import annotations

from dataclasses import dataclass

from app.Schemas.api_configs import APIConfig
from app.Utils.config import LLM_MODE_NON_STREAM
from app.Utils.llm import LLMRequestOverrides


@dataclass(frozen=True)
class EffectiveAPIConfig:
  config: APIConfig
  api_key: str


def build_llm_overrides(
  effective_config: EffectiveAPIConfig,
  *,
  temperature_override: float | None = None,
) -> LLMRequestOverrides:
  settings = effective_config.config
  request_options: dict[str, object] = {
    "max_tokens": settings.max_tokens,
    "response_format": {"type": "json_object"},
  }
  if settings.top_p is not None:
    request_options["top_p"] = settings.top_p
  if settings.top_k is not None:
    request_options["top_k"] = settings.top_k

  if settings.provider == "deepseek" and settings.thinking_enabled:
    request_options["thinking"] = {"type": "enabled"}
    request_options["reasoning_effort"] = settings.reasoning_effort
    request_options["temperature"] = None
  elif settings.provider == "siliconflow" and settings.thinking_enabled:
    request_options["enable_thinking"] = True
    request_options["temperature"] = None
  elif settings.provider == "deepseek":
    request_options["thinking"] = {"type": "disabled"}
    request_options["reasoning_effort"] = None
    request_options["temperature"] = settings.temperature
  elif settings.provider == "siliconflow":
    request_options["enable_thinking"] = False
    request_options["temperature"] = settings.temperature
  elif settings.temperature is not None:
    request_options["temperature"] = settings.temperature

  if temperature_override is not None:
    request_options["temperature"] = temperature_override

  return LLMRequestOverrides(
    api_key=effective_config.api_key,
    api_key_required=settings.api_key_required,
    base_url=settings.base_url,
    mode=LLM_MODE_NON_STREAM,
    model=settings.model,
    request_options=request_options,
  )
