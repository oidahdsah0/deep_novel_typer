import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.generation import PolishSelectionRequest
from app.Schemas.projects import CreateProjectRequest
from tests.fakes import FakeLLMClient
from tests.service_factories import build_generation_services


@pytest.mark.asyncio
async def test_generation_service_polishes_selected_text(tmp_path) -> None:
  llm_client = FakeLLMClient('{"text":"林澈停在门口，听见潮声从楼梯下方漫上来。"}')
  store, project_service, chapter_service, generation_service, api_config_service = (
    await build_generation_services(tmp_path, llm_client)
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(
      project.id,
      "chapter-001",
      "林澈停在门口。\n他听见潮声从楼梯下方漫上来。",
    )
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Polish Config",
        api_key="polish-secret",
        base_url="https://polish.example.test",
        mode="non_stream",
        model="polish-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=True,
      ),
    )

    draft = await generation_service.polish_selection(
      project.id,
      PolishSelectionRequest(
        chapter_id="chapter-001",
        selected_text="林澈停在门口。",
        polish_preset_id="tighten",
        polish_prompt="保持克制，增强画面。",
      ),
    )

    assert draft.source == "llm"
    assert draft.model == "polish-model"
    assert draft.text == "林澈停在门口，听见潮声从楼梯下方漫上来。"
    assert len(llm_client.calls) == 1
    messages, overrides = llm_client.calls[0]
    assert "可直接替换选区" in messages[0].content
    assert "合法 json object" in messages[0].content
    assert '"text"' in messages[0].content
    assert "保持克制，增强画面。" in messages[1].content
    assert "林澈停在门口。" in messages[1].content
    assert overrides.api_key == "polish-secret"
    assert overrides.model == "polish-model"
  finally:
    await store.shutdown()
