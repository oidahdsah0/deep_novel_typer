from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
from pydantic import ValidationError

from app.Schemas.chat import ChatMessage, ChatRequest
from app.Schemas.chat_session import CreateChatSessionRequest, UpdateChatSessionRequest
from app.Schemas.prompt_profiles import UpdatePromptProfileRequest
from app.Schemas.projects import CreateProjectRequest
from app.Services.chat_session.repository import ChatSessionRepository
from app.Services.prompt_profiles import PromptProfileService
from app.Utils.locks import AsyncLockRegistry
from tests.service_factories import build_services


async def _create_project(store, project_service):
    project = await project_service.create_project(CreateProjectRequest(title="Test"))
    return project


def test_chat_message_accepts_reasoning_only_assistant():
    message = ChatMessage(role="assistant", content="", reasoning="推理中")

    assert message.content == ""
    assert message.reasoning == "推理中"

    with pytest.raises(ValidationError):
        ChatMessage(role="user", content=" ")

    with pytest.raises(ValidationError):
        ChatMessage(role="assistant", content="", reasoning="")


def test_chat_request_requires_latest_user_message():
    ChatRequest(
        messages=[
            ChatMessage(role="assistant", content="", reasoning="推理中"),
            ChatMessage(role="user", content="继续说"),
        ]
    )

    with pytest.raises(ValidationError):
        ChatRequest(messages=[ChatMessage(role="assistant", content="好的")])


@pytest.mark.asyncio
async def test_create_and_list_sessions(tmp_path):
    store, project_service, _ch, _doc = await build_services(tmp_path)
    try:
        project = await _create_project(store, project_service)
        db = project_service._db
        repo = ChatSessionRepository(db)

        now1 = "2026-01-01T00:00:00+00:00"
        now2 = "2026-01-01T00:00:01+00:00"
        await repo.create_session(
            project.id, "s1", CreateChatSessionRequest(title="对话1"), now1
        )
        await repo.create_session(
            project.id, "s2", CreateChatSessionRequest(title="对话2"), now2
        )

        sessions = await repo.list_sessions(project.id)
        assert len(sessions) == 2
        assert sessions[0].title == "对话2"  # most recent first
        assert sessions[1].title == "对话1"
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_list_sessions_empty(tmp_path):
    store, project_service, _ch, _doc = await build_services(tmp_path)
    try:
        project = await _create_project(store, project_service)
        db = project_service._db
        repo = ChatSessionRepository(db)

        sessions = await repo.list_sessions(project.id)
        assert sessions == []
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_append_and_list_messages(tmp_path):
    store, project_service, _ch, _doc = await build_services(tmp_path)
    try:
        project = await _create_project(store, project_service)
        db = project_service._db
        repo = ChatSessionRepository(db)

        now = "2026-01-01T00:00:00+00:00"
        await repo.create_session(project.id, "s1", CreateChatSessionRequest(), now)
        await repo.append_message(
            project.id, "s1", "user", "你好", "", now
        )
        now2 = "2026-01-01T00:00:01+00:00"
        await repo.append_message(
            project.id, "s1", "assistant", "你好！", "思考中", now2
        )

        msgs = await repo.list_messages(project.id, "s1")
        assert len(msgs) == 2
        assert msgs[0].role == "user"
        assert msgs[0].content == "你好"
        assert msgs[1].role == "assistant"
        assert msgs[1].content == "你好！"
        assert msgs[1].reasoning == "思考中"
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_update_session_title(tmp_path):
    store, project_service, _ch, _doc = await build_services(tmp_path)
    try:
        project = await _create_project(store, project_service)
        db = project_service._db
        repo = ChatSessionRepository(db)

        now = "2026-01-01T00:00:00+00:00"
        await repo.create_session(
            project.id, "s1", CreateChatSessionRequest(title="旧标题"), now
        )
        await repo.update_session(
            project.id, "s1", UpdateChatSessionRequest(title="新标题"), now
        )

        row = await repo.get_session_row(project.id, "s1")
        assert row is not None
        assert str(row["title"]) == "新标题"
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_delete_session(tmp_path):
    store, project_service, _ch, _doc = await build_services(tmp_path)
    try:
        project = await _create_project(store, project_service)
        db = project_service._db
        repo = ChatSessionRepository(db)

        now = "2026-01-01T00:00:00+00:00"
        await repo.create_session(project.id, "s1", CreateChatSessionRequest(), now)
        await repo.delete_session(project.id, "s1")

        row = await repo.get_session_row(project.id, "s1")
        assert row is None
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_delete_session_cascades_messages(tmp_path):
    store, project_service, _ch, _doc = await build_services(tmp_path)
    try:
        project = await _create_project(store, project_service)
        db = project_service._db
        repo = ChatSessionRepository(db)

        now = "2026-01-01T00:00:00+00:00"
        await repo.create_session(project.id, "s1", CreateChatSessionRequest(), now)
        await repo.append_message(
            project.id, "s1", "user", "hello", "", now
        )
        await repo.delete_session(project.id, "s1")

        msgs = await repo.list_messages(project.id, "s1")
        assert msgs == []
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_get_session_row_not_found(tmp_path):
    store, project_service, _ch, _doc = await build_services(tmp_path)
    try:
        db = project_service._db
        repo = ChatSessionRepository(db)

        row = await repo.get_session_row("nonexistent", "s1")
        assert row is None
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_persist_turn_rolls_back_user_message_when_assistant_insert_fails(tmp_path, monkeypatch):
    store, project_service, _ch, _doc = await build_services(tmp_path)
    try:
        project = await _create_project(store, project_service)
        repo = ChatSessionRepository(project_service._db)
        now = "2026-01-01T00:00:00+00:00"
        await repo.create_session(project.id, "s1", CreateChatSessionRequest(), now)
        # 令事务内第 2 条 SQL（assistant 插入）失败，验证同一事务回滚 user 消息。
        real_transaction = repo._db.transaction

        @asynccontextmanager
        async def failing_assistant_transaction():
            async with real_transaction() as conn:
                original_execute = conn.execute
                counter = [0]

                async def execute(query, params=()):
                    counter[0] += 1
                    if counter[0] == 2:
                        raise RuntimeError("assistant insert failed")
                    return await original_execute(query, params)

                conn.execute = execute
                yield conn

        monkeypatch.setattr(repo._db, "transaction", failing_assistant_transaction)

        with pytest.raises(RuntimeError, match="assistant insert failed"):
            await repo.persist_turn(
                project.id, "s1", "用户问题", "助手回复", "", "2026-01-01T00:00:01+00:00"
            )

        assert await repo.list_messages(project.id, "s1") == []
    finally:
        await store.shutdown()


@pytest.mark.asyncio
async def test_chat_prompt_profile_normalizes_legacy_json_contract(tmp_path):
    store, project_service, chapter_service, document_service = await build_services(tmp_path)
    try:
        project = await _create_project(store, project_service)
        locks = AsyncLockRegistry()
        prompt_profile_service = PromptProfileService(
            project_service._db,
            locks,
            project_service,
            chapter_service,
            document_service,
        )

        profile = await prompt_profile_service.update_profile(
            project.id,
            "chat_about_work",
            UpdatePromptProfileRequest(
                output_contract="强制输出契约（不可删除）：最终响应必须只返回合法 JSON object，顶层只能包含 text。"
            ),
        )

        assert "流式自由文本对话" in profile.output_contract
        assert "最终响应必须只返回合法 JSON object" not in profile.output_contract
    finally:
        await store.shutdown()
