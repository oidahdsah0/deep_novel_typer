import type { EmbeddingTag, EmbeddingTextRange } from "@/lib/api/index";
import type { ChapterSelection } from "@/features/workspace/types";
import type { EmbeddingRangeMode } from "./embeddingToolboxTypes";

export function reconcileSelectedTags(current: string[], tags: EmbeddingTag[]) {
  const existing = new Set(tags.map((tag) => tag.id));
  const selected = current.filter((id) => existing.has(id));
  return selected.length ? selected : tags.filter((tag) => tag.is_enabled).map((tag) => tag.id);
}

export function analysisRange(
  rangeMode: EmbeddingRangeMode,
  activeSelection: ChapterSelection | null,
): EmbeddingTextRange | null {
  return rangeMode === "selection" && activeSelection
    ? { start_offset: activeSelection.start, end_offset: activeSelection.end }
    : null;
}

export function validateEmbeddingAnalysis(
  selectedApiConfigId: string,
  selectedTagIds: string[],
  rangeMode: EmbeddingRangeMode,
  activeSelection: ChapterSelection | null,
) {
  if (!selectedApiConfigId) return "没有可用的 Embedding API 配置";
  if (selectedTagIds.length === 0) return "至少选择一个语义标签";
  if (rangeMode === "selection" && !activeSelection) return "当前没有可分析的选区";
  return null;
}

export function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Embedding 请求失败";
}
