from types import SimpleNamespace

from app.Utils.llm import (
  LLMMessage,
  LLMRequestOverrides,
  OpenAIChatClient,
  build_chat_completion_request_snapshot,
  _stream_event_from_chunk,
)


class FakeChunk(SimpleNamespace):
  def model_dump(self) -> dict:
    payload = {
      "model": self.model,
      "choices": [],
    }
    if self.choices:
      payload["choices"].append(
        {
          "delta": {
            "reasoning_content": self.choices[0].delta.reasoning_content,
            "content": self.choices[0].delta.content,
          },
          "finish_reason": self.choices[0].finish_reason,
        }
      )
    if hasattr(self, "usage"):
      payload["usage"] = self.usage
    return payload


def test_openai_chat_client_builds_openai_kwargs_with_deepseek_extra_body() -> None:
  client = OpenAIChatClient(
    api_key="secret-token",
    api_key_required=True,
    enabled=True,
    base_url="https://api.deepseek.com",
    headers={"Accept": "application/json"},
    mode="non_stream",
    model="deepseek-v4-pro",
    non_stream_request_options={
      "thinking": {"type": "enabled"},
      "reasoning_effort": "high",
      "max_tokens": 4096,
      "top_p": 0.95,
      "top_k": 50,
      "response_format": {"type": "json_object"},
      "stream": False,
      "custom_deepseek_param": "non-stream-value",
    },
    timeout_seconds=60,
  )
  messages = [LLMMessage(role="user", content="Hi")]

  non_stream_kwargs = client._build_create_kwargs(messages, stream=False)
  assert non_stream_kwargs["model"] == "deepseek-v4-pro"
  assert non_stream_kwargs["messages"] == [{"role": "user", "content": "Hi"}]
  assert non_stream_kwargs["stream"] is False
  assert non_stream_kwargs["reasoning_effort"] == "high"
  assert non_stream_kwargs["max_tokens"] == 4096
  assert non_stream_kwargs["top_p"] == 0.95
  assert non_stream_kwargs["response_format"] == {"type": "json_object"}
  assert non_stream_kwargs["extra_body"] == {
    "thinking": {"type": "enabled"},
    "top_k": 50,
    "custom_deepseek_param": "non-stream-value",
  }


def test_openai_chat_client_applies_database_request_overrides() -> None:
  client = OpenAIChatClient(
    api_key="secret-token",
    api_key_required=True,
    enabled=True,
    base_url="https://api.deepseek.com",
    headers={"Accept": "application/json"},
    mode="non_stream",
    model="yaml-model",
    non_stream_request_options={
      "thinking": {"type": "enabled"},
      "reasoning_effort": "high",
      "max_tokens": 4096,
      "response_format": {"type": "json_object"},
      "stream": False,
      "temperature": 1,
    },
    timeout_seconds=60,
  )
  overrides = LLMRequestOverrides(
    mode="non_stream",
    model="db-model",
    request_options={
      "thinking": None,
      "reasoning_effort": None,
      "max_tokens": 1024,
      "temperature": 0.8,
      "top_p": 0.9,
      "top_k": 40,
      "response_format": {"type": "json_object"},
    },
  )

  create_kwargs = client._build_create_kwargs(
    [LLMMessage(role="user", content="Hi")], stream=True, overrides=overrides
  )

  assert create_kwargs["model"] == "db-model"
  assert create_kwargs["stream"] is False
  assert create_kwargs["max_tokens"] == 1024
  assert create_kwargs["temperature"] == 0.8
  assert create_kwargs["top_p"] == 0.9
  assert create_kwargs["response_format"] == {"type": "json_object"}
  assert "reasoning_effort" not in create_kwargs
  assert create_kwargs["extra_body"] == {"top_k": 40}


def test_openai_chat_client_configuration_uses_database_api_key_and_endpoint() -> None:
  client = OpenAIChatClient(
    api_key="",
    api_key_required=True,
    enabled=True,
    base_url="https://yaml.example.test",
    headers={"Accept": "application/json"},
    mode="non_stream",
    model="yaml-model",
    non_stream_request_options={
      "max_tokens": 4096,
      "response_format": {"type": "json_object"},
      "stream": False,
    },
    timeout_seconds=60,
  )

  assert client.is_configured is False
  assert client.is_configured_for(
    LLMRequestOverrides(
      api_key="db-secret",
      base_url="https://db.example.test",
      model="db-model",
    )
  )


def test_openai_chat_client_empty_api_config_key_does_not_fallback_to_global_key() -> None:
  client = OpenAIChatClient(
    api_key="yaml-secret",
    api_key_required=True,
    enabled=True,
    base_url="https://yaml.example.test",
    headers={"Accept": "application/json"},
    mode="non_stream",
    model="yaml-model",
    non_stream_request_options={
      "max_tokens": 4096,
      "response_format": {"type": "json_object"},
      "stream": False,
    },
    timeout_seconds=60,
  )

  assert client.is_configured is True
  assert not client.is_configured_for(
    LLMRequestOverrides(
      api_key="",
      base_url="https://db.example.test",
      model="db-model",
    )
  )


def test_openai_chat_client_allows_local_api_configs_without_key() -> None:
  client = OpenAIChatClient(
    api_key="",
    api_key_required=True,
    enabled=True,
    base_url="https://yaml.example.test",
    headers={"Accept": "application/json"},
    mode="non_stream",
    model="yaml-model",
    non_stream_request_options={
      "max_tokens": 4096,
      "response_format": {"type": "json_object"},
      "stream": False,
    },
    timeout_seconds=60,
  )

  assert client.is_configured_for(
    LLMRequestOverrides(
      api_key="",
      api_key_required=False,
      base_url="http://127.0.0.1:11434/v1",
      model="llama3.1",
    )
  )


def test_openai_stream_event_parser_reads_content_and_reasoning_delta() -> None:
  chunk = FakeChunk(
    model="deepseek-v4-pro",
    choices=[
      SimpleNamespace(
        delta=SimpleNamespace(
          content="正文",
          reasoning_content="想法",
          model_extra={},
        ),
        finish_reason=None,
      )
    ],
  )

  event = _stream_event_from_chunk(chunk)

  assert event.model == "deepseek-v4-pro"
  assert event.reasoning_delta == "想法"
  assert event.content_delta == "正文"
  assert event.finish_reason is None


def test_openai_stream_event_parser_reads_usage_chunk() -> None:
  chunk = FakeChunk(
    model="deepseek-v4-pro",
    choices=[],
    usage=SimpleNamespace(
      prompt_tokens=11,
      completion_tokens=7,
      total_tokens=18,
    ),
  )

  event = _stream_event_from_chunk(chunk)

  assert event.prompt_tokens == 11
  assert event.completion_tokens == 7
  assert event.total_tokens == 18


def test_stream_request_snapshot_omits_json_response_format() -> None:
  snapshot = build_chat_completion_request_snapshot(
    [LLMMessage(role="user", content="Hi")],
    LLMRequestOverrides(
      model="chat-model",
      request_options={
        "max_tokens": 1024,
        "top_k": 40,
        "response_format": {"type": "json_object"},
      },
    ),
    stream=True,
  )

  assert snapshot["model"] == "chat-model"
  assert snapshot["stream"] is True
  assert snapshot["stream_options"] == {"include_usage": True}
  assert "response_format" not in snapshot
  assert snapshot["extra_body"] == {"top_k": 40}
