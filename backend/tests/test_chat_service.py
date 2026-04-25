from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI

from app.APIs.dependencies import get_chat_service
from app.APIs.error_handlers import register_error_handlers
from app.APIs.routers.chat import router as chat_router
from app.Schemas.chat import ChatMessage, ChatRequest
from app.Schemas.chat_session import CreateChatSessionRequest
from app.Schemas.projects import CreateProjectRequest
from app.Services.api_configs import APIConfigService
from app.Services.chat_service import ChatService
from app.Services.chat_session.repository import ChatSessionRepository
from app.Services.debug_log_service import DebugLogService
from app.Services.prompt_profiles import PromptProfileService
from app.Utils.config import _load_llm_settings
from app.Utils.errors import EntityNotFoundError, LLMNotConfiguredError
from app.Utils.llm import LLMMessage, LLMRequestOverrides, LLMStreamEvent
from app.Utils.locks import AsyncLockRegistry
from tests.fakes import DisabledLLMClient
from tests.service_factories import build_services


class FakeStreamingLLMClient:
    model = "fake-stream-model"

    def __init__(self) -> None:
        self.calls: list[tuple[list[LLMMessage], LLMRequestOverrides | None]] = []

    @property
    def is_configured(self) -> bool:
        return True

    def is_configured_for(self, overrides: LLMRequestOverrides | None = None) -> bool:
        return True

    async def complete(self, messages, overrides=None):
        raise AssertionError("chat should use complete_stream")

    async def complete_non_stream(self, messages, overrides=None):
        raise AssertionError("chat should use complete_stream")

    async def complete_stream(self, messages, overrides=None):
        self.calls.append((messages, overrides))
        yield LLMStreamEvent(
            content_delta="回答",
            model="fake-stream-model",
            raw={"choices": [{"delta": {"content": "回答"}}]},
        )
        yield LLMStreamEvent(
            model="fake-stream-model",
            raw={
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 3,
                    "total_tokens": 13,
                }
            },
            prompt_tokens=10,
            completion_tokens=3,
            total_tokens=13,
        )


class UnconfiguredRouteChatService:
    stream_started = False

    async def prepare_stream_chat(self, project_id, request):
        raise LLMNotConfiguredError("需要配置 LLM")

    async def stream_chat(self, project_id, request, plan=None):
        self.stream_started = True
        raise AssertionError("route should not start streaming after prepare failure")


class InterruptedRouteChatService:
    def __init__(self) -> None:
        self.persisted: list[tuple[str, str, str, str, str]] = []

    async def prepare_stream_chat(self, project_id, request):
        return object()

    async def stream_chat(self, project_id, request, plan=None):
        yield LLMStreamEvent(content_delta="半截回复", reasoning_delta="半截推理")
        raise RuntimeError("upstream interrupted")

    async def persist_messages(
        self,
        project_id,
        session_id,
        user_content,
        assistant_content,
        assistant_reasoning,
    ):
        self.persisted.append(
            (
                project_id,
                session_id,
                user_content,
                assistant_content,
                assistant_reasoning,
            )
        )


async def _create_project(project_service):
    return await project_service.create_project(CreateProjectRequest(title="Test"))


def _make_chat_service(
    project_service,
    chapter_service,
    document_service,
    llm_client,
    *,
    debug_log_service=None,
    chat_session_repo=None,
):
    db = project_service._db
    locks = AsyncLockRegistry()
    prompt_profile_service = PromptProfileService(
        db,
        locks,
        project_service,
        chapter_service,
        document_service,
    )
    api_config_service = APIConfigService(db, locks, _load_llm_settings())
    return (
        ChatService(
            project_service,
            chapter_service,
            document_service,
            prompt_profile_service,
            api_config_service,
            llm_client,
            debug_log_service,
            chat_session_repo=chat_session_repo or ChatSessionRepository(db),
            locks=locks,
        ),
        api_config_service,
    )


@pytest.mark.asyncio
async def test_chat_service_rejects_missing_project(tmp_path):
    store, project_service, chapter_service, document_service = await build_services(tmp_path)
    try:
        service, _api_config_service = _make_chat_service(
            project_service,
            chapter_service,
            document_service,
            FakeStreamingLLMClient(),
        )

        with pytest.raises(EntityNotFoundError):
            await service.list_sessions("missing-project")
        with pytest.raises(EntityNotFoundError):
            await service.create_session("missing-project", CreateChatSessionRequest())
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_chat_service_uses_prompt_profile_stream_request_and_records_debug(tmp_path):
    store, project_service, chapter_service, document_service = await build_services(tmp_path)
    try:
        project = await _create_project(project_service)
        await chapter_service.update_chapter(
            project.id,
            "chapter-001",
            "林澈把旧档案摊开，码头雾气压在窗外。",
        )
        db = project_service._db
        locks = AsyncLockRegistry()
        prompt_profile_service = PromptProfileService(
            db,
            locks,
            project_service,
            chapter_service,
            document_service,
        )
        api_config_service = APIConfigService(db, locks, _load_llm_settings())
        await api_config_service.ensure_default_config()
        debug_log_service = DebugLogService(db, locks)
        fake_llm = FakeStreamingLLMClient()
        service = ChatService(
            project_service,
            chapter_service,
            document_service,
            prompt_profile_service,
            api_config_service,
            fake_llm,
            debug_log_service,
            chat_session_repo=ChatSessionRepository(db),
            locks=locks,
        )

        events = [
            event
            async for event in service.stream_chat(
                project.id,
                ChatRequest(
                    chapter_id="chapter-001",
                    messages=[ChatMessage(role="user", content="下一步怎么写？")],
                ),
            )
        ]

        assert [event.content_delta for event in events] == ["回答"]
        sent_messages = fake_llm.calls[0][0]
        assert sent_messages[0].role == "system"
        assert "流式自由文本对话" in sent_messages[0].content
        assert "最终响应必须只返回合法 json object" not in sent_messages[0].content
        assert sent_messages[1].role == "user"
        assert "作品上下文" in sent_messages[1].content
        assert "当前对话摘录" not in sent_messages[1].content
        assert sent_messages[-1].content == "下一步怎么写？"
        assert sum(
            message.content.count("下一步怎么写？") for message in sent_messages
        ) == 1

        logs = await debug_log_service.request_logs(project_id=project.id)
        assert len(logs) == 1
        log = logs[0]
        assert log.request_type == "chat_about_work"
        assert log.request_body["stream"] is True
        assert "response_format" not in log.request_body
        assert log.request_body["stream_options"] == {"include_usage": True}
        assert log.response_body["chunks"]
        assert log.total_tokens == 13
        assert log.debug_readable.schema_error is None
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_prepare_stream_chat_rejects_unconfigured_llm_before_streaming(tmp_path):
    store, project_service, chapter_service, document_service = await build_services(tmp_path)
    try:
        project = await _create_project(project_service)
        service, api_config_service = _make_chat_service(
            project_service,
            chapter_service,
            document_service,
            DisabledLLMClient(),
        )
        await api_config_service.ensure_default_config()

        with pytest.raises(LLMNotConfiguredError, match="作品聊天需要可用的 LLM API 配置"):
            await service.prepare_stream_chat(
                project.id,
                ChatRequest(messages=[ChatMessage(role="user", content="下一步怎么写？")]),
            )
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_chat_route_returns_json_error_before_opening_stream() -> None:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(chat_router)
    service = UnconfiguredRouteChatService()
    app.dependency_overrides[get_chat_service] = lambda: service

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/projects/project-1/chat",
            json={"messages": [{"role": "user", "content": "下一步怎么写？"}]},
        )

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["code"] == "llm_not_configured"
    assert service.stream_started is False


@pytest.mark.asyncio
async def test_chat_route_sends_error_event_when_stream_interrupts() -> None:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(chat_router)
    service = InterruptedRouteChatService()
    app.dependency_overrides[get_chat_service] = lambda: service

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/projects/project-1/chat",
            json={
                "session_id": "session-1",
                "messages": [{"role": "user", "content": "下一步怎么写？"}],
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'data: {"delta": "半截回复", "reasoning_delta": "半截推理"}' in response.text
    assert "chat_stream_interrupted" in response.text
    assert "[DONE]" not in response.text
    assert service.persisted == [
        (
            "project-1",
            "session-1",
            "下一步怎么写？",
            "半截回复",
            "半截推理",
        )
    ]


@pytest.mark.asyncio
async def test_persist_messages_updates_session_timestamp_and_preserves_order(tmp_path):
    store, project_service, chapter_service, document_service = await build_services(tmp_path)
    try:
        project = await _create_project(project_service)
        repo = ChatSessionRepository(project_service._db)
        service, _api_config_service = _make_chat_service(
            project_service,
            chapter_service,
            document_service,
            FakeStreamingLLMClient(),
            chat_session_repo=repo,
        )
        await repo.create_session(
            project.id,
            "s1",
            CreateChatSessionRequest(title="旧对话"),
            "2026-01-01T00:00:00+00:00",
        )

        await service.persist_messages(
            project.id,
            "s1",
            "用户问题",
            "助手回答",
            "推理",
        )

        session = await repo.get_session_row(project.id, "s1")
        messages = await repo.list_messages(project.id, "s1")
        assert session is not None
        assert str(session["updated_at"]) != "2026-01-01T00:00:00+00:00"
        assert [message.role for message in messages] == ["user", "assistant"]
        assert [message.content for message in messages] == ["用户问题", "助手回答"]
        assert messages[1].reasoning == "推理"
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_persist_messages_requires_existing_session(tmp_path):
    store, project_service, chapter_service, document_service = await build_services(tmp_path)
    try:
        project = await _create_project(project_service)
        repo = ChatSessionRepository(project_service._db)
        service, _api_config_service = _make_chat_service(
            project_service,
            chapter_service,
            document_service,
            FakeStreamingLLMClient(),
            chat_session_repo=repo,
        )

        with pytest.raises(EntityNotFoundError):
            await service.persist_messages(
                project.id,
                "missing-session",
                "用户问题",
                "助手回答",
                "",
            )
    finally:
        await store.shutdown()
