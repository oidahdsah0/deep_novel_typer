import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.perspectives import CreatePerspectiveRequest, UpdatePerspectiveRequest
from app.Schemas.projects import CreateProjectRequest
from app.Utils.errors import LLMContextWindowExceededError
from tests.fakes import DisabledLLMClient, FakeLLMClient
from tests.service_factories import build_suggestion_services


@pytest.mark.asyncio
async def test_created_project_has_no_default_perspectives(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    perspective_service,
    _suggestion_service,
    _api_config_service,
  ) = await build_suggestion_services(tmp_path, DisabledLLMClient())
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    assert await perspective_service.list_perspectives(project.id) == []
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_created_perspective_starts_disabled(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    perspective_service,
    _suggestion_service,
    _api_config_service,
  ) = await build_suggestion_services(tmp_path, DisabledLLMClient())
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    perspective = await perspective_service.create_perspective(
      project.id,
      CreatePerspectiveRequest(
        name="Pace Editor",
        description="关注节奏。",
        instructions="检查节奏。",
      ),
    )

    assert perspective.is_enabled is False
    assert (await perspective_service.list_perspectives(project.id))[0].is_enabled is False
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_suggestion_service_uses_local_fallback_without_llm(tmp_path) -> None:
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    _api_config_service,
  ) = await build_suggestion_services(tmp_path, DisabledLLMClient())
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await _create_test_perspective(perspective_service, project.id, "Pace Editor")
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      "林澈听见码头深处传来第二次回声，却没有告诉同行的警员。",
    )

    suggestions = await suggestion_service.suggest_for_paragraph(
      project.id, "chapter-001", "林澈听见码头深处传来第二次回声。"
    )

    assert suggestions
    assert {suggestion.source for suggestion in suggestions} == {"local"}
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_suggestion_service_local_snapshot_does_not_call_llm(tmp_path) -> None:
  llm_client = FakeLLMClient('{"cards": []}')
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    _api_config_service,
  ) = await build_suggestion_services(tmp_path, llm_client)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await _create_test_perspective(perspective_service, project.id, "Pace Editor")
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      "林澈听见码头深处传来第二次回声，却没有告诉同行的警员。",
    )

    suggestions = await suggestion_service.suggest_locally_for_paragraph(
      project.id, "chapter-001", "林澈听见码头深处传来第二次回声。"
    )

    assert suggestions
    assert {suggestion.source for suggestion in suggestions} == {"local"}
    assert llm_client.calls == []
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_disabled_perspective_can_be_requested_manually(tmp_path) -> None:
  llm_client = FakeLLMClient('{"cards": []}')
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    api_config_service,
  ) = await build_suggestion_services(tmp_path, llm_client)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    perspective = await perspective_service.create_perspective(
      project.id,
      CreatePerspectiveRequest(
        name="Line Reader",
        description="关注句子。",
        instructions="检查句子。",
      ),
    )
    config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Line Config",
        api_key="line-secret",
        base_url="https://line.example.test",
        mode="non_stream",
        model="line-model",
      ),
    )
    await perspective_service.update_perspective(
      project.id,
      perspective.id,
      UpdatePerspectiveRequest(api_config_id=config.id),
    )
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在码头。")
    llm_client.content = f"""
    {{
      "cards": [
        {{
          "perspective_id": "{perspective.id}",
          "title": "句子重心清楚",
          "body": "这一句可以保留。",
          "severity": "calm"
        }}
      ]
    }}
    """

    automatic = await suggestion_service.suggest_for_paragraph(
      project.id, "chapter-001", "林澈停在码头。"
    )
    manual = await suggestion_service.suggest_for_paragraph(
      project.id,
      "chapter-001",
      "林澈停在码头。",
      perspective_id=perspective.id,
    )

    assert automatic == []
    assert len(llm_client.calls) == 1
    assert [suggestion.perspective_id for suggestion in manual] == [perspective.id]
    assert manual[0].source == "llm"
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_suggestion_service_parses_llm_cards(tmp_path) -> None:
  llm_client = FakeLLMClient(
    {
      "pace-model": """
      {
        "cards": [
          {
            "perspective_id": "pace-editor",
            "title": "悬念节拍清楚",
            "body": "这一段可以保留回声意象，再补一个动作让紧张感落地。",
            "severity": "focus"
          }
        ]
      }
      """,
      "character-model": """
      {
        "cards": [
          {
            "perspective_id": "character-critic",
            "title": "人物反应明确",
            "body": "人物回避信息的动作可以再具体一点。",
            "severity": "calm"
          }
        ]
      }
      """,
    }
  )
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    api_config_service,
  ) = await build_suggestion_services(tmp_path, llm_client)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await _create_test_perspective(perspective_service, project.id, "Pace Editor")
    await _create_test_perspective(perspective_service, project.id, "Character Critic")
    pace_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Pace Config",
        api_key="pace-secret",
        base_url="https://pace.example.test",
        mode="non_stream",
        model="pace-model",
        thinking_enabled=True,
        reasoning_effort="max",
        max_tokens=2048,
        temperature=None,
        top_p=0.86,
        top_k=64,
      ),
    )
    character_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Character Config",
        api_key="character-secret",
        base_url="https://character.example.test",
        mode="non_stream",
        model="character-model",
        thinking_enabled=False,
        reasoning_effort="high",
        max_tokens=1024,
        temperature=0.7,
        top_p=0.91,
        top_k=32,
      ),
    )
    await perspective_service.update_perspective(
      project.id,
      "pace-editor",
      UpdatePerspectiveRequest(api_config_id=pace_config.id),
    )
    await perspective_service.update_perspective(
      project.id,
      "character-critic",
      UpdatePerspectiveRequest(api_config_id=character_config.id),
    )
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      "林澈听见码头深处传来第二次回声，却没有告诉同行的警员。",
    )

    suggestions = await suggestion_service.suggest_for_paragraph(
      project.id, "chapter-001", "林澈听见码头深处传来第二次回声。"
    )

    llm_suggestions = [suggestion for suggestion in suggestions if suggestion.source == "llm"]
    assert {suggestion.perspective_id for suggestion in llm_suggestions} == {
      "pace-editor",
      "character-critic",
    }
    assert len(llm_client.calls) == 2
    pace_call = next(call for call in llm_client.calls if call[1].model == "pace-model")
    character_call = next(call for call in llm_client.calls if call[1].model == "character-model")
    assert "启用视角" in pace_call[0][1].content
    assert pace_call[1].mode == "non_stream"
    assert pace_call[1].api_key == "pace-secret"
    assert pace_call[1].base_url == "https://pace.example.test"
    assert pace_call[1].request_options == {
      "max_tokens": 2048,
      "response_format": {"type": "json_object"},
      "top_p": 0.86,
      "top_k": 64,
      "thinking": {"type": "enabled"},
      "reasoning_effort": "max",
      "temperature": None,
    }
    assert character_call[1].mode == "non_stream"
    assert character_call[1].api_key == "character-secret"
    assert character_call[1].base_url == "https://character.example.test"
    assert character_call[1].request_options == {
      "max_tokens": 1024,
      "response_format": {"type": "json_object"},
      "top_p": 0.91,
      "top_k": 32,
      "thinking": {"type": "disabled"},
      "reasoning_effort": None,
      "temperature": 0.7,
    }
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_suggestion_service_does_not_group_perspectives_with_same_config(tmp_path) -> None:
  llm_client = FakeLLMClient('{"cards": []}')
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    api_config_service,
  ) = await build_suggestion_services(tmp_path, llm_client)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await _create_test_perspective(perspective_service, project.id, "Pace Editor")
    await _create_test_perspective(perspective_service, project.id, "Character Critic")
    shared_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Shared Config",
        api_key="shared-secret",
        base_url="https://shared.example.test",
        mode="non_stream",
        model="shared-model",
      ),
    )
    for perspective_id in ("pace-editor", "character-critic"):
      await perspective_service.update_perspective(
        project.id,
        perspective_id,
        UpdatePerspectiveRequest(api_config_id=shared_config.id),
      )
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在码头。")

    suggestions = await suggestion_service.suggest_for_paragraph(
      project.id, "chapter-001", "林澈停在码头。"
    )

    assert len(llm_client.calls) == 2
    user_messages = [call[0][1].content for call in llm_client.calls]
    assert sum('"id": "pace-editor"' in content for content in user_messages) == 1
    assert sum('"id": "character-critic"' in content for content in user_messages) == 1
    assert all(
      not ('"id": "pace-editor"' in content and '"id": "character-critic"' in content)
      for content in user_messages
    )
    assert {suggestion.perspective_id for suggestion in suggestions} == {
      "pace-editor",
      "character-critic",
    }
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_suggestion_service_rejects_invalid_llm_card_schema(tmp_path) -> None:
  llm_client = FakeLLMClient(
    {
      "pace-model": """
      {
        "cards": [
          {
            "perspective_id": "pace-editor",
            "title": "坏枚举",
            "body": "这张卡不应被接受。",
            "severity": "bad"
          }
        ]
      }
      """,
    }
  )
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    api_config_service,
  ) = await build_suggestion_services(tmp_path, llm_client)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await _create_test_perspective(perspective_service, project.id, "Pace Editor")
    pace_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Pace Config",
        api_key="pace-secret",
        base_url="https://pace.example.test",
        mode="non_stream",
        model="pace-model",
      ),
    )
    await perspective_service.update_perspective(
      project.id,
      "pace-editor",
      UpdatePerspectiveRequest(api_config_id=pace_config.id),
    )
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在码头。")

    suggestions = await suggestion_service.suggest_for_paragraph(
      project.id, "chapter-001", "林澈停在码头。"
    )

    pace_suggestion = next(item for item in suggestions if item.perspective_id == "pace-editor")
    assert pace_suggestion.source == "local"
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_suggestion_service_surfaces_context_window_overflow(tmp_path) -> None:
  llm_client = FakeLLMClient('{"cards": []}')
  (
    store,
    project_service,
    chapter_service,
    perspective_service,
    suggestion_service,
    api_config_service,
  ) = await build_suggestion_services(tmp_path, llm_client)
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    perspective = await perspective_service.create_perspective(
      project.id,
      CreatePerspectiveRequest(
        name="Line Reader",
        description="关注句子。",
        instructions="检查句子。",
      ),
    )
    config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Tiny Context Config",
        api_key="tiny-secret",
        base_url="https://tiny.example.test",
        mode="non_stream",
        model="tiny-model",
        max_tokens=4096,
        context_window_tokens=1024,
      ),
    )
    await perspective_service.update_perspective(
      project.id,
      perspective.id,
      UpdatePerspectiveRequest(api_config_id=config.id, is_enabled=True),
    )
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在码头。")

    with pytest.raises(LLMContextWindowExceededError):
      await suggestion_service.suggest_for_paragraph(
        project.id,
        "chapter-001",
        "林澈停在码头。",
      )

    assert llm_client.calls == []
  finally:
    await store.shutdown()


async def _create_test_perspective(perspective_service, project_id: str, name: str) -> None:
  perspective = await perspective_service.create_perspective(
    project_id,
    CreatePerspectiveRequest(
      name=name,
      description=f"{name} description",
      instructions=f"{name} instructions",
    ),
  )
  await perspective_service.update_perspective(
    project_id,
    perspective.id,
    UpdatePerspectiveRequest(is_enabled=True),
  )
