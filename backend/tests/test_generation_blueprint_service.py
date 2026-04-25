import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.generation import GenerateChapterBlueprintRequest
from app.Schemas.projects import CreateProjectRequest
from tests.fakes import FakeLLMClient
from tests.service_factories import build_generation_services


@pytest.mark.asyncio
async def test_generation_service_generates_chapter_blueprint_points(tmp_path) -> None:
  llm_client = FakeLLMClient(
    '{"points":["开场先给少年一个明确任务。","中段用异兽失控制造反差。"]}'
  )
  store, project_service, chapter_service, generation_service, api_config_service = (
    await build_generation_services(tmp_path, llm_client)
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "少年站在哨塔下。")
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Blueprint Config",
        api_key="blueprint-secret",
        base_url="https://blueprint.example.test",
        mode="non_stream",
        model="blueprint-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=True,
      ),
    )

    blueprint = await generation_service.generate_chapter_blueprint(
      project.id,
      GenerateChapterBlueprintRequest(
        chapter_id="chapter-001",
        cursor_index=6,
        previous_paragraph="少年",
        next_paragraph="站在哨塔下。",
        blueprint_preset_id="basic-blueprint",
        blueprint_prompt="强调爽点和钩子。",
        author_preset_id="skill",
        author_skill="保持轻快。",
      ),
    )

    assert blueprint.source == "llm"
    assert blueprint.model == "blueprint-model"
    assert blueprint.points == [
      "开场先给少年一个明确任务。",
      "中段用异兽失控制造反差。",
    ]
    assert len(llm_client.calls) == 1
    messages, overrides = llm_client.calls[0]
    assert "points" in messages[0].content
    assert "强调爽点和钩子。" in messages[1].content
    assert "光标插入位置" in messages[1].content
    assert "cursor_index=6" in messages[1].content
    assert "保持轻快。" in messages[1].content
    assert overrides.api_key == "blueprint-secret"
    assert overrides.model == "blueprint-model"
  finally:
    await store.shutdown()
