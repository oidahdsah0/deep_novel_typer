import type { ApiConfigKind } from "./common";
import type { PromptProfileVersionType, PromptRequestType } from "./common";

export type PromptProfile = {
  request_type: PromptRequestType;
  name: string;
  system_template: string;
  user_template: string;
  output_contract: string;
  chapter_ids: string[];
  document_ids: string[];
  config: Record<string, unknown>;
  is_system: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type PromptProfileLibrary = {
  profiles: PromptProfile[];
};

export type PromptProfileSnapshot = {
  name: string;
  system_template: string;
  user_template: string;
  output_contract: string;
  chapter_ids: string[];
  document_ids: string[];
  config: Record<string, unknown>;
};

export type PromptProfileVersion = {
  id: string;
  project_id: string;
  request_type: PromptRequestType;
  version_type: PromptProfileVersionType;
  label: string | null;
  note: string;
  system_chars: number;
  user_chars: number;
  chapter_count: number;
  document_count: number;
  created_at: string;
};

export type PromptProfileVersionDetail = PromptProfileVersion & {
  snapshot: PromptProfileSnapshot;
};

export type RestorePromptProfileVersionResponse = {
  profile: PromptProfile;
  version: PromptProfileVersionDetail;
};

export type PromptProfileUpdate = {
  name?: string;
  system_template?: string;
  user_template?: string;
  output_contract?: string;
  chapter_ids?: string[];
  document_ids?: string[];
  config?: Record<string, unknown>;
};

export type PromptContextFocusBlock = {
  key: string;
  label: string;
  format: "plain" | "markdown" | "json";
  content: string;
  content_mode: "full" | "tail" | "truncated" | "empty" | "metadata_only";
  chars: number;
  token_estimate: number;
  empty: boolean;
  metadata: Record<string, unknown>;
};

export type PromptContextMaterialBlock = {
  id: string;
  title: string;
  kind: "chapter" | "document";
  source: string;
  format: "plain" | "markdown" | "json";
  content: string;
  content_mode: "full" | "tail" | "truncated" | "empty" | "metadata_only";
  chars: number;
  token_estimate: number;
  truncated: boolean;
};

export type PromptContextAgentBlock = {
  id: string;
  name: string;
  kind: "perspective" | "author_persona" | "editor_persona";
  description: string;
  instructions: string;
};

export type PromptContextBudgetReport = {
  input_tokens: number;
  task_tokens: number;
  project_tokens: number;
  focus_tokens: number;
  material_tokens: number;
  agent_tokens: number;
  truncated_materials: number;
  estimator: string;
};

export type PromptContextPack = {
  version: number;
  request_type: PromptRequestType;
  project_id: string;
  task: string;
  project: Record<string, unknown>;
  focus: PromptContextFocusBlock[];
  materials: PromptContextMaterialBlock[];
  agents: PromptContextAgentBlock[];
  constraints: string[];
  budget: PromptContextBudgetReport;
};

export type PromptPreviewProfileOverride = {
  name?: string;
  system_template?: string;
  user_template?: string;
  output_contract?: string;
  chapter_ids?: string[];
  document_ids?: string[];
  config?: Record<string, unknown>;
};

export type PromptPreviewInput = {
  request_type: PromptRequestType;
  chapter_id?: string | null;
  document_id?: string | null;
  paragraph?: string;
  selected_text?: string;
  cursor_index?: number;
  previous_paragraph?: string;
  next_paragraph?: string;
  writing_prompt?: string;
  quick_prompt?: string;
  blueprint_prompt?: string;
  author_persona_id?: string;
  author_persona_name?: string;
  author_persona?: string;
  polish_prompt?: string;
  generation_prompt?: string;
  editor_persona_id?: string;
  editor_persona_name?: string;
  editor_persona?: string;
  profile_override?: PromptPreviewProfileOverride | null;
};

export type PromptPreviewMessage = {
  role: string;
  content: string;
};

export type PromptPreviewMaterial = {
  id: string;
  title: string;
  source: string;
  chars: number;
  truncated: boolean;
  kind: string;
  format: string;
  content_mode: string;
  token_estimate: number;
};

export type PromptPreviewApiConfig = {
  id: string | null;
  name: string;
  provider: string;
  kind: ApiConfigKind;
  base_url: string;
  model: string;
  api_key_required: boolean;
  api_key_configured: boolean;
  configured: boolean;
  is_default: boolean;
  context_window_tokens: number | null;
};

export type PromptPreviewTokenEstimate = {
  input_tokens: number;
  system_tokens: number;
  user_tokens: number;
  output_token_budget: number | null;
  total_with_output_budget: number | null;
  context_window_tokens: number | null;
  context_usage_ratio: number | null;
  context_window_exceeded: boolean;
  estimator: string;
};

export type PromptPreviewItem = {
  label: string;
  api_config: PromptPreviewApiConfig | null;
  request_options: Record<string, unknown>;
  token_estimate: PromptPreviewTokenEstimate;
  context_pack: PromptContextPack | null;
  messages: PromptPreviewMessage[];
  chapters: PromptPreviewMaterial[];
  documents: PromptPreviewMaterial[];
  warnings: string[];
};

export type PromptPreviewResponse = {
  request_type: PromptRequestType;
  items: PromptPreviewItem[];
  warnings: string[];
};
