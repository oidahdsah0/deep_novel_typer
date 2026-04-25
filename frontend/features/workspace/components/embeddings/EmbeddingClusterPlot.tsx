"use client";

import type { ClusterPoint, ClusterResponse } from "@/lib/api/index";

const MAX_RENDERED_POINTS = 600;

type EmbeddingClusterPlotProps = {
  activeTagId: string | null;
  clusters: ClusterResponse;
  onActiveTagChange: (tagId: string | null) => void;
  onPointSelect: (point: ClusterPoint) => void;
};

export function EmbeddingClusterPlot({
  activeTagId,
  clusters,
  onActiveTagChange,
  onPointSelect,
}: EmbeddingClusterPlotProps) {
  const filteredPoints = activeTagId
    ? clusters.points.filter((point) => point.tag_id === activeTagId)
    : clusters.points;
  const visiblePoints = filteredPoints.slice(0, MAX_RENDERED_POINTS);
  const anchorsByTag = new Map(clusters.tag_anchors.map((anchor) => [anchor.tag_id, anchor]));

  return (
    <div className="embedding-cluster-plot">
      <svg role="img" viewBox="0 0 100 100" aria-label="语言簇散点图">
        <g className="embedding-cluster-grid">
          <line x1="50" x2="50" y1="8" y2="92" />
          <line x1="8" x2="92" y1="50" y2="50" />
        </g>
        {visiblePoints.map((point) => {
          const anchor = anchorsByTag.get(point.tag_id);
          const dimmed = Boolean(activeTagId && point.tag_id !== activeTagId);
          return (
            <circle
              aria-label={point.text}
              className={dimmed ? "dimmed" : ""}
              cx={projectAxis(point.x)}
              cy={projectAxis(-point.y)}
              fill={anchor?.color ?? "#59677f"}
              key={`${point.token_index}-${point.start_offset}`}
              onClick={() => onPointSelect(point)}
              r={2.1 + Math.min(1.4, point.closeness)}
            />
          );
        })}
        {clusters.tag_anchors.map((anchor) => (
          <g
            className="embedding-cluster-anchor"
            key={anchor.tag_id}
            onClick={() => onActiveTagChange(activeTagId === anchor.tag_id ? null : anchor.tag_id)}
            transform={`translate(${projectAxis(anchor.x)} ${projectAxis(-anchor.y)})`}
          >
            <circle fill={anchor.color} r="4.4" />
            <text x="6" y="3">{anchor.name}</text>
          </g>
        ))}
      </svg>
      {filteredPoints.length > visiblePoints.length ? (
        <p className="embedding-plot-note">
          显示 {visiblePoints.length} / {filteredPoints.length} 个点
        </p>
      ) : null}
    </div>
  );
}

function projectAxis(value: number) {
  const clamped = Math.max(-1, Math.min(1, Number.isFinite(value) ? value : 0));
  return 50 + clamped * 40;
}
