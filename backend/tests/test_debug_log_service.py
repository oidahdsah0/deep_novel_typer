import pytest

from app.Services.debug_log_service import LLMDebugContext
from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.generation import GenerateDraftRequest
from app.Schemas.projects import CreateProjectRequest
from tests.fakes import DisabledLLMClient, FakeLLMClient
from tests.service_factories import build_generation_services

@pytest.mark.asyncio
async def test_debug_log_service_records_generation_usage_and_raw_payload(tmp_path) -> None:
  llm_client = FakeLLMClient('{"text":"码头另一侧亮起一盏灯。"}')
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
        name="Debug Config",
        api_key="debug-secret",
        base_url="https://debug.example.test",
        mode="non_stream",
        model="debug-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=True,
      ),
    )

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

    snapshot = await debug_log_service.snapshot(project.id)
    assert snapshot.token_usage.today == 19
    assert snapshot.token_usage.last_7_days == 19
    assert snapshot.token_usage.last_30_days == 19
    assert snapshot.token_usage.total == 19
    assert snapshot.token_usage.unknown_usage_requests == 0
    assert len(snapshot.request_logs) == 1
    log = snapshot.request_logs[0]
    assert log.request_type == "generate_next_paragraph"
    assert log.provider == "deepseek"
    assert log.model == "debug-model"
    assert log.total_tokens == 19
    assert log.request_body["model"] == "debug-model"
    assert log.debug_readable.context_pack is not None
    assert log.debug_readable.context_pack.request_type == "generate_next_paragraph"
    assert log.debug_readable.context_pack.project["title"] == "Test Book"
    assert log.debug_readable.context_pack.budget.input_tokens > 0
    assert log.debug_readable.context_budget is not None
    assert log.debug_readable.context_materials == []
    assert log.response_body["usage"] == {
      "prompt_tokens": 12,
      "completion_tokens": 7,
      "total_tokens": 19,
    }
    assert log.debug_readable.system_messages
    assert log.debug_readable.user_messages
    assert (
      log.request_body["messages"][1]["content"]
      == log.debug_readable.user_messages[0].content
    )
    assert "<context_pack" in log.debug_readable.user_messages[0].content
    assert log.debug_readable.request_options == {
      "model": "debug-model",
      "stream": False,
    }
    assert log.debug_readable.raw_content == '{"text":"码头另一侧亮起一盏灯。"}'
    assert log.debug_readable.parsed_payload == {"text": "码头另一侧亮起一盏灯。"}
    assert log.debug_readable.schema_error is None

    await debug_log_service.clear_request_logs(project.id)
    assert await debug_log_service.request_logs(project_id=project.id) == []
    assert (await debug_log_service.token_usage(project.id)).total == 19

    await debug_log_service.clear_token_usage(project.id)
    assert (await debug_log_service.token_usage(project.id)).total == 0
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_debug_log_service_readable_view_redacts_secrets_and_reports_json_errors(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    _generation_service,
    _api_config_service,
    debug_log_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_debug_log_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    error_message = "LLM response for perspective_suggestion was not a valid JSON object"
    await debug_log_service.record_llm_request(
      context=LLMDebugContext(
        project_id=project.id,
        request_type="perspective_suggestion",
        provider="deepseek",
        model="debug-model",
      ),
      request_body={
        "model": "debug-model",
        "messages": [
          {"role": "system", "content": "只返回 JSON。"},
          {"role": "user", "content": "检查这一段。"},
        ],
        "stream": False,
        "api_key": "debug-secret",
        "headers": {"Authorization": "Bearer debug-secret", "X-Trace": "ok"},
        "extra_body": {"api-token": "debug-secret"},
      },
      response_body={
        "choices": [{"message": {"content": "我不是 JSON"}, "finish_reason": "stop"}],
      },
      status="error",
      error_message=error_message,
    )

    logs = await debug_log_service.request_logs(project_id=project.id)
    readable = logs[0].debug_readable
    assert readable.system_messages[0].content == "只返回 JSON。"
    assert readable.user_messages[0].content == "检查这一段。"
    assert readable.raw_content == "我不是 JSON"
    assert readable.parsed_payload is None
    assert readable.schema_error == error_message
    assert readable.request_options["api_key"] == "[redacted]"
    assert readable.request_options["headers"] == {"Authorization": "[redacted]", "X-Trace": "ok"}
    assert readable.request_options["extra_body"] == {"api-token": "[redacted]"}
    assert "debug-secret" not in str(readable.model_dump())
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_debug_log_service_keeps_recent_50_logs(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    _generation_service,
    _api_config_service,
    debug_log_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_debug_log_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    for index in range(55):
      await debug_log_service.record_llm_request(
        context=LLMDebugContext(
          project_id=project.id,
          request_type="generate_next_paragraph",
          provider="deepseek",
          model="debug-model",
        ),
        request_body={"index": index},
        response_body={"ok": True},
        status="success",
        prompt_tokens=1,
        completion_tokens=1,
        total_tokens=2,
        duration_ms=index,
      )

    logs = await debug_log_service.request_logs(project_id=project.id)
    assert len(logs) == 50
    assert logs[0].request_body["index"] == 54
    assert logs[-1].request_body["index"] == 5
    assert (await debug_log_service.token_usage(project.id)).total == 110

    await debug_log_service.clear_all(project.id)
    assert await debug_log_service.request_logs(project_id=project.id) == []
    assert (await debug_log_service.token_usage(project.id)).total == 0
  finally:
    await store.shutdown()
