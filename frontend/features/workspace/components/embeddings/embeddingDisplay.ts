import type {
  ClusterPoint,
  EmbeddingDistanceAlgorithm,
  EmbeddingTag,
  HeatmapItem,
  HeatmapTagScore,
} from "@/lib/api/index";

export function heatmapTokenStyle(
  item: HeatmapItem,
  tagsById: Map<string, EmbeddingTag>,
  activeTagId: string | null,
) {
  const score = activeTagId ? item.scores[activeTagId] : null;
  if (score) {
    return {
      backgroundColor: spectrumColor(score.closeness),
      boxShadow: tokenBorder(spectrumBorder(score.closeness)),
    };
  }
  const tag = item.nearest_tag_id ? tagsById.get(item.nearest_tag_id) : null;
  const closeness = item.nearest_tag_id ? item.scores[item.nearest_tag_id]?.closeness ?? 0 : 0;
  const rgb = hexToRgb(tag?.color ?? "#59677f");
  return {
    backgroundColor: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${0.18 + closeness * 0.34})`,
    boxShadow: tokenBorder(`rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${0.32 + closeness * 0.3})`),
  };
}

export function tokenTitle(
  item: HeatmapItem,
  tagsById: Map<string, EmbeddingTag>,
  activeTagId: string | null,
  algorithm: EmbeddingDistanceAlgorithm,
) {
  const tagId = activeTagId ?? item.nearest_tag_id;
  const score = tagId ? item.scores[tagId] : null;
  const tag = tagId ? tagsById.get(tagId) : null;
  const metric = score ? formatScore(score, algorithm) : "无分数";
  return `${item.text} · ${tag?.name ?? "未匹配"} · ${metric}`;
}

export function formatScore(score: HeatmapTagScore, algorithm: EmbeddingDistanceAlgorithm) {
  const closeness = `${Math.round(score.closeness * 100)}%`;
  if (algorithm === "cosine") {
    return `接近度 ${closeness} · 相似度 ${formatNumber(score.raw_score)}`;
  }
  return `接近度 ${closeness} · 距离 ${formatNumber(score.raw_distance)}`;
}

export function formatClusterMetric(point: ClusterPoint, algorithm: EmbeddingDistanceAlgorithm) {
  const closeness = `${Math.round(point.closeness * 100)}%`;
  if (algorithm === "cosine") {
    return `接近度 ${closeness} · 相似度 ${formatNumber(point.raw_score)}`;
  }
  return `接近度 ${closeness} · 距离 ${formatNumber(point.raw_distance)}`;
}

export function formatCacheStats(hit: number, miss: number) {
  return `${hit} 命中 / ${miss} 请求`;
}

function spectrumColor(closeness: number) {
  const hue = 218 - clamp01(closeness) * 210;
  return `hsla(${hue}, 84%, 58%, ${0.18 + clamp01(closeness) * 0.34})`;
}

function spectrumBorder(closeness: number) {
  const hue = 218 - clamp01(closeness) * 210;
  return `hsla(${hue}, 84%, 42%, ${0.26 + clamp01(closeness) * 0.3})`;
}

function tokenBorder(color: string) {
  return `inset 0 0 0 1px ${color}`;
}

function formatNumber(value: number | null) {
  return value === null ? "无" : value.toFixed(4);
}

function clamp01(value: number) {
  return Math.min(1, Math.max(0, value));
}

function hexToRgb(value: string) {
  const normalized = /^#[0-9a-fA-F]{6}$/.test(value) ? value.slice(1) : "59677f";
  return {
    r: Number.parseInt(normalized.slice(0, 2), 16),
    g: Number.parseInt(normalized.slice(2, 4), 16),
    b: Number.parseInt(normalized.slice(4, 6), 16),
  };
}
