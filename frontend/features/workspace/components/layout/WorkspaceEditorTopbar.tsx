"use client";

import {
  AlertCircle,
  BrainCircuit,
  Bug,
  Check,
  Clock3,
  FileDown,
  History,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Pilcrow,
  RefreshCw,
  Upload,
  WandSparkles,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { ModelQueueMenu } from "@/features/model-queue/ModelQueueMenu";
import type { ActiveResource, SaveState } from "@/features/workspace/types";
import { formatDate } from "@/features/workspace/utils";

type WorkspaceEditorTopbarProps = {
  activeWordCountLabel: string;
  debugHref: string;
  isInsightRailVisible: boolean;
  isEmbeddingToolboxOpen: boolean;
  isProjectRailVisible: boolean;
  isTypewriterToolboxOpen: boolean;
  onOpenDocxExport: () => void;
  onOpenPromptManager: () => void;
  onOpenVersionDialog: () => void;
  onOverwriteConflict: () => void;
  onReloadConflict: () => void;
  onToggleEmbeddingToolbox: () => void;
  onToggleTypewriterToolbox: () => void;
  onSetInsightRailVisible: (next: (current: boolean) => boolean) => void;
  onSetProjectRailVisible: (next: (current: boolean) => boolean) => void;
  projectSubtitle: string;
  projectUpdatedAt: string;
  resource: ActiveResource;
  saveState: SaveState;
  statusLabel: string;
};

export function WorkspaceEditorTopbar({
  activeWordCountLabel,
  debugHref,
  isInsightRailVisible,
  isEmbeddingToolboxOpen,
  isProjectRailVisible,
  isTypewriterToolboxOpen,
  onOpenDocxExport,
  onOpenPromptManager,
  onOpenVersionDialog,
  onOverwriteConflict,
  onReloadConflict,
  onToggleEmbeddingToolbox,
  onToggleTypewriterToolbox,
  onSetInsightRailVisible,
  onSetProjectRailVisible,
  projectSubtitle,
  projectUpdatedAt,
  resource,
  saveState,
  statusLabel,
}: WorkspaceEditorTopbarProps) {
  const updatedAtLabel = formatDate(projectUpdatedAt);
  const saveTooltip = `${statusLabel} · ${updatedAtLabel}`;
  const eyebrowLabel = resource.type === "chapter" ? projectSubtitle.trim() : "Project Document";

  return (
    <header className="editor-topbar">
      <div className="editor-titlebar">
        <RailToggle
          active={isProjectRailVisible}
          activeIcon={<PanelLeftClose size={17} />}
          inactiveIcon={<PanelLeftOpen size={17} />}
          label={isProjectRailVisible ? "隐藏左侧栏" : "显示左侧栏"}
          onClick={() => onSetProjectRailVisible((current) => !current)}
          side="left"
        />
        <div className="editor-title-copy">
          {eyebrowLabel ? <p className="eyebrow">{eyebrowLabel}</p> : null}
          <div className="editor-title-row">
            <h2>{resource.title}</h2>
            <span className="editor-title-word-count">{activeWordCountLabel}</span>
          </div>
        </div>
      </div>
      <div className="editor-topbar-actions">
        <div className="editor-tool-buttons" aria-label="编辑器工具">
          <TopbarIconButton label="导出正文 DOCX" onClick={onOpenDocxExport}>
            <FileDown size={16} />
          </TopbarIconButton>
          <TopbarIconButton label="请求管理" onClick={onOpenPromptManager}>
            <WandSparkles size={16} />
          </TopbarIconButton>
          <button
            aria-label={isTypewriterToolboxOpen ? "关闭排版工具箱" : "打开排版工具箱"}
            aria-pressed={isTypewriterToolboxOpen}
            className={isTypewriterToolboxOpen ? "icon-button icon-tooltip active" : "icon-button icon-tooltip"}
            data-tooltip={isTypewriterToolboxOpen ? "关闭排版工具箱" : "打开排版工具箱"}
            onClick={onToggleTypewriterToolbox}
            type="button"
          >
            <Pilcrow size={16} />
          </button>
          <button
            aria-label={isEmbeddingToolboxOpen ? "关闭 Embedding 工具箱" : "打开 Embedding 工具箱"}
            aria-pressed={isEmbeddingToolboxOpen}
            className={isEmbeddingToolboxOpen ? "icon-button icon-tooltip active" : "icon-button icon-tooltip"}
            data-tooltip={isEmbeddingToolboxOpen ? "关闭语义工具箱" : "打开语义工具箱"}
            onClick={onToggleEmbeddingToolbox}
            type="button"
          >
            <BrainCircuit size={16} />
          </button>
          <Link className="icon-button icon-tooltip" href={debugHref} aria-label="Debug" data-tooltip="Debug 控制台">
            <Bug size={16} />
          </Link>
          <ModelQueueMenu variant="square" />
          <button
            aria-label="历史版本"
            className="icon-button icon-tooltip"
            data-tooltip="历史版本"
            onClick={onOpenVersionDialog}
            type="button"
          >
            <History size={16} />
          </button>
          {saveState === "conflict" ? (
            <>
              <TopbarIconButton label="重新加载当前资源，丢弃本地改动" onClick={onReloadConflict}>
                <RefreshCw size={16} />
              </TopbarIconButton>
              <TopbarIconButton label="用当前内容覆盖远端版本" onClick={onOverwriteConflict}>
                <Upload size={16} />
              </TopbarIconButton>
            </>
          ) : null}
        </div>
        <div className="editor-stats" aria-label="章节状态">
          <span
            aria-label={saveTooltip}
            className={`icon-button icon-tooltip editor-save-compact save-state ${saveState}`}
            data-tooltip={saveTooltip}
            role="status"
            tabIndex={0}
          >
            <SaveStateIcon saveState={saveState} />
          </span>
          <span className={`save-state editor-stat-save ${saveState}`}>
            <Check size={15} />
            {statusLabel}
          </span>
          <span className="editor-stat-date">
            <Clock3 size={15} />
            {updatedAtLabel}
          </span>
        </div>
        <RailToggle
          active={isInsightRailVisible}
          activeIcon={<PanelRightClose size={17} />}
          inactiveIcon={<PanelRightOpen size={17} />}
          label={isInsightRailVisible ? "隐藏右侧栏" : "显示右侧栏"}
          onClick={() => onSetInsightRailVisible((current) => !current)}
          side="right"
        />
      </div>
    </header>
  );
}

function SaveStateIcon({ saveState }: { saveState: SaveState }) {
  if (saveState === "saving") {
    return <Clock3 size={15} />;
  }
  if (saveState === "error" || saveState === "conflict") {
    return <AlertCircle size={15} />;
  }
  return <Check size={15} />;
}

function TopbarIconButton({
  children,
  label,
  onClick,
}: {
  children: ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      aria-label={label}
      className="icon-button icon-tooltip"
      data-tooltip={label}
      onClick={onClick}
      type="button"
    >
      {children}
    </button>
  );
}

function RailToggle({
  active,
  activeIcon,
  inactiveIcon,
  label,
  onClick,
  side,
}: {
  active: boolean;
  activeIcon: ReactNode;
  inactiveIcon: ReactNode;
  label: string;
  onClick: () => void;
  side: "left" | "right";
}) {
  return (
    <button
      aria-label={label}
      aria-pressed={active}
      data-tooltip={label}
      className={
        active
          ? `icon-button icon-tooltip tooltip-align-${side === "left" ? "start" : "end"} editor-rail-toggle editor-${side}-rail-toggle active`
          : `icon-button icon-tooltip tooltip-align-${side === "left" ? "start" : "end"} editor-rail-toggle editor-${side}-rail-toggle`
      }
      onClick={onClick}
      type="button"
    >
      {active ? activeIcon : inactiveIcon}
    </button>
  );
}
