export type ProjectStatus = "planning" | "drafting" | "revising" | "completed";
export type ApiConfigKind = "llm" | "embedding";
export type GenerationPresetKind =
  | "writing_mode"
  | "quick_generation_mode"
  | "chapter_blueprint_mode"
  | "author_persona"
  | "polish_mode"
  | "document_polish_mode"
  | "document_generation_mode"
  | "editor_persona";
export type DraftGenerationAction = "next_paragraph" | "next_section";
export type PromptRequestType =
  | "perspective_suggestion"
  | "polish_selection"
  | "quick_generate_next_paragraph"
  | "generate_next_paragraph"
  | "generate_next_section"
  | "generate_chapter_blueprint"
  | "polish_document_selection"
  | "generate_document_continuation"
  | "chat_about_work";
export type VersionedResourceType = "chapter" | "document";
export type VersionType = "manual" | "auto" | "initial" | "pre_action" | "pre_restore";
export type PromptProfileVersionType = "manual" | "initial" | "pre_restore";
export type DebugRequestStatus = "success" | "error";
export type ApiProvider =
  | "deepseek"
  | "openai"
  | "gemini"
  | "grok"
  | "siliconflow"
  | "ollama"
  | "lm_studio"
  | "vllm";
export type ApiProtocol = "openai_compatible";
export type ProjectSearchScope =
  | "all"
  | "chapters"
  | "documents"
  | "prompts"
  | "presets"
  | "versions";
export type ProjectSearchResourceType =
  | "chapter"
  | "document"
  | "prompt_profile"
  | "prompt_profile_version"
  | "generation_preset"
  | "resource_version";
