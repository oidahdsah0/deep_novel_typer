from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.Schemas.common import PromptRequestType


PromptContextContentMode = Literal["full", "tail", "truncated", "empty", "metadata_only"]
PromptContextFormat = Literal["plain", "markdown", "json"]


class PromptContextFocusBlock(BaseModel):
  key: str
  label: str
  format: PromptContextFormat = "plain"
  content: str = ""
  content_mode: PromptContextContentMode = "full"
  chars: int = 0
  token_estimate: int = 0
  empty: bool = False
  metadata: dict[str, Any] = Field(default_factory=dict)


class PromptContextMaterialBlock(BaseModel):
  id: str
  title: str
  kind: Literal["chapter", "document"]
  source: str = "fixed"
  format: PromptContextFormat = "plain"
  content: str = ""
  content_mode: PromptContextContentMode = "full"
  chars: int = 0
  token_estimate: int = 0
  truncated: bool = False


class PromptContextAgentBlock(BaseModel):
  id: str
  name: str
  kind: Literal["perspective", "author_persona", "editor_persona"] = "perspective"
  description: str = ""
  instructions: str = ""


class PromptContextBudgetReport(BaseModel):
  input_tokens: int = 0
  task_tokens: int = 0
  project_tokens: int = 0
  focus_tokens: int = 0
  material_tokens: int = 0
  agent_tokens: int = 0
  truncated_materials: int = 0
  estimator: str = "rough_mixed_text"


class PromptContextPack(BaseModel):
  version: int = 1
  request_type: PromptRequestType
  project_id: str
  task: str = ""
  project: dict[str, Any] = Field(default_factory=dict)
  focus: list[PromptContextFocusBlock] = Field(default_factory=list)
  materials: list[PromptContextMaterialBlock] = Field(default_factory=list)
  agents: list[PromptContextAgentBlock] = Field(default_factory=list)
  constraints: list[str] = Field(default_factory=list)
  budget: PromptContextBudgetReport = Field(default_factory=PromptContextBudgetReport)
