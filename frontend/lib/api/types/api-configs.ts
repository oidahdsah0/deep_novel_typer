import type { ApiConfigKind, ApiProtocol, ApiProvider } from "./common";

export type ApiConfig = {
  id: string;
  name: string;
  provider: ApiProvider;
  kind: ApiConfigKind;
  protocol: ApiProtocol;
  base_url: string;
  api_key_required: boolean;
  api_key_configured: boolean;
  mode: "non_stream";
  model: string;
  thinking_enabled: boolean;
  reasoning_effort: "high" | "max";
  max_tokens: number;
  context_window_tokens: number;
  temperature: number | null;
  top_p: number | null;
  top_k: number | null;
  dimensions: number | null;
  is_default: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type ApiConfigTemplate = Omit<
  ApiConfig,
  "id" | "api_key_configured" | "is_default" | "created_at" | "updated_at"
> & {
  provider_label: string;
  supports_streaming: false;
  supports_thinking: boolean;
  supports_embeddings: boolean;
};

export type ApiConfigHealthCheckResult = {
  ok: boolean;
  config_id: string;
  kind: ApiConfigKind;
  provider: ApiProvider;
  model: string;
  mode: "non_stream";
  latency_ms: number | null;
  checked_at: string;
  json_mode_supported: boolean | null;
  embedding_dimensions: number | null;
  error_code: string | null;
  error_message: string | null;
};

export type ApiConfigInput = Omit<
  ApiConfig,
  "id" | "api_key_configured" | "created_at" | "updated_at"
> & {
  api_key?: string | null;
  clear_api_key?: boolean;
};
