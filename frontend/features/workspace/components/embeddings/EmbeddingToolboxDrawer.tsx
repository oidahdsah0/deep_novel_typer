"use client";

import { Activity, ListChecks, Settings, Tags, X } from "lucide-react";
import type { ReactNode } from "react";
import type { EmbeddingToolboxApi } from "@/features/workspace/hooks/useEmbeddingToolbox";
import type { ActiveResource, ChapterSelection } from "@/features/workspace/types";
import { EmbeddingClusterPanel } from "./EmbeddingClusterPanel";
import { EmbeddingHeatmapPanel } from "./EmbeddingHeatmapPanel";
import { EmbeddingSettingsPanel } from "./EmbeddingSettingsPanel";
import { EmbeddingTagManager } from "./EmbeddingTagManager";
import { useDraggableToolbox } from "@/features/workspace/hooks/useDraggableToolbox";

type EmbeddingToolboxDrawerProps = {
  activeSelection: ChapterSelection | null;
  onFocusTextRange: (start: number, end: number) => void;
  resource: ActiveResource;
  toolbox: EmbeddingToolboxApi;
};

export function EmbeddingToolboxDrawer({
  activeSelection,
  onFocusTextRange,
  resource,
  toolbox,
}: EmbeddingToolboxDrawerProps) {
  const { dragHandlers, drawerRef, drawerStyle, isDragging } = useDraggableToolbox(toolbox.isOpen);

  if (!toolbox.isOpen) return null;

  return (
    <aside
      aria-label="Embedding 工具箱"
      className={`embedding-toolbox-drawer${isDragging ? " is-dragging" : ""}`}
      ref={drawerRef}
      style={drawerStyle}
    >
      <header
        className="embedding-toolbox-header"
        {...dragHandlers}
      >
        <div>
          <p className="eyebrow">Embedding</p>
          <h2>语义工具箱</h2>
        </div>
        <button
          aria-label="关闭 Embedding 工具箱"
          className="icon-button"
          onClick={() => toolbox.setIsOpen(false)}
          type="button"
        >
          <X size={17} />
        </button>
      </header>

      <nav className="embedding-toolbox-tabs" aria-label="Embedding 工具箱视图">
        <TabButton
          active={toolbox.activeTab === "heatmap"}
          icon={<Activity size={15} />}
          label="热图"
          onClick={() => toolbox.setActiveTab("heatmap")}
        />
        <TabButton
          active={toolbox.activeTab === "clusters"}
          icon={<ListChecks size={15} />}
          label="语言簇"
          onClick={() => toolbox.setActiveTab("clusters")}
        />
        <TabButton
          active={toolbox.activeTab === "tags"}
          icon={<Tags size={15} />}
          label="标签"
          onClick={() => toolbox.setActiveTab("tags")}
        />
        <TabButton
          active={toolbox.activeTab === "settings"}
          icon={<Settings size={15} />}
          label="设置"
          onClick={() => toolbox.setActiveTab("settings")}
        />
      </nav>

      <div className="embedding-toolbox-body">
        {toolbox.error ? <p className="embedding-message error">{toolbox.error}</p> : null}
        {toolbox.notice ? <p className="embedding-message">{toolbox.notice}</p> : null}
        {toolbox.activeTab === "heatmap" ? (
          <EmbeddingHeatmapPanel
            activeHeatmapTagId={toolbox.activeHeatmapTagId}
            activeSelection={activeSelection}
            heatmap={toolbox.heatmap}
            isAnalyzing={toolbox.isAnalyzing}
            isHeatmapVisible={toolbox.isHeatmapVisible}
            onActiveHeatmapTagChange={toolbox.setActiveHeatmapTagId}
            onAnalyze={() => void toolbox.analyzeHeatmap()}
            onHeatmapVisibleChange={toolbox.setIsHeatmapVisible}
            onRangeModeChange={toolbox.setRangeMode}
            onToggleTag={toolbox.toggleSelectedTag}
            rangeMode={toolbox.rangeMode}
            resource={resource}
            selectedTagIds={toolbox.selectedTagIds}
            tags={toolbox.tags}
          />
        ) : null}
        {toolbox.activeTab === "clusters" ? (
          <EmbeddingClusterPanel
            activeClusterTagId={toolbox.activeClusterTagId}
            activeSelection={activeSelection}
            clusters={toolbox.clusters}
            isAnalyzing={toolbox.isAnalyzing}
            isMapOpen={toolbox.isClusterMapOpen}
            onActiveClusterTagChange={toolbox.setActiveClusterTagId}
            onAnalyze={() => void toolbox.analyzeClusters()}
            onFocusPoint={(point) => onFocusTextRange(point.start_offset, point.end_offset)}
            onMapOpenChange={toolbox.setIsClusterMapOpen}
            onRangeModeChange={toolbox.setRangeMode}
            onToggleTag={toolbox.toggleSelectedTag}
            rangeMode={toolbox.rangeMode}
            resource={resource}
            selectedTagIds={toolbox.selectedTagIds}
            tags={toolbox.tags}
          />
        ) : null}
        {toolbox.activeTab === "tags" ? (
          <EmbeddingTagManager
            isSaving={toolbox.isSavingTag}
            onCreate={toolbox.saveNewTag}
            onDelete={toolbox.removeTag}
            onUpdate={toolbox.saveTag}
            tags={toolbox.tags}
          />
        ) : null}
        {toolbox.activeTab === "settings" ? (
          <EmbeddingSettingsPanel
            algorithm={toolbox.draftSettings.algorithm}
            embeddingConfigs={toolbox.embeddingConfigs}
            hasUnsavedSettings={toolbox.hasUnsavedSettings}
            isLoading={toolbox.isLoadingSettings}
            isSaving={toolbox.isSavingSettings || toolbox.isAnalyzing}
            onAlgorithmChange={(algorithm) =>
              toolbox.setDraftSettings((current) => ({ ...current, algorithm }))
            }
            onConfigChange={(selectedApiConfigId) =>
              toolbox.setDraftSettings((current) => ({ ...current, selectedApiConfigId }))
            }
            onRegenerateVectors={() => void toolbox.saveSettingsAndReembed()}
            onSegmentationChange={(segmentationMode) =>
              toolbox.setDraftSettings((current) => ({ ...current, segmentationMode }))
            }
            onSegmentSizeChange={(segmentSize) =>
              toolbox.setDraftSettings((current) => ({ ...current, segmentSize }))
            }
            segmentationMode={toolbox.draftSettings.segmentationMode}
            segmentSize={toolbox.draftSettings.segmentSize}
            selectedApiConfigId={toolbox.draftSettings.selectedApiConfigId}
          />
        ) : null}
      </div>
    </aside>
  );
}

function TabButton({
  active,
  icon,
  label,
  onClick,
}: {
  active: boolean;
  icon: ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button className={active ? "active" : ""} onClick={onClick} type="button">
      {icon}
      {label}
    </button>
  );
}
