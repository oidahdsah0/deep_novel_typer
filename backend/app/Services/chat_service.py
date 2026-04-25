from __future__ import annotations

import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.Services.api_configs import APIConfigService, EffectiveAPIConfig, build_llm_overrides
from app.Services.chapter_service import ChapterService
from app.Services.chat_session.repository import ChatSessionRepository
from app.Services.context_limits import CHAPTER_CONTEXT_CHARS
from app.Services.debug_log_service import DebugLogService, LLMDebugContext
from app.Services.document_service import DocumentService
from app.Services.llm_context_budget import ensure_context_budget, int_option
from app.Services.model_request_queue_service import model_request_label
from app.Services.prompt_profiles.rendering import PromptProfileBuildResult
from app.Services.prompt_profiles.service import PromptProfileService
from app.Services.project_service import ProjectService
from app.Schemas.chat import ChatRequest
from app.Schemas.chat_session import (
  ChatSessionSummary,
  ChatSessionWithMessages,
  CreateChatSessionRequest,
  UpdateChatSessionRequest,
)
from app.Utils.errors import EntityNotFoundError, LLMNotConfiguredError
from app.Utils.llm import (
  CompletionClient,
  LLMMessage,
  LLMRequestOverrides,
  LLMStreamEvent,
  build_chat_completion_request_snapshot,
)
from app.Utils.locks import AsyncLockRegistry
from app.Utils.text import tail_text

@dataclass(frozen=True)
class ChatStreamPlan:
  effective_config: EffectiveAPIConfig | None
  build_result: PromptProfileBuildResult
  messages: list[LLMMessage]
  overrides: LLMRequestOverrides | None
  request_snapshot: dict[str, object]


class ChatService:
  def __init__(
    self,
    project_service: ProjectService,
    chapter_service: ChapterService,
    document_service: DocumentService,
    prompt_profile_service: PromptProfileService,
    api_config_service: APIConfigService,
    llm_client: CompletionClient,
    debug_log_service: DebugLogService | None = None,
    chat_session_repo: ChatSessionRepository | None = None,
    locks: AsyncLockRegistry | None = None,
  ) -> None:
    self._project_service = project_service
    self._chapter_service = chapter_service
    self._document_service = document_service
    self._prompt_profile_service = prompt_profile_service
    self._api_config_service = api_config_service
    self._llm_client = llm_client
    self._debug_log_service = debug_log_service
    self._chat_session_repo = chat_session_repo
    self._locks = locks

  async def list_sessions(self, project_id: str) -> list[ChatSessionSummary]:
    await self._require_project(project_id)
    return await self._chat_session_repo.list_sessions(project_id)

  async def create_session(
    self, project_id: str, request: CreateChatSessionRequest | None = None
  ) -> ChatSessionWithMessages:
    await self._require_project(project_id)
    if request is None:
      request = CreateChatSessionRequest()
    session_id = uuid4().hex[:12]
    now = _now_iso()
    async with self._locks.get(f"{project_id}:chat"):
      await self._chat_session_repo.create_session(project_id, session_id, request, now)
    return ChatSessionWithMessages(
      id=session_id,
      project_id=project_id,
      title=request.title,
      messages=[],
      created_at=now,
      updated_at=now,
    )

  async def get_session(
    self, project_id: str, session_id: str
  ) -> ChatSessionWithMessages:
    await self._require_project(project_id)
    row = await self._chat_session_repo.get_session_row(project_id, session_id)
    if row is None:
      raise EntityNotFoundError(f"Chat session not found: {session_id}")
    messages = await self._chat_session_repo.list_messages(project_id, session_id)
    return ChatSessionWithMessages(
      id=str(row["id"]),
      project_id=str(row["project_id"]),
      title=str(row["title"]),
      messages=messages,
      created_at=str(row["created_at"]),
      updated_at=str(row["updated_at"]),
    )

  async def update_session(
    self, project_id: str, session_id: str, request: UpdateChatSessionRequest
  ) -> ChatSessionSummary:
    await self._require_project(project_id)
    row = await self._chat_session_repo.get_session_row(project_id, session_id)
    if row is None:
      raise EntityNotFoundError(f"Chat session not found: {session_id}")
    now = _now_iso()
    async with self._locks.get(f"{project_id}:chat"):
      await self._chat_session_repo.update_session(project_id, session_id, request, now)
    return ChatSessionSummary(
      id=session_id,
      project_id=project_id,
      title=request.title,
      created_at=str(row["created_at"]),
      updated_at=now,
    )

  async def delete_session(self, project_id: str, session_id: str) -> None:
    await self._require_project(project_id)
    row = await self._chat_session_repo.get_session_row(project_id, session_id)
    if row is None:
      raise EntityNotFoundError(f"Chat session not found: {session_id}")
    async with self._locks.get(f"{project_id}:chat"):
      await self._chat_session_repo.delete_session(project_id, session_id)

  async def persist_messages(
    self,
    project_id: str,
    session_id: str,
    user_content: str,
    assistant_content: str,
    assistant_reasoning: str,
  ) -> None:
    await self._require_project(project_id)
    if not user_content.strip():
      return
    row = await self._chat_session_repo.get_session_row(project_id, session_id)
    if row is None:
      raise EntityNotFoundError(f"Chat session not found: {session_id}")
    now = _now_iso()
    async with self._locks.get(f"{project_id}:chat"):
      await self._chat_session_repo.persist_turn(
        project_id,
        session_id,
        user_content,
        assistant_content,
        assistant_reasoning,
        now,
      )

  async def stream_chat(
    self, project_id: str, request: ChatRequest, plan: ChatStreamPlan | None = None
  ) -> AsyncIterator[LLMStreamEvent]:
    plan = plan or await self.prepare_stream_chat(project_id, request)
    effective_config = plan.effective_config
    build_result = plan.build_result
    messages = plan.messages
    overrides = plan.overrides
    request_snapshot = plan.request_snapshot

    content_parts: list[str] = []
    reasoning_parts: list[str] = []
    raw_chunks: list[dict[str, object]] = []
    model = ""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    started_at = time.monotonic()

    try:
      with model_request_label("chat_about_work"):
        async for event in self._llm_client.complete_stream(messages, overrides):
          if event.raw:
            raw_chunks.append(event.raw)
          if event.prompt_tokens is not None:
            prompt_tokens = event.prompt_tokens
          if event.completion_tokens is not None:
            completion_tokens = event.completion_tokens
          if event.total_tokens is not None:
            total_tokens = event.total_tokens
          if event.model and not model:
            model = event.model
          if not event.content_delta and not event.reasoning_delta:
            continue
          if event.content_delta:
            content_parts.append(event.content_delta)
          if event.reasoning_delta:
            reasoning_parts.append(event.reasoning_delta)
          yield event
    except Exception:
      if self._debug_log_service:
        duration_ms = int((time.monotonic() - started_at) * 1000)
        await self._debug_log_service.record_llm_request(
          context=LLMDebugContext(
            project_id=project_id,
            request_type="chat_about_work",
            api_config_id=effective_config.config.id if effective_config else None,
            provider=effective_config.config.provider if effective_config else "",
            model=model,
          ),
          request_body=request_snapshot,
          response_body={
            "content": "".join(content_parts),
            "reasoning": "".join(reasoning_parts),
            "chunks": raw_chunks,
            "stream_error": True,
          },
          status="error",
          duration_ms=duration_ms,
          prompt_tokens=prompt_tokens,
          completion_tokens=completion_tokens,
          total_tokens=total_tokens,
          context_pack=build_result.context_pack,
        )
      raise

    duration_ms = int((time.monotonic() - started_at) * 1000)
    if self._debug_log_service:
      await self._debug_log_service.record_llm_request(
        context=LLMDebugContext(
          project_id=project_id,
          request_type="chat_about_work",
          api_config_id=effective_config.config.id if effective_config else None,
          provider=effective_config.config.provider if effective_config else "",
          model=model,
        ),
        request_body=request_snapshot,
        response_body={
          "content": "".join(content_parts),
          "reasoning": "".join(reasoning_parts),
          "chunks": raw_chunks,
          "usage": _usage_payload(prompt_tokens, completion_tokens, total_tokens),
        },
        status="success",
        duration_ms=duration_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        context_pack=build_result.context_pack,
      )

  async def prepare_stream_chat(
    self, project_id: str, request: ChatRequest
  ) -> ChatStreamPlan:
    await self._require_project(project_id)
    effective_config = await self._effective_config(project_id)
    build_result = await self._prompt_profile_service.build_preview(
      project_id,
      "chat_about_work",
      await self._chat_runtime_input(project_id, request),
    )

    prompt_messages = [
      message for message in build_result.messages if message.content.strip()
    ]
    messages = [
      *prompt_messages,
      *[
        LLMMessage(role=msg.role, content=msg.content)
        for msg in request.messages
        if msg.content.strip()
      ],
    ]

    temperature_override = await self._prompt_profile_service.request_temperature(
      project_id,
      "chat_about_work",
    )
    overrides = (
      build_llm_overrides(effective_config, temperature_override=temperature_override)
      if effective_config
      else None
    )
    if effective_config is None or not self._llm_client.is_configured_for(overrides):
      raise LLMNotConfiguredError(
        "作品聊天需要可用的 LLM API 配置，请先在主页面配置可用的 LLM Key、Endpoint 和模型。"
      )
    request_snapshot = build_chat_completion_request_snapshot(
      messages,
      overrides,
      stream=True,
    )
    request_options = overrides.request_options if overrides else {}
    ensure_context_budget(
      messages,
      output_token_budget=int_option((request_options or {}).get("max_tokens")),
      context_window_tokens=(
        effective_config.config.context_window_tokens if effective_config else None
      ),
      request_label="chat_about_work",
    )
    return ChatStreamPlan(
      effective_config=effective_config,
      build_result=build_result,
      messages=messages,
      overrides=overrides,
      request_snapshot=request_snapshot,
    )

  async def _effective_config(self, project_id: str):
    config_id = await self._prompt_profile_service.request_api_config_id(
      project_id, "chat_about_work"
    )
    return await self._api_config_service.get_effective_config(config_id, kind="llm")

  async def _require_project(self, project_id: str) -> None:
    await self._project_service.get_manifest(project_id)

  async def _chat_runtime_input(
    self, project_id: str, request: ChatRequest
  ) -> dict[str, object]:
    runtime_input: dict[str, object] = {}
    if request.chapter_id:
      chapter = await self._chapter_service.get_chapter(project_id, request.chapter_id)
      runtime_input.update(
        {
          "current_chapter_id": request.chapter_id,
          "chapter_title": chapter.title,
          "current_chapter": tail_text(chapter.content, CHAPTER_CONTEXT_CHARS),
        }
      )
    return runtime_input


def _now_iso() -> str:
  return datetime.now(timezone.utc).isoformat()

def _usage_payload(
  prompt_tokens: int | None,
  completion_tokens: int | None,
  total_tokens: int | None,
) -> dict[str, int] | None:
  if prompt_tokens is None and completion_tokens is None and total_tokens is None:
    return None
  payload: dict[str, int] = {}
  if prompt_tokens is not None:
    payload["prompt_tokens"] = prompt_tokens
  if completion_tokens is not None:
    payload["completion_tokens"] = completion_tokens
  if total_tokens is not None:
    payload["total_tokens"] = total_tokens
  return payload
