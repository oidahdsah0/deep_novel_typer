import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.generation import (
  GenerateDocumentContinuationRequest,
  PolishDocumentSelectionRequest,
)
from app.Schemas.projects import CreateProjectRequest
from tests.fakes import FakeLLMClient
from tests.service_factories import build_generation_services


@pytest.mark.asyncio
async def test_generation_service_handles_markdown_document_requests(tmp_path) -> None:
  llm_client = FakeLLMClient(
    {
      "document-model": '{"text":"## 线索补充\\n\\n- 林澈把录音笔标记为 A-17。"}',
    }
  )
  (
    store,
    project_service,
    _chapter_service,
    generation_service,
    api_config_service,
    document_service,
  ) = await build_generation_services(
    tmp_path,
    llm_client,
    include_document_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await document_service.update_document(
      project.id,
      "outline",
      "# 主线大纲\n\n- 林澈回到港口。\n- 匿名信提到旧案。",
    )
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Document Config",
        api_key="document-secret",
        base_url="https://document.example.test",
        mode="non_stream",
        model="document-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=True,
      ),
    )

    polished = await generation_service.polish_document_selection(
      project.id,
      PolishDocumentSelectionRequest(
        document_id="outline",
        selected_text="- 林澈回到港口。",
        polish_preset_id="document-tighten",
        polish_prompt="让资料更清晰。",
        editor_preset_id="structured-editor",
        editor_skill="保持 Markdown 列表格式。",
      ),
    )
    continued = await generation_service.generate_document_continuation(
      project.id,
      GenerateDocumentContinuationRequest(
        document_id="outline",
        generation_preset_id="document-continue",
        generation_prompt="补充录音笔线索。",
        editor_preset_id="structured-editor",
        editor_skill="保持结构化记录。",
      ),
    )

    assert polished.source == "llm"
    assert continued.source == "llm"
    assert polished.text.startswith("## 线索补充")
    assert continued.text.startswith("## 线索补充")
    assert len(llm_client.calls) == 2
    polish_messages, polish_overrides = llm_client.calls[0]
    continuation_messages, _continuation_overrides = llm_client.calls[1]
    assert "Markdown 片段" in polish_messages[0].content
    assert "合法 json object" in polish_messages[0].content
    assert "让资料更清晰。" in polish_messages[1].content
    assert "保持 Markdown 列表格式。" in polish_messages[1].content
    assert "- 林澈回到港口。" in polish_messages[1].content
    assert "补充录音笔线索。" in continuation_messages[1].content
    assert "当前资料摘录" in continuation_messages[1].content
    assert polish_overrides.api_key == "document-secret"
    assert polish_overrides.model == "document-model"
    assert polish_overrides.request_options["response_format"] == {"type": "json_object"}
  finally:
    await store.shutdown()
