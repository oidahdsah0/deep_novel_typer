from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace

import pytest

import app.Services.embeddings.chroma_store as chroma_store_module
from app.Schemas.api_configs import APIConfig
from app.Services.api_configs.health import OpenAIAPIConfigHealthChecker
from app.Services.api_configs.runtime import EffectiveAPIConfig
from app.Services.embeddings.chroma_store import ChromaEmbeddingStore
from app.Services.embeddings.model_runtime import OpenAIEmbeddingRuntime
from app.Services.model_request_queue_service import ModelRequestPriority
from app.Utils import openai_client_cache
from app.Utils.openai_client_cache import close_cached_openai_clients


class ImmediateQueue:
  def __init__(self) -> None:
    self.calls = []

  async def run(self, label, factory, *, kind, model, priority):
    self.calls.append((label, kind, model, priority))
    return await factory()


class FakeOpenAI:
  instances: list["FakeOpenAI"] = []

  def __init__(self, *, api_key, base_url, default_headers, timeout):
    self.api_key = api_key
    self.base_url = base_url
    self.default_headers = default_headers
    self.timeout = timeout
    self.embedding_requests = []
    self.chat_requests = []
    self.closed = False
    self.embeddings = _FakeEmbeddings(self)
    self.chat = SimpleNamespace(completions=_FakeChatCompletions(self))
    self.instances.append(self)

  def with_options(self, **kwargs):
    raise AssertionError(f"cached health checks should not clone clients: {kwargs}")

  async def close(self) -> None:
    self.closed = True


class _FakeEmbeddings:
  def __init__(self, client: FakeOpenAI) -> None:
    self._client = client

  async def create(self, **kwargs):
    self._client.embedding_requests.append(kwargs)
    inputs = kwargs["input"]
    texts = inputs if isinstance(inputs, list) else [inputs]
    return SimpleNamespace(
      data=[
        SimpleNamespace(index=index, embedding=[float(index), float(index + 1)])
        for index, _text in enumerate(texts)
      ],
      usage=SimpleNamespace(prompt_tokens=len(texts), total_tokens=len(texts) + 1),
    )


class _FakeChatCompletions:
  def __init__(self, client: FakeOpenAI) -> None:
    self._client = client

  async def create(self, **kwargs):
    self._client.chat_requests.append(kwargs)
    return {
      "choices": [
        {
          "message": {"content": '{"text":"ok"}'},
          "finish_reason": "stop",
        }
      ],
      "usage": {
        "prompt_tokens": 2,
        "completion_tokens": 1,
        "total_tokens": 3,
      },
      "model": kwargs["model"],
    }


@pytest.mark.asyncio
async def test_chroma_store_concurrent_initialization_creates_one_client(
  tmp_path, monkeypatch
) -> None:
  created_clients = []

  class FakeCollection:
    def get(self, ids, include):
      return {"ids": []}

  class FakeClient:
    def get_or_create_collection(self, collection_name):
      return FakeCollection()

  def persistent_client(*, path, settings):
    time.sleep(0.02)
    created_clients.append((path, settings))
    return FakeClient()

  monkeypatch.setattr(chroma_store_module.chromadb, "PersistentClient", persistent_client)
  store = ChromaEmbeddingStore(tmp_path / "chroma")

  await asyncio.gather(
    *(store.get_embeddings("test_collection", [f"id-{index}"]) for index in range(8))
  )

  assert len(created_clients) == 1


@pytest.mark.asyncio
async def test_embedding_runtime_reuses_cached_openai_client(monkeypatch) -> None:
  await close_cached_openai_clients()
  FakeOpenAI.instances = []
  monkeypatch.setattr(openai_client_cache, "AsyncOpenAI", FakeOpenAI)
  runtime = OpenAIEmbeddingRuntime(
    ImmediateQueue(),  # type: ignore[arg-type]
    timeout_seconds=3,
    headers={"X-Test": "yes"},
  )
  config = _effective_config(kind="embedding", model="text-embedding-test")
  changed_key = _effective_config(
    kind="embedding",
    api_key="next-secret",
    model="text-embedding-test",
  )

  try:
    await runtime.embed_texts(config, ["码头", "海雾"])
    await runtime.embed_texts(config, ["新词"])
    await runtime.embed_texts(changed_key, ["新 key"])
  finally:
    await close_cached_openai_clients()

  assert len(FakeOpenAI.instances) == 2
  assert [len(client.embedding_requests) for client in FakeOpenAI.instances] == [2, 1]
  assert FakeOpenAI.instances[0].api_key == "secret"
  assert FakeOpenAI.instances[1].api_key == "next-secret"
  assert all(client.closed for client in FakeOpenAI.instances)


@pytest.mark.asyncio
async def test_health_checker_reuses_cached_openai_clients(monkeypatch) -> None:
  await close_cached_openai_clients()
  FakeOpenAI.instances = []
  monkeypatch.setattr(openai_client_cache, "AsyncOpenAI", FakeOpenAI)
  checker = OpenAIAPIConfigHealthChecker(
    headers={"X-Test": "yes"},
    timeout_seconds=3,
    request_queue=ImmediateQueue(),  # type: ignore[arg-type]
  )
  embedding_config = _effective_config(kind="embedding", model="text-embedding-test")
  llm_config = _effective_config(kind="llm", api_key="llm-secret", model="chat-model")

  try:
    first_embedding = await checker.check_embedding(embedding_config)
    second_embedding = await checker.check_embedding(embedding_config)
    first_llm = await checker.check_llm(llm_config)
    second_llm = await checker.check_llm(llm_config)
  finally:
    await close_cached_openai_clients()

  assert first_embedding.ok is True
  assert second_embedding.ok is True
  assert first_llm.ok is True
  assert second_llm.ok is True
  assert len(FakeOpenAI.instances) == 2
  assert [len(client.embedding_requests) for client in FakeOpenAI.instances] == [2, 0]
  assert [len(client.chat_requests) for client in FakeOpenAI.instances] == [0, 2]
  assert all(client.closed for client in FakeOpenAI.instances)


def _effective_config(
  *,
  kind: str,
  api_key: str = "secret",
  model: str,
) -> EffectiveAPIConfig:
  return EffectiveAPIConfig(
    config=APIConfig(
      id=f"{kind}-config",
      name=f"{kind} Config",
      provider="openai",
      kind=kind,  # type: ignore[arg-type]
      api_key_configured=bool(api_key),
      api_key_required=True,
      base_url="https://api.example.test/v1",
      mode="non_stream",
      model=model,
      thinking_enabled=False,
      max_tokens=1024,
      dimensions=2 if kind == "embedding" else None,
    ),
    api_key=api_key,
  )
