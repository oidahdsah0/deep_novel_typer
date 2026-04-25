import type { DebugRequestStatus } from "./common";
import type { PromptContextPack } from "./prompts";

export type DebugTokenUsage = {
  today: number;
  last_7_days: number;
  last_30_days: number;
  total: number;
  unknown_usage_requests: number;
};

export type DebugReadableMessage = {
  role: string;
  content: string;
};

export type DebugReadableView = {
  system_messages: DebugReadableMessage[];
  user_messages: DebugReadableMessage[];
  request_options: Record<string, unknown>;
  context_pack: PromptContextPack | null;
  context_budget: Record<string, unknown> | null;
  context_materials: Array<Record<string, unknown>>;
  raw_content: string | null;
  parsed_payload: Record<string, unknown> | null;
  schema_error: string | null;
  embedding_summary: Record<string, unknown>;
};

export type DebugRequestLog = {
  id: string;
  project_id: string | null;
  model_kind: "llm" | "embedding";
  request_type: string;
  api_config_id: string | null;
  provider: string;
  model: string;
  status: DebugRequestStatus;
  created_at: string;
  request_body: Record<string, unknown>;
  response_body: Record<string, unknown>;
  debug_readable: DebugReadableView;
  error_message: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  duration_ms: number | null;
};

export type DebugSnapshot = {
  token_usage: DebugTokenUsage;
  request_logs: DebugRequestLog[];
};

export type ModelQueueItem = {
  id: string;
  kind: "llm" | "embedding";
  label: string;
  status: "queued" | "running";
  priority: "manual" | "batch" | "auto";
  model: string | null;
  queued_at: string;
  started_at: string | null;
};

export type ModelQueueSnapshot = {
  worker_count: number;
  queued_count: number;
  running_count: number;
  items: ModelQueueItem[];
};
