"use client";

import { useMemo, useState } from "react";
import type { EmbeddingTag, HeatmapItem, HeatmapResponse } from "@/lib/api/index";
import type { TypewriterTextHighlight } from "@/features/workspace/components/editor/TypewriterTextEditor";
import { heatmapTokenStyle, tokenTitle } from "./embeddingDisplay";

export type HeatmapScaleHover = {
  label: string;
  percentage: number;
  tagName: string;
};

export function useEditorHeatmap({
  activeTagId,
  content,
  heatmap,
  tags,
}: {
  activeTagId: string | null;
  content: string;
  heatmap: HeatmapResponse | null;
  tags: EmbeddingTag[];
}) {
  const [hoveredHighlightId, setHoveredHighlightId] = useState<string | null>(null);
  const tagsById = useMemo(() => new Map(tags.map((tag) => [tag.id, tag])), [tags]);
  const itemsByHighlightId = useMemo(
    () => new Map((heatmap?.items ?? []).map((item) => [highlightId(item), item])),
    [heatmap],
  );
  const highlights = useMemo(
    () =>
      heatmap?.resource_type === "chapter"
        ? buildHeatmapHighlights(content, heatmap, tagsById, activeTagId)
        : [],
    [activeTagId, content, heatmap, tagsById],
  );
  const hover = useMemo(() => {
    const item = hoveredHighlightId ? itemsByHighlightId.get(hoveredHighlightId) : null;
    return item ? heatmapScaleHover(item, tagsById, activeTagId) : null;
  }, [activeTagId, hoveredHighlightId, itemsByHighlightId, tagsById]);

  return {
    clearHover: () => setHoveredHighlightId(null),
    handleHighlightEnter: setHoveredHighlightId,
    highlights,
    hover,
  };
}

function buildHeatmapHighlights(
  content: string,
  heatmap: HeatmapResponse,
  tagsById: Map<string, EmbeddingTag>,
  activeTagId: string | null,
): TypewriterTextHighlight[] {
  return heatmap.items
    .filter((item) => item.end_offset > item.start_offset)
    .map((item) => ({
      className: "writing-heatmap-token",
      endOffset: Math.min(content.length, item.end_offset),
      id: highlightId(item),
      startOffset: Math.max(0, Math.min(content.length, item.start_offset)),
      style: styleObjectToCssText(heatmapTokenStyle(item, tagsById, activeTagId)),
      title: tokenTitle(item, tagsById, activeTagId, heatmap.algorithm),
    }))
    .filter((highlight) => highlight.endOffset > highlight.startOffset);
}

function heatmapScaleHover(
  item: HeatmapItem,
  tagsById: Map<string, EmbeddingTag>,
  activeTagId: string | null,
): HeatmapScaleHover | null {
  const tagId = activeTagId ?? item.nearest_tag_id;
  if (!tagId) return null;
  const score = tagId ? item.scores[tagId] : null;
  if (!score) return null;
  return {
    label: item.text,
    percentage: Math.round(clamp01(score.closeness) * 100),
    tagName: tagsById.get(tagId)?.name ?? "未匹配",
  };
}

function styleObjectToCssText(style: Record<string, string>) {
  return Object.entries(style)
    .map(([property, value]) => `${toKebabCase(property)}: ${value}`)
    .join("; ");
}

function toKebabCase(value: string) {
  return value.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`);
}

function highlightId(item: HeatmapItem) {
  return `heatmap-${item.token_index}-${item.start_offset}-${item.end_offset}`;
}

function clamp01(value: number) {
  return Math.min(1, Math.max(0, value));
}
