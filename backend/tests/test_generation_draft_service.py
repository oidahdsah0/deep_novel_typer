import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.generation import GenerateDraftRequest, GenerateQuickDraftRequest
from app.Schemas.prompt_profiles import UpdatePromptProfileRequest
from app.Schemas.projects import CreateProjectRequest
from app.Utils.errors import (
  LLMContextWindowExceededError,
  LLMRequestError,
  LLMResponseFormatError,
)
from tests.fakes import FailingLLMClient, FakeLLMClient
from tests.service_factories import build_generation_services


@pytest.mark.asyncio
async def test_generation_service_rejects_context_window_overflow(tmp_path) -> None:
  llm_client = FakeLLMClient('{"text":"不应调用"}')
  store, project_service, chapter_service, generation_service, api_config_service = (
    await build_generation_services(tmp_path, llm_client)
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈站在门口。")
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Tiny Context",
        api_key="tiny-secret",
        base_url="https://tiny.example.test",
        mode="non_stream",
        model="tiny-model",
        thinking_enabled=False,
        reasoning_effort="high",
        max_tokens=900,
        context_window_tokens=1024,
        is_default=True,
      ),
    )

    with pytest.raises(LLMContextWindowExceededError):
      await generation_service.generate_draft(
        project.id,
        GenerateDraftRequest(
          chapter_id="chapter-001",
          action="next_paragraph",
          writing_preset_id="camera",
          writing_prompt="继续。",
          author_preset_id="skill",
          author_skill="克制。",
        ),
      )
    assert len(llm_client.calls) == 0
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_generation_service_surfaces_configured_llm_failure(tmp_path) -> None:
  llm_client = FailingLLMClient("provider timed out")
  store, project_service, chapter_service, generation_service, api_config_service = (
    await build_generation_services(tmp_path, llm_client)
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈站在门口。")
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Failing Config",
        api_key="failing-secret",
        base_url="https://failing.example.test",
        mode="non_stream",
        model="failing-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=True,
      ),
    )

    with pytest.raises(LLMRequestError, match="provider timed out"):
      await generation_service.generate_draft(
        project.id,
        GenerateDraftRequest(
          chapter_id="chapter-001",
          action="next_paragraph",
          writing_preset_id="camera",
          writing_prompt="继续。",
          author_preset_id="skill",
          author_skill="克制。",
        ),
      )

    assert len(llm_client.calls) == 1
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_generation_service_uses_request_profile_api_config(tmp_path) -> None:
  llm_client = FakeLLMClient(
    {
      "default-model": '{"text":"默认模型返回。"}',
      "selected-request-model": '{"text":"请求配置模型返回。"}',
    }
  )
  (
    store,
    project_service,
    chapter_service,
    generation_service,
    api_config_service,
    prompt_profile_service,
  ) = await build_generation_services(
    tmp_path,
    llm_client,
    include_prompt_profile_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在门口。")
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Default Model",
        api_key="default-secret",
        base_url="https://default.example.test",
        mode="non_stream",
        model="default-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=True,
      ),
    )
    selected_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Selected Request Model",
        api_key="selected-secret",
        base_url="https://selected.example.test",
        mode="non_stream",
        model="selected-request-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=False,
      ),
    )
    await prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(config={"api_config_id": selected_config.id}),
    )

    draft = await generation_service.generate_draft(
      project.id,
      GenerateDraftRequest(
        chapter_id="chapter-001",
        action="next_paragraph",
        writing_preset_id="camera",
        writing_prompt="继续。",
        author_preset_id="skill",
        author_skill="克制。",
      ),
    )

    assert draft.text == "请求配置模型返回。"
    assert draft.model == "selected-request-model"
    _messages, overrides = llm_client.calls[0]
    assert overrides.api_key == "selected-secret"
    assert overrides.model == "selected-request-model"
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_generation_service_uses_json_llm_request(tmp_path) -> None:
  llm_client = FakeLLMClient('{"text":"码头另一侧忽然亮起一盏灯，像是在替某个人指路。"}')
  store, project_service, chapter_service, generation_service, api_config_service = (
    await build_generation_services(tmp_path, llm_client)
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      "林澈听见码头深处传来第二次回声，却没有告诉同行的警员。",
    )
    base_chapter = await chapter_service.get_chapter(project.id, "chapter-001")
    await chapter_service.update_chapter_writing_synopsis(
      project.id,
      "chapter-001",
      "本章梗概：林澈必须意识到码头旧案证词被调包。",
      base_updated_at=base_chapter.writing_synopsis_updated_at,
    )
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Draft Config",
        api_key="draft-secret",
        base_url="https://draft.example.test",
        mode="non_stream",
        model="draft-model",
        thinking_enabled=False,
        reasoning_effort="high",
        max_tokens=1536,
        temperature=0.55,
        top_p=0.77,
        top_k=12,
        is_default=True,
      ),
    )

    draft = await generation_service.generate_draft(
      project.id,
      GenerateDraftRequest(
        chapter_id="chapter-001",
        action="next_paragraph",
        cursor_index=22,
        previous_paragraph="林澈听见码头深处传来第二次回声，却没有告诉同行的警员。",
        next_paragraph="巡逻艇的灯从雨幕里扫过去。",
        writing_preset_id="camera",
        writing_prompt="使用镜头语言推进下一段。",
        author_preset_id="skill",
        author_skill="保持冷静克制。",
      ),
    )

    assert draft.source == "llm"
    assert draft.model == "draft-model"
    assert draft.text == "码头另一侧忽然亮起一盏灯，像是在替某个人指路。"
    assert len(llm_client.calls) == 1
    messages, overrides = llm_client.calls[0]
    assert "不要在 text 字段里加入标题、解释、项目符号或分析过程" in messages[0].content
    assert "合法 json object" in messages[0].content
    assert '"text"' in messages[0].content
    assert "光标前最近的有文字段落" in messages[1].content
    assert "光标后第一段正文" in messages[1].content
    assert "巡逻艇的灯从雨幕里扫过去。" in messages[1].content
    assert "本章梗概：林澈必须意识到码头旧案证词被调包。" in messages[1].content
    assert "使用镜头语言推进下一段。" in messages[1].content
    assert "保持冷静克制。" in messages[1].content
    assert overrides.api_key == "draft-secret"
    assert overrides.base_url == "https://draft.example.test"
    assert overrides.mode == "non_stream"
    assert overrides.model == "draft-model"
    assert overrides.request_options == {
      "max_tokens": 1536,
      "response_format": {"type": "json_object"},
      "top_p": 0.77,
      "top_k": 12,
      "thinking": {"type": "disabled"},
      "reasoning_effort": None,
      "temperature": 0.55,
    }
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_generation_service_omits_quick_generation_prompt(tmp_path) -> None:
  llm_client = FakeLLMClient('{"text":"他按住门把手，先听里面的动静。"}')
  store, project_service, chapter_service, generation_service, api_config_service = (
    await build_generation_services(tmp_path, llm_client)
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在门外。")
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Quick Config",
        api_key="quick-secret",
        base_url="https://quick.example.test",
        mode="non_stream",
        model="quick-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=True,
      ),
    )

    draft = await generation_service.generate_quick_draft(
      project.id,
      GenerateQuickDraftRequest(
        chapter_id="chapter-001",
        cursor_index=6,
        previous_paragraph="林澈停在门外。",
        next_paragraph="门内忽然传来一声轻响。",
        quick_preset_id="quick-next-paragraph",
        quick_prompt="快速接一句动作，不要解释。",
        author_preset_id="skill",
        author_skill="冷静克制。",
      ),
    )

    assert draft.source == "llm"
    assert draft.model == "quick-model"
    assert draft.text == "他按住门把手，先听里面的动静。"
    assert len(llm_client.calls) == 1
    messages, overrides = llm_client.calls[0]
    assert "快速生成助手" in messages[0].content
    assert "快速生成任务提示词" not in messages[1].content
    assert "快速接一句动作，不要解释。" not in messages[1].content
    assert "冷静克制。" in messages[1].content
    assert "门内忽然传来一声轻响。" in messages[1].content
    assert overrides.api_key == "quick-secret"
    assert overrides.model == "quick-model"
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_quick_generation_uses_prompt_profile_model_system_and_temperature(
  tmp_path,
) -> None:
  llm_client = FakeLLMClient(
    {
      "profile-model": '{"text":"请求配置模型返回。"}',
    }
  )
  (
    store,
    project_service,
    chapter_service,
    generation_service,
    api_config_service,
    prompt_profile_service,
  ) = await build_generation_services(
    tmp_path,
    llm_client,
    include_prompt_profile_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在门外。")
    profile_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Profile Model",
        api_key="profile-secret",
        base_url="https://profile.example.test",
        mode="non_stream",
        model="profile-model",
        thinking_enabled=False,
        reasoning_effort="high",
        temperature=0.2,
        is_default=True,
      ),
    )
    await prompt_profile_service.update_profile(
      project.id,
      "quick_generate_next_paragraph",
      UpdatePromptProfileRequest(
        config={"api_config_id": profile_config.id, "temperature": 0.9},
        system_template="SQL 系统提示词：写一个短动作。",
      ),
    )

    draft = await generation_service.generate_quick_draft(
      project.id,
      GenerateQuickDraftRequest(
        chapter_id="chapter-001",
        cursor_index=6,
        previous_paragraph="林澈停在门外。",
        next_paragraph="门内忽然传来一声轻响。",
        quick_preset_id="quick-next-paragraph",
        quick_prompt="快速接一句动作，不要解释。",
        author_preset_id="skill",
        author_skill="冷静克制。",
      ),
    )

    assert draft.text == "请求配置模型返回。"
    assert draft.model == "profile-model"
    messages, overrides = llm_client.calls[0]
    assert "SQL 系统提示词：写一个短动作。" in messages[0].content
    assert "快速接一句动作，不要解释。" not in messages[0].content
    assert "合法 json object" in messages[0].content
    assert overrides.api_key == "profile-secret"
    assert overrides.model == "profile-model"
    assert overrides.request_options["temperature"] == 0.9
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_generation_service_rejects_invalid_json_schema_and_logs_error(tmp_path) -> None:
  llm_client = FakeLLMClient('{"text":"   "}')
  (
    store,
    project_service,
    chapter_service,
    generation_service,
    api_config_service,
    debug_log_service,
  ) = await build_generation_services(
    tmp_path,
    llm_client,
    include_debug_log_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在码头。")
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Invalid Schema Config",
        api_key="schema-secret",
        base_url="https://schema.example.test",
        mode="non_stream",
        model="schema-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=True,
      ),
    )

    with pytest.raises(LLMResponseFormatError):
      await generation_service.generate_draft(
        project.id,
        GenerateDraftRequest(
          chapter_id="chapter-001",
          action="next_paragraph",
          writing_preset_id="camera",
          writing_prompt="继续推进。",
          author_preset_id="skill",
          author_skill="克制。",
        ),
      )

    logs = await debug_log_service.request_logs(project_id=project.id)
    assert len(logs) == 1
    assert logs[0].status == "error"
    assert logs[0].debug_readable.parsed_payload == {"text": "   "}
    assert logs[0].debug_readable.schema_error
    assert "schema validation failed" in logs[0].debug_readable.schema_error
  finally:
    await store.shutdown()
