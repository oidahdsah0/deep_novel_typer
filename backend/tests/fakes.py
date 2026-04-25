from app.Utils.llm import LLMMessage, LLMRequestOverrides, LLMResponse
from app.Services.embeddings import EmbeddingBatchResult, build_model_signature
from app.Schemas.api_configs import APIConfigHealthCheckResult
from app.Utils.config import GenerationPresetDefault


class DisabledLLMClient:
  model = "disabled"

  @property
  def is_configured(self) -> bool:
    return False

  def is_configured_for(self, overrides: LLMRequestOverrides | None = None) -> bool:
    return False

  async def complete(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> LLMResponse:
    raise AssertionError("disabled client should not be called")

  async def complete_non_stream(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> LLMResponse:
    return await self.complete(messages, overrides)


class FakeLLMClient:
  model = "fake-model"

  def __init__(self, content: str | dict[str, str]) -> None:
    self.content = content
    self.messages: list[LLMMessage] = []
    self.overrides: LLMRequestOverrides | None = None
    self.calls: list[tuple[list[LLMMessage], LLMRequestOverrides | None]] = []

  @property
  def is_configured(self) -> bool:
    return True

  def is_configured_for(self, overrides: LLMRequestOverrides | None = None) -> bool:
    return overrides is None or bool(overrides.api_key)

  async def complete(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> LLMResponse:
    self.messages = messages
    self.overrides = overrides
    self.calls.append((messages, overrides))
    if isinstance(self.content, dict):
      content = self.content.get(overrides.model if overrides else "", '{"cards": []}')
    else:
      content = self.content
    model = overrides.model if overrides else self.model
    return LLMResponse(
      content=content,
      model=model,
      request_body={
        "model": model,
        "messages": [message.__dict__ for message in messages],
        "stream": False,
      },
      response_body={
        "model": model,
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 7, "total_tokens": 19},
      },
      prompt_tokens=12,
      completion_tokens=7,
      total_tokens=19,
    )

  async def complete_non_stream(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> LLMResponse:
    return await self.complete(messages, overrides)


class FailingLLMClient(FakeLLMClient):
  def __init__(self, message: str = "upstream unavailable") -> None:
    super().__init__('{"text":"unused"}')
    self.message = message

  async def complete(
    self, messages: list[LLMMessage], overrides: LLMRequestOverrides | None = None
  ) -> LLMResponse:
    self.messages = messages
    self.overrides = overrides
    self.calls.append((messages, overrides))
    raise RuntimeError(self.message)


class FakeAPIConfigHealthChecker:
  def __init__(self) -> None:
    self.llm_calls = []
    self.embedding_calls = []

  async def check_llm(self, effective_config):
    self.llm_calls.append(effective_config)
    config = effective_config.config
    return APIConfigHealthCheckResult(
      ok=True,
      config_id=config.id,
      kind=config.kind,
      provider=config.provider,
      model=config.model,
      latency_ms=12,
      checked_at="2026-04-26T00:00:00+00:00",
      json_mode_supported=True,
    )

  async def check_embedding(self, effective_config):
    self.embedding_calls.append(effective_config)
    config = effective_config.config
    return APIConfigHealthCheckResult(
      ok=True,
      config_id=config.id,
      kind=config.kind,
      provider=config.provider,
      model=config.model,
      latency_ms=8,
      checked_at="2026-04-26T00:00:00+00:00",
      embedding_dimensions=config.dimensions or 3,
    )


class FakeEmbeddingRuntime:
  def __init__(self) -> None:
    self.calls = []
    self.fail_next: Exception | None = None
    self.omit_usage = False

  async def embed_texts(self, effective_config, texts, *, label="embedding_batch"):
    self.calls.append((effective_config, list(texts), label))
    if self.fail_next is not None:
      error = self.fail_next
      self.fail_next = None
      raise error
    vectors = [[float(index + 1), float(len(text))] for index, text in enumerate(texts)]
    token_count = sum(len(text) for text in texts)
    return EmbeddingBatchResult(
      vectors=vectors,
      model=effective_config.config.model,
      model_signature=build_model_signature(effective_config.config),
      prompt_tokens=None if self.omit_usage else token_count,
      total_tokens=None if self.omit_usage else token_count,
      duration_ms=1,
    )


GENERATION_DEFAULTS = (
  GenerationPresetDefault(
    kind="writing_mode",
    preset_id="camera",
    name="镜头写作",
    content="镜头默认提示词",
  ),
  GenerationPresetDefault(
    kind="writing_mode",
    preset_id="linear",
    name="线性写作",
    content="线性默认提示词",
  ),
  GenerationPresetDefault(
    kind="author_persona",
    preset_id="skill",
    name="人格设定 Skill",
    content="人格默认提示词",
  ),
  GenerationPresetDefault(
    kind="quick_generation_mode",
    preset_id="quick-next-paragraph",
    name="快速下一段",
    content="快速默认提示词",
  ),
  GenerationPresetDefault(
    kind="chapter_blueprint_mode",
    preset_id="basic-blueprint",
    name="基础铺设",
    content="铺设默认提示词",
  ),
  GenerationPresetDefault(
    kind="polish_mode",
    preset_id="tighten",
    name="凝练润色",
    content="润色默认提示词",
  ),
  GenerationPresetDefault(
    kind="document_polish_mode",
    preset_id="document-tighten",
    name="资料凝练润色",
    content="资料润色默认提示词",
  ),
  GenerationPresetDefault(
    kind="document_generation_mode",
    preset_id="document-continue",
    name="延续当前资料",
    content="资料续写默认提示词",
  ),
  GenerationPresetDefault(
    kind="editor_persona",
    preset_id="structured-editor",
    name="结构化资料编辑",
    content="资料编辑人格默认提示词",
  ),
)
