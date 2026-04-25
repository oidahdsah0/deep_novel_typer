export type DebugDetailTab =
  | "summary"
  | "context"
  | "system"
  | "user"
  | "options"
  | "request"
  | "response"
  | "parsed";

export const requestTypeLabels: Record<string, string> = {
  perspective_suggestion: "视角建议",
  polish_selection: "润色选中",
  quick_generate_next_paragraph: "快速生成下一段",
  generate_next_paragraph: "生成下一段落",
  generate_next_section: "生成下一部分",
  generate_chapter_blueprint: "章节基础铺设",
  polish_document_selection: "资料润色选区",
  generate_document_continuation: "资料生成后续",
  embedding_heatmap_tags: "Embedding 热图标签",
  embedding_heatmap_tokens: "Embedding 热图分词",
  embedding_clusters_tags: "Embedding 语言簇标签",
  embedding_clusters_tokens: "Embedding 语言簇分词",
};

export const llmDetailTabs: Array<{ id: DebugDetailTab; label: string }> = [
  { id: "summary", label: "摘要" },
  { id: "context", label: "Context" },
  { id: "system", label: "System" },
  { id: "user", label: "User" },
  { id: "options", label: "参数" },
  { id: "request", label: "原始请求" },
  { id: "response", label: "原始返回" },
  { id: "parsed", label: "解析结果" },
];

export const embeddingDetailTabs: Array<{ id: DebugDetailTab; label: string }> = [
  { id: "summary", label: "摘要" },
  { id: "options", label: "参数" },
  { id: "request", label: "脱敏请求" },
  { id: "response", label: "脱敏返回" },
];

export function detailTabsForKind(modelKind: string) {
  return modelKind === "embedding" ? embeddingDetailTabs : llmDetailTabs;
}

export function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatFullDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatTokens(value: number | null) {
  return value === null ? "未返回" : value.toLocaleString("zh-CN");
}

export function buildDebugHref(activeProjectId: string | null, returnProjectId: string | null) {
  if (!activeProjectId && !returnProjectId) {
    return "/debug";
  }
  const params = new URLSearchParams();
  if (activeProjectId) {
    params.set("project_id", activeProjectId);
  }
  if (returnProjectId) {
    params.set("return_project_id", returnProjectId);
  }
  return `/debug?${params.toString()}`;
}
