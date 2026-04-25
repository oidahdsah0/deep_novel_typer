from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ChatMessage(BaseModel):
  model_config = ConfigDict(extra="forbid")
  role: Literal["user", "assistant"]
  content: str = Field(default="", max_length=10000)
  reasoning: str = Field(default="", max_length=20000)

  @model_validator(mode="after")
  def validate_payload(self) -> "ChatMessage":
    if self.role == "user" and not self.content.strip():
      raise ValueError("User chat message content is required.")
    if self.role == "assistant" and not (self.content or self.reasoning):
      raise ValueError("Assistant chat message content or reasoning is required.")
    return self


class ChatRequest(BaseModel):
  model_config = ConfigDict(extra="forbid")
  chapter_id: str | None = Field(default=None, max_length=80)
  session_id: str | None = Field(default=None, max_length=80)
  messages: list[ChatMessage] = Field(min_length=1, max_length=100)

  @model_validator(mode="after")
  def validate_latest_message(self) -> "ChatRequest":
    if self.messages[-1].role != "user":
      raise ValueError("Latest chat message must be from user.")
    return self
