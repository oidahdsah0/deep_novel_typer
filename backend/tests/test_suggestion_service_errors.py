import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.perspectives import CreatePerspectiveRequest, UpdatePerspectiveRequest
from app.Schemas.projects import CreateProjectRequest
from app.Utils.errors import LLMRequestError
from tests.fakes import FailingLLMClient
from tests.service_factories import build_suggestion_services


@pytest.mark.asyncio
async def test_suggestion_service_surfaces_configured_llm_failure(tmp_path) -> None:
  llm_client = FailingLLMClient("provider unavailable")
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
        name="Failing Config",
        api_key="failing-secret",
        base_url="https://failing.example.test",
        mode="non_stream",
        model="failing-model",
      ),
    )
    await perspective_service.update_perspective(
      project.id,
      perspective.id,
      UpdatePerspectiveRequest(api_config_id=config.id, is_enabled=True),
    )
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在码头。")

    with pytest.raises(LLMRequestError, match="provider unavailable"):
      await suggestion_service.suggest_for_paragraph(
        project.id, "chapter-001", "林澈停在码头。"
      )

    assert len(llm_client.calls) == 1
  finally:
    await store.shutdown()
