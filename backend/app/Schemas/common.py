from __future__ import annotations

from typing import Literal

DocumentKind = Literal["outline", "design", "note"]
DocumentNodeType = Literal["folder", "markdown"]
ChapterNodeType = Literal["folder", "chapter"]
APIConfigKind = Literal["llm", "embedding"]
ModelRequestKind = Literal["llm", "embedding"]
APIProvider = Literal[
  "deepseek",
  "openai",
  "gemini",
  "grok",
  "siliconflow",
  "ollama",
  "lm_studio",
  "vllm",
]
APIProtocol = Literal["openai_compatible"]
LLMMode = Literal["non_stream"]
LLMReasoningEffort = Literal["high", "max"]
ProjectStatus = Literal["planning", "drafting", "revising", "completed"]
SuggestionSource = Literal["llm", "local"]
GenerationPresetKind = Literal[
  "writing_mode",
  "quick_generation_mode",
  "chapter_blueprint_mode",
  "author_persona",
  "polish_mode",
  "document_polish_mode",
  "document_generation_mode",
  "editor_persona",
]
DraftGenerationAction = Literal["next_paragraph", "next_section"]
PromptRequestType = Literal[
  "perspective_suggestion",
  "polish_selection",
  "quick_generate_next_paragraph",
  "generate_next_paragraph",
  "generate_next_section",
  "generate_chapter_blueprint",
  "polish_document_selection",
  "generate_document_continuation",
  "chat_about_work",
]
PromptProfileVersionType = Literal["manual", "initial", "pre_restore"]
VersionedResourceType = Literal["chapter", "document"]
VersionType = Literal["manual", "auto", "initial", "pre_action", "pre_restore"]
DebugRequestStatus = Literal["success", "error"]
EmbeddingAnalysisStatus = Literal["pending", "running", "success", "error", "stale"]
EmbeddingDistanceAlgorithm = Literal["cosine", "euclidean", "manhattan"]
EmbeddingSegmentationMode = Literal["word", "sentence"]
EmbeddingToolType = Literal["heatmap", "clusters"]
EmbeddingResourceType = Literal["chapter", "document"]
EmbeddingClusterMode = Literal["fixed_tag_centers"]
