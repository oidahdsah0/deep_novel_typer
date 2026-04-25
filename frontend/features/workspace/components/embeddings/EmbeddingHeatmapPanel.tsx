"use client";

import { Activity, RefreshCw } from "lucide-react";
import type { EmbeddingTag, HeatmapResponse } from "@/lib/api/index";
import type { EmbeddingRangeMode } from "@/features/workspace/hooks/useEmbeddingToolbox";
import type { ActiveResource, ChapterSelection } from "@/features/workspace/types";
import { formatCacheStats, formatScore } from "./embeddingDisplay";

type EmbeddingHeatmapPanelProps = {
  activeHeatmapTagId: string | null;
  activeSelection: ChapterSelection | null;
  heatmap: HeatmapResponse | null;
  isAnalyzing: boolean;
  isHeatmapVisible: boolean;
  onActiveHeatmapTagChange: (tagId: string | null) => void;
  onAnalyze: () => void;
  onHeatmapVisibleChange: (visible: boolean) => void;
  onRangeModeChange: (mode: EmbeddingRangeMode) => void;
  onToggleTag: (tagId: string) => void;
  rangeMode: EmbeddingRangeMode;
  resource: ActiveResource;
  selectedTagIds: string[];
  tags: EmbeddingTag[];
};

export function EmbeddingHeatmapPanel({
  activeHeatmapTagId,
  activeSelection,
  heatmap,
  isAnalyzing,
  isHeatmapVisible,
  onActiveHeatmapTagChange,
  onAnalyze,
  onHeatmapVisibleChange,
  onRangeModeChange,
  onToggleTag,
  rangeMode,
  resource,
  selectedTagIds,
  tags,
}: EmbeddingHeatmapPanelProps) {
  const selectedTags = tags.filter((tag) => selectedTagIds.includes(tag.id));
  const canUseSelection = Boolean(activeSelection);

  return (
    <div className="embedding-panel-stack">
      <div className="embedding-resource-line">
        <span>{resource.type === "chapter" ? "章节" : "资料"}</span>
        <strong>{resource.title}</strong>
      </div>

      <div className="embedding-segmented" aria-label="分析范围">
        <button
          className={rangeMode === "full" ? "active" : ""}
          onClick={() => onRangeModeChange("full")}
          type="button"
        >
          全文
        </button>
        <button
          className={rangeMode === "selection" ? "active" : ""}
          disabled={!canUseSelection}
          onClick={() => onRangeModeChange("selection")}
          type="button"
        >
          选区
        </button>
      </div>

      <div className="embedding-tag-pick-list">
        {tags.map((tag) => (
          <label className="embedding-tag-pick" key={tag.id}>
            <input
              checked={selectedTagIds.includes(tag.id)}
              onChange={() => onToggleTag(tag.id)}
              type="checkbox"
            />
            <i style={{ backgroundColor: tag.color }} />
            <span>{tag.name}</span>
          </label>
        ))}
      </div>

      <button
        className="primary-button embedding-analyze-button"
        disabled={isAnalyzing || selectedTags.length === 0}
        onClick={onAnalyze}
        type="button"
      >
        {isAnalyzing ? <RefreshCw size={15} /> : <Activity size={15} />}
        {isAnalyzing ? "分析中" : "分析"}
      </button>

      {heatmap ? (
        <HeatmapResult
          activeHeatmapTagId={activeHeatmapTagId}
          heatmap={heatmap}
          isHeatmapVisible={isHeatmapVisible}
          onActiveHeatmapTagChange={onActiveHeatmapTagChange}
          onHeatmapVisibleChange={onHeatmapVisibleChange}
        />
      ) : null}
    </div>
  );
}

function HeatmapResult({
  activeHeatmapTagId,
  heatmap,
  isHeatmapVisible,
  onActiveHeatmapTagChange,
  onHeatmapVisibleChange,
}: {
  activeHeatmapTagId: string | null;
  heatmap: HeatmapResponse;
  isHeatmapVisible: boolean;
  onActiveHeatmapTagChange: (tagId: string | null) => void;
  onHeatmapVisibleChange: (visible: boolean) => void;
}) {
  const previewItems = heatmap.items.slice(0, 12);

  return (
    <section className="embedding-result-block">
      <div className="embedding-run-summary">
        <span>{heatmap.run_id}</span>
        <strong>{heatmap.items.length} 片段</strong>
        <span>{formatCacheStats(heatmap.token_cache.cache_hit_count, heatmap.token_cache.cache_miss_count)}</span>
      </div>
      <label className="embedding-check-row">
        <input
          checked={isHeatmapVisible}
          onChange={(event) => onHeatmapVisibleChange(event.target.checked)}
          type="checkbox"
        />
        <span>显示正文热图</span>
      </label>
      <select
        value={activeHeatmapTagId ?? ""}
        onChange={(event) => onActiveHeatmapTagChange(event.target.value || null)}
      >
        <option value="">最近标签</option>
        {heatmap.tags.map((tag) => (
          <option key={tag.id} value={tag.id}>
            {tag.name}
          </option>
        ))}
      </select>
      {heatmap.warnings.map((warning) => (
        <p className="embedding-warning" key={warning}>{warning}</p>
      ))}
      <div className="embedding-token-list">
        {previewItems.map((item) => {
          const tagId = activeHeatmapTagId ?? item.nearest_tag_id;
          const score = tagId ? item.scores[tagId] : null;
          return (
            <span key={`${item.token_index}-${item.start_offset}`}>
              <b>{item.text}</b>
              {score ? <small>{formatScore(score, heatmap.algorithm)}</small> : null}
            </span>
          );
        })}
      </div>
    </section>
  );
}
