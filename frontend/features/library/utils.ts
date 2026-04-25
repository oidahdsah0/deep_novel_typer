import {
  defaultApiConfigInput,
  fallbackApiConfigTemplates,
  type ApiConfig,
  type ApiConfigHealthCheckResult,
  type ApiConfigInput,
  type ApiConfigKind,
  type ApiConfigTemplate,
  type ApiProvider,
  type LibrarySnapshot,
  type ProjectInput,
  type ProjectStatus,
  type VersionSettings,
} from "@/lib/api/index";

export const API_CONFIG_MIN_TOKENS = 256;
export const API_CONFIG_MAX_TOKENS = 10_000_000;
export const API_CONFIG_MIN_CONTEXT_WINDOW_TOKENS = 1_024;
export const API_CONFIG_MAX_CONTEXT_WINDOW_TOKENS = 10_000_000;
export const PROJECT_CARD_SUMMARY_MAX_CHARS = 50;

export const statusLabels: Record<ProjectStatus, string> = {
  planning: "构思中",
  drafting: "写作中",
  revising: "修订中",
  completed: "已完成",
};

export const emptyDraft: ProjectInput = {
  title: "",
  subtitle: "",
  description: "",
  genre: "",
  status: "drafting",
};

export function formatProjectCardSummary(text: string) {
  const normalized = text.trim().replace(/\s+/g, " ");
  const chars = Array.from(normalized);

  if (chars.length <= PROJECT_CARD_SUMMARY_MAX_CHARS) {
    return normalized;
  }

  return `${chars.slice(0, PROJECT_CARD_SUMMARY_MAX_CHARS).join("").trimEnd()}...`;
}

export function toApiConfigInput(config: ApiConfig): ApiConfigInput {
  return {
    name: config.name,
    provider: config.provider,
    kind: config.kind,
    protocol: config.protocol,
    base_url: config.base_url,
    api_key_required: config.api_key_required,
    mode: "non_stream",
    model: config.model,
    thinking_enabled: config.thinking_enabled,
    reasoning_effort: config.reasoning_effort,
    max_tokens: config.max_tokens,
    context_window_tokens: config.context_window_tokens,
    temperature: config.temperature,
    top_p: config.top_p,
    top_k: config.top_k,
    dimensions: config.dimensions,
    is_default: config.is_default,
    api_key: null,
    clear_api_key: false,
  };
}

export function templateToApiConfigInput(template?: ApiConfigTemplate): ApiConfigInput {
  if (!template) {
    return defaultApiConfigInput;
  }
  return {
    name: template.name,
    provider: template.provider,
    kind: template.kind,
    protocol: template.protocol,
    base_url: template.base_url,
    api_key_required: template.api_key_required,
    mode: "non_stream",
    model: template.model,
    thinking_enabled: template.thinking_enabled,
    reasoning_effort: template.reasoning_effort,
    max_tokens: template.max_tokens,
    context_window_tokens: template.context_window_tokens,
    temperature: template.temperature,
    top_p: template.top_p,
    top_k: template.top_k,
    dimensions: template.dimensions,
    is_default: false,
    api_key: null,
    clear_api_key: false,
  };
}

export function applyTemplate(
  draft: ApiConfigInput,
  template?: ApiConfigTemplate,
): ApiConfigInput {
  return {
    ...templateToApiConfigInput(template),
    is_default: draft.is_default,
    api_key: draft.api_key,
    clear_api_key: draft.clear_api_key,
  };
}

export function findTemplate(
  templates: ApiConfigTemplate[],
  provider: ApiProvider,
  kind: ApiConfigKind,
): ApiConfigTemplate | undefined {
  return (
    templates.find((template) => template.provider === provider && template.kind === kind) ??
    templates.find((template) => template.provider === provider) ??
    templates[0]
  );
}

export function uniqueProviders(templates: ApiConfigTemplate[]) {
  return Array.from(new Set(templates.map((template) => template.provider)));
}

export function uniqueKinds(templates: ApiConfigTemplate[], provider: ApiProvider) {
  return Array.from(
    new Set(
      templates
        .filter((template) => template.provider === provider)
        .map((template) => template.kind),
    ),
  );
}

export function normalizeApiConfigInput(input: ApiConfigInput): ApiConfigInput {
  return {
    ...input,
    name: input.name.trim(),
    mode: "non_stream",
    base_url: input.base_url.trim(),
    model: input.model.trim(),
    api_key: input.api_key?.trim() || null,
    dimensions:
      input.dimensions === null ? null : clampInteger(input.dimensions, 1, 32768),
    max_tokens: clampInteger(input.max_tokens, API_CONFIG_MIN_TOKENS, API_CONFIG_MAX_TOKENS),
    context_window_tokens: clampInteger(
      input.context_window_tokens,
      API_CONFIG_MIN_CONTEXT_WINDOW_TOKENS,
      API_CONFIG_MAX_CONTEXT_WINDOW_TOKENS,
    ),
    temperature: input.temperature === null ? null : clampNumber(input.temperature, 0, 2),
    top_p: input.top_p === null ? null : clampNumber(input.top_p, 0, 1),
    top_k: input.top_k === null ? null : clampInteger(input.top_k, 1, 1000),
  };
}

export function normalizeVersionSettings(settings: VersionSettings): VersionSettings {
  return {
    ...settings,
    auto_interval_minutes: clampInteger(settings.auto_interval_minutes, 1, 240),
    auto_min_chars_changed: clampInteger(settings.auto_min_chars_changed, 1, 10000),
    auto_min_change_ratio: clampNumber(settings.auto_min_change_ratio, 0, 1),
  };
}

export function sortApiConfigs(left: ApiConfig, right: ApiConfig) {
  if (left.kind !== right.kind) {
    return left.kind === "llm" ? -1 : 1;
  }
  if (left.is_default !== right.is_default) {
    return left.is_default ? -1 : 1;
  }
  return (
    (right.updated_at ?? "").localeCompare(left.updated_at ?? "") ||
    left.name.localeCompare(right.name)
  );
}

export function clampInteger(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, Number.isFinite(value) ? Math.round(value) : min));
}

export function clampNumber(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, Number.isFinite(value) ? value : min));
}

export function kindLabel(kind: ApiConfigKind) {
  return kind === "embedding" ? "Embedding" : "LLM";
}

export function providerLabel(provider: ApiProvider, templates: ApiConfigTemplate[]) {
  return (
    templates.find((template) => template.provider === provider)?.provider_label ?? provider
  );
}

export function providerName(provider: ApiProvider) {
  const labels: Record<ApiProvider, string> = {
    deepseek: "DeepSeek",
    openai: "OpenAI",
    gemini: "Gemini",
    grok: "Grok",
    siliconflow: "SiliconFlow",
    ollama: "Ollama",
    lm_studio: "LM Studio",
    vllm: "vLLM",
  };
  return labels[provider] ?? provider;
}

export function apiHealthMetric(result: ApiConfigHealthCheckResult) {
  const latency = result.latency_ms === null ? "延迟未知" : `${result.latency_ms}ms`;
  if (result.kind === "embedding" && result.embedding_dimensions) {
    return `${latency} · ${result.embedding_dimensions} 维`;
  }
  if (result.kind === "llm" && result.json_mode_supported !== null) {
    return `${latency} · JSON ${result.json_mode_supported ? "可用" : "失败"}`;
  }
  return latency;
}

export function normalizeLibrarySnapshot(snapshot: LibrarySnapshot): LibrarySnapshot {
  return {
    ...snapshot,
    projects: snapshot.projects ?? [],
    recent_projects: snapshot.recent_projects ?? [],
    api_configs: snapshot.api_configs ?? [],
    api_config_templates:
      snapshot.api_config_templates?.length ? snapshot.api_config_templates : fallbackApiConfigTemplates,
  };
}

export function formatDate(value: string) {
  return new Date(value).toLocaleDateString("zh-CN");
}

export function formatDateTime(value: string) {
  return new Date(value).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
