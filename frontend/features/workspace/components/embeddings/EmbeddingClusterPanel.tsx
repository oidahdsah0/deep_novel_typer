"use client";

import { Expand, GitFork, RefreshCw } from "lucide-react";
import type { ClusterPoint, ClusterResponse, EmbeddingTag } from "@/lib/api/index";
import type { EmbeddingRangeMode } from "@/features/workspace/hooks/useEmbeddingToolbox";
import type { ActiveResource, ChapterSelection } from "@/features/workspace/types";
import { formatCacheStats, formatClusterMetric } from "./embeddingDisplay";
import { EmbeddingClusterPlot } from "./EmbeddingClusterPlot";

type EmbeddingClusterPanelProps = {
  activeClusterTagId: string | null;
  activeSelection: ChapterSelection | null;
  clusters: ClusterResponse | null;
  isAnalyzing: boolean;
  isMapOpen: boolean;
  onActiveClusterTagChange: (tagId: string | null) => void;
  onAnalyze: () => void;
  onFocusPoint: (point: ClusterPoint) => void;
  onMapOpenChange: (open: boolean) => void;
  onRangeModeChange: (mode: EmbeddingRangeMode) => void;
  onToggleTag: (tagId: string) => void;
  rangeMode: EmbeddingRangeMode;
  resource: ActiveResource;
  selectedTagIds: string[];
  tags: EmbeddingTag[];
};

export function EmbeddingClusterPanel(props: EmbeddingClusterPanelProps) {
  const selectedTags = props.tags.filter((tag) => props.selectedTagIds.includes(tag.id));
  return (
    <div className="embedding-panel-stack">
      <div className="embedding-resource-line">
        <span>{props.resource.type === "chapter" ? "章节" : "资料"}</span>
        <strong>{props.resource.title}</strong>
      </div>
      <RangeButtons
        activeSelection={props.activeSelection}
        onRangeModeChange={props.onRangeModeChange}
        rangeMode={props.rangeMode}
      />
      <TagPickList
        onToggleTag={props.onToggleTag}
        selectedTagIds={props.selectedTagIds}
        tags={props.tags}
      />
      <button
        className="primary-button embedding-analyze-button"
        disabled={props.isAnalyzing || selectedTags.length === 0}
        onClick={props.onAnalyze}
        type="button"
      >
        {props.isAnalyzing ? <RefreshCw size={15} /> : <GitFork size={15} />}
        {props.isAnalyzing ? "分析中" : "分析语言簇"}
      </button>
      {props.clusters ? <ClusterResult {...props} clusters={props.clusters} /> : null}
    </div>
  );
}

function RangeButtons({
  activeSelection,
  onRangeModeChange,
  rangeMode,
}: {
  activeSelection: ChapterSelection | null;
  onRangeModeChange: (mode: EmbeddingRangeMode) => void;
  rangeMode: EmbeddingRangeMode;
}) {
  return (
    <div className="embedding-segmented" aria-label="分析范围">
      <button className={rangeMode === "full" ? "active" : ""} onClick={() => onRangeModeChange("full")} type="button">
        全文
      </button>
      <button
        className={rangeMode === "selection" ? "active" : ""}
        disabled={!activeSelection}
        onClick={() => onRangeModeChange("selection")}
        type="button"
      >
        选区
      </button>
    </div>
  );
}

function TagPickList({
  onToggleTag,
  selectedTagIds,
  tags,
}: {
  onToggleTag: (tagId: string) => void;
  selectedTagIds: string[];
  tags: EmbeddingTag[];
}) {
  return (
    <div className="embedding-tag-pick-list">
      {tags.map((tag) => (
        <label className="embedding-tag-pick" key={tag.id}>
          <input checked={selectedTagIds.includes(tag.id)} onChange={() => onToggleTag(tag.id)} type="checkbox" />
          <i style={{ backgroundColor: tag.color }} />
          <span>{tag.name}</span>
        </label>
      ))}
    </div>
  );
}

function ClusterResult(props: EmbeddingClusterPanelProps & { clusters: ClusterResponse }) {
  const visiblePoints = props.activeClusterTagId
    ? props.clusters.points.filter((point) => point.tag_id === props.activeClusterTagId)
    : props.clusters.points;
  return (
    <section className="embedding-result-block embedding-cluster-result">
      <div className="embedding-run-summary">
        <span>{props.clusters.run_id}</span>
        <strong>{props.clusters.points.length} 点</strong>
        <span>{formatCacheStats(props.clusters.token_cache.cache_hit_count, props.clusters.token_cache.cache_miss_count)}</span>
      </div>
      {props.clusters.warnings.map((warning) => (
        <p className="embedding-warning" key={warning}>{warning}</p>
      ))}
      <select value={props.activeClusterTagId ?? ""} onChange={(event) => props.onActiveClusterTagChange(event.target.value || null)}>
        <option value="">全部簇</option>
        {props.clusters.clusters.map((cluster) => (
          <option key={cluster.cluster_id} value={cluster.tag_id}>{cluster.name}</option>
        ))}
      </select>
      <EmbeddingClusterPlot
        activeTagId={props.activeClusterTagId}
        clusters={props.clusters}
        onActiveTagChange={props.onActiveClusterTagChange}
        onPointSelect={props.onFocusPoint}
      />
      <button className="secondary-button embedding-map-button" onClick={() => props.onMapOpenChange(true)} type="button">
        <Expand size={14} />
        展开图谱
      </button>
      <ClusterStats clusters={props.clusters} onActiveTagChange={props.onActiveClusterTagChange} />
      <PointPreview clusters={props.clusters} onFocusPoint={props.onFocusPoint} points={visiblePoints} />
      {props.isMapOpen ? <ClusterMapDialog {...props} /> : null}
    </section>
  );
}

function ClusterStats({ clusters, onActiveTagChange }: { clusters: ClusterResponse; onActiveTagChange: (tagId: string | null) => void }) {
  return (
    <div className="embedding-cluster-stats">
      {clusters.clusters.map((cluster) => (
        <button key={cluster.cluster_id} onClick={() => onActiveTagChange(cluster.tag_id)} type="button">
          <i style={{ backgroundColor: cluster.color }} />
          <span>{cluster.name}</span>
          <strong>{cluster.point_count}</strong>
        </button>
      ))}
    </div>
  );
}

function PointPreview({
  clusters,
  onFocusPoint,
  points,
}: {
  clusters: ClusterResponse;
  onFocusPoint: (point: ClusterPoint) => void;
  points: ClusterPoint[];
}) {
  const names = new Map(clusters.clusters.map((cluster) => [cluster.tag_id, cluster.name]));
  return (
    <div className="embedding-cluster-point-list">
      {points.slice(0, 10).map((point) => (
        <button key={`${point.token_index}-${point.start_offset}`} onClick={() => onFocusPoint(point)} type="button">
          <b>{point.text}</b>
          <small>{names.get(point.tag_id) ?? point.tag_id} · {formatClusterMetric(point, clusters.algorithm)}</small>
        </button>
      ))}
    </div>
  );
}

function ClusterMapDialog(props: EmbeddingClusterPanelProps & { clusters: ClusterResponse }) {
  return (
    <div className="embedding-map-dialog" role="dialog" aria-modal="true" aria-label="语言簇图谱">
      <div className="embedding-map-dialog-panel">
        <header>
          <strong>{props.resource.title}</strong>
          <button className="secondary-button" onClick={() => props.onMapOpenChange(false)} type="button">关闭</button>
        </header>
        <EmbeddingClusterPlot
          activeTagId={props.activeClusterTagId}
          clusters={props.clusters}
          onActiveTagChange={props.onActiveClusterTagChange}
          onPointSelect={props.onFocusPoint}
        />
        <ClusterStats clusters={props.clusters} onActiveTagChange={props.onActiveClusterTagChange} />
      </div>
    </div>
  );
}
