from app.Utils.config import _load_llm_settings


def _clear_llm_override_env(monkeypatch) -> None:
  for name in [
    "NOVEL_TYPER_LLM_API_KEY",
    "NOVEL_TYPER_LLM_API_KEY_REQUIRED",
    "NOVEL_TYPER_LLM_BASE_URL",
    "NOVEL_TYPER_LLM_ENABLED",
    "NOVEL_TYPER_LLM_MAX_TOKENS",
    "NOVEL_TYPER_LLM_MODE",
    "NOVEL_TYPER_LLM_MODEL",
    "NOVEL_TYPER_LLM_TEMPERATURE",
    "NOVEL_TYPER_LLM_TIMEOUT_SECONDS",
    "NOVEL_TYPER_LLM_TOP_K",
    "NOVEL_TYPER_LLM_TOP_P",
  ]:
    monkeypatch.delenv(name, raising=False)


def test_llm_settings_load_deepseek_yaml_once_from_config_path(tmp_path, monkeypatch) -> None:
  _clear_llm_override_env(monkeypatch)
  config_path = tmp_path / "llm.yaml"
  config_path.write_text(
    """
enabled: true
api_key_env: CUSTOM_DEEPSEEK_KEY
base_url: https://api.deepseek.com
model: deepseek-v4-pro
timeout_seconds: 12
headers:
  Accept: application/json
request:
  thinking:
    type: enabled
  reasoning_effort: high
  temperature: 0.7
  max_tokens: 2048
  top_p: 0.8
  top_k: 50
""",
    encoding="utf-8",
  )
  monkeypatch.setenv("NOVEL_TYPER_LLM_CONFIG", str(config_path))
  monkeypatch.setenv("CUSTOM_DEEPSEEK_KEY", "secret-token")

  settings = _load_llm_settings()

  assert settings.enabled is True
  assert settings.api_key == "secret-token"
  assert settings.base_url == "https://api.deepseek.com"
  assert settings.model == "deepseek-v4-pro"
  assert settings.timeout_seconds == 12
  assert settings.mode == "non_stream"
  assert settings.request_options["thinking"] == {"type": "enabled"}
  assert settings.request_options["reasoning_effort"] == "high"
  assert settings.request_options["temperature"] == 0.7
  assert settings.request_options["max_tokens"] == 2048
  assert settings.request_options["top_p"] == 0.8
  assert settings.request_options["top_k"] == 50
  assert settings.request_options["response_format"] == {"type": "json_object"}
  assert settings.non_stream_request_options["stream"] is False


def test_llm_settings_env_overrides_yaml_request_fields(tmp_path, monkeypatch) -> None:
  _clear_llm_override_env(monkeypatch)
  config_path = tmp_path / "llm.yaml"
  config_path.write_text(
    """
enabled: false
api_key_required: false
base_url: https://yaml.example.test
model: yaml-model
request:
  common:
    temperature: 0.1
    max_tokens: 128
    custom_deepseek_param: value
""",
    encoding="utf-8",
  )
  monkeypatch.setenv("NOVEL_TYPER_LLM_CONFIG", str(config_path))
  monkeypatch.setenv("NOVEL_TYPER_LLM_ENABLED", "true")
  monkeypatch.setenv("NOVEL_TYPER_LLM_BASE_URL", "https://env.example.test")
  monkeypatch.setenv("NOVEL_TYPER_LLM_MODE", "stream")
  monkeypatch.setenv("NOVEL_TYPER_LLM_MODEL", "env-model")
  monkeypatch.setenv("NOVEL_TYPER_LLM_TEMPERATURE", "0.9")
  monkeypatch.setenv("NOVEL_TYPER_LLM_MAX_TOKENS", "512")
  monkeypatch.setenv("NOVEL_TYPER_LLM_TOP_P", "0.75")
  monkeypatch.setenv("NOVEL_TYPER_LLM_TOP_K", "80")

  settings = _load_llm_settings()

  assert settings.enabled is True
  assert settings.api_key_required is False
  assert settings.base_url == "https://env.example.test"
  assert settings.mode == "non_stream"
  assert settings.model == "env-model"
  assert settings.request_options["temperature"] == 0.9
  assert settings.request_options["max_tokens"] == 512
  assert settings.request_options["top_p"] == 0.75
  assert settings.request_options["top_k"] == 80
  assert settings.request_options["custom_deepseek_param"] == "value"
  assert settings.non_stream_request_options["stream"] is False
