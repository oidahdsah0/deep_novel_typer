from __future__ import annotations

from pydantic import BaseModel, Field

from app.Schemas.chat import ChatMessage


class ChatSessionSummary(BaseModel):
    id: str
    project_id: str
    title: str
    created_at: str
    updated_at: str


class ChatSessionWithMessages(ChatSessionSummary):
    messages: list[ChatMessage]


class CreateChatSessionRequest(BaseModel):
    title: str = Field(default="新对话", max_length=80)


class UpdateChatSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)
