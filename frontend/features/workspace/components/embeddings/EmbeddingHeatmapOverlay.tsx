"use client";

import type { HeatmapResponse } from "@/lib/api/index";
import type { HeatmapScaleHover } from "./useEditorHeatmap";

type EmbeddingHeatmapOverlayProps = {
  heatmap: HeatmapResponse | null;
  hover: HeatmapScaleHover | null;
};

export function EmbeddingHeatmapOverlay({
  heatmap,
  hover,
}: EmbeddingHeatmapOverlayProps) {
  if (!heatmap || heatmap.resource_type !== "chapter" || heatmap.items.length === 0) {
    return null;
  }
  return <HeatmapScale hover={hover} />;
}

function HeatmapScale({ hover }: { hover: HeatmapScaleHover | null }) {
  return (
    <div className="writing-heatmap-scale">
      <div className="writing-heatmap-scale-header">
        <span>接近度</span>
        {hover ? (
          <strong>
            {hover.label} · {hover.tagName} · {hover.percentage}%
          </strong>
        ) : null}
      </div>
      <div className="writing-heatmap-scale-track">
        {hover ? (
          <i
            className="writing-heatmap-scale-marker"
            style={{ left: `${hover.percentage}%` }}
          />
        ) : null}
      </div>
      <div className="writing-heatmap-scale-ticks">
        <span>远 0</span>
        <span>50</span>
        <span>近 100</span>
      </div>
    </div>
  );
}
