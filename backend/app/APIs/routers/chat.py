from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import StreamingResponse

from app.APIs.dependencies import get_chat_service
from app.Schemas.chat import ChatRequest
from app.Schemas.chat_session import (
    ChatSessionSummary,
    ChatSessionWithMessages,
    CreateChatSessionRequest,
    UpdateChatSessionRequest,
)
from app.Services.chat_service import ChatService

router = APIRouter()


@router.get(
    "/api/projects/{project_id}/chat/sessions",
    response_model=list[ChatSessionSummary],
)
async def list_sessions(
    project_id: str,
    service: ChatService = Depends(get_chat_service),
) -> list[ChatSessionSummary]:
    return await service.list_sessions(project_id)


@router.post(
    "/api/projects/{project_id}/chat/sessions",
    response_model=ChatSessionWithMessages,
    status_code=201,
)
async def create_session(
    project_id: str,
    request: CreateChatSessionRequest | None = None,
    service: ChatService = Depends(get_chat_service),
) -> ChatSessionWithMessages:
    return await service.create_session(project_id, request)


@router.get(
    "/api/projects/{project_id}/chat/sessions/{session_id}",
    response_model=ChatSessionWithMessages,
)
async def get_session(
    project_id: str,
    session_id: str,
    service: ChatService = Depends(get_chat_service),
) -> ChatSessionWithMessages:
    return await service.get_session(project_id, session_id)


@router.patch(
    "/api/projects/{project_id}/chat/sessions/{session_id}",
    response_model=ChatSessionSummary,
)
async def update_session(
    project_id: str,
    session_id: str,
    request: UpdateChatSessionRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatSessionSummary:
    return await service.update_session(project_id, session_id, request)


@router.delete(
    "/api/projects/{project_id}/chat/sessions/{session_id}",
    status_code=204,
)
async def delete_session(
    project_id: str,
    session_id: str,
    service: ChatService = Depends(get_chat_service),
) -> Response:
    await service.delete_session(project_id, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/api/projects/{project_id}/chat")
async def stream_chat(
    project_id: str,
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    session_id = request.session_id
    user_message = request.messages[-1].content if request.messages else ""
    plan = await service.prepare_stream_chat(project_id, request)

    async def sse_generator():
        content_parts: list[str] = []
        reasoning_parts: list[str] = []
        try:
            async for event in service.stream_chat(project_id, request, plan):
                if event.content_delta:
                    content_parts.append(event.content_delta)
                if event.reasoning_delta:
                    reasoning_parts.append(event.reasoning_delta)
                if not event.content_delta and not event.reasoning_delta:
                    continue
                payload = {
                    "delta": event.content_delta,
                    "reasoning_delta": event.reasoning_delta,
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            if session_id and (user_message or content_parts):
                await service.persist_messages(
                    project_id,
                    session_id,
                    user_message,
                    "".join(content_parts),
                    "".join(reasoning_parts),
                )
            yield "data: [DONE]\n\n"
        except Exception:
            if session_id and (user_message or content_parts):
                try:
                    await service.persist_messages(
                        project_id,
                        session_id,
                        user_message,
                        "".join(content_parts),
                        "".join(reasoning_parts),
                    )
                except Exception:
                    pass
            payload = {
                "error": {
                    "code": "chat_stream_interrupted",
                    "message": "聊天流式响应中断，消息可能未完整保存。",
                }
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
