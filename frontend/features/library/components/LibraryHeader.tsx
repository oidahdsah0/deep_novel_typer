"use client";

import {
  Bug,
  Check,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Upload,
} from "lucide-react";
import type { RefObject } from "react";
import { ModelQueueMenu } from "@/features/model-queue/ModelQueueMenu";
import type { LibraryPanel } from "@/features/library/types";

type LibraryHeaderProps = {
  activePanel: LibraryPanel;
  importInputRef: RefObject<HTMLInputElement | null>;
  isDetailVisible: boolean;
  isPending: boolean;
  isSidebarVisible: boolean;
  onDebugOpen: () => void;
  onImport: (file: File | null) => void;
  onToggleDetail: () => void;
  onToggleSidebar: () => void;
};

const headerCopy: Record<LibraryPanel, { eyebrow: string; title: string }> = {
  projects: { eyebrow: "Library", title: "所有小说" },
  "api-configs": { eyebrow: "API Configs", title: "固定 API 配置" },
  "save-settings": { eyebrow: "Versioning", title: "保存与版本" },
  "shortcut-settings": { eyebrow: "Keyboard", title: "快捷键设置" },
};

export function LibraryHeader({
  activePanel,
  importInputRef,
  isDetailVisible,
  isPending,
  isSidebarVisible,
  onDebugOpen,
  onImport,
  onToggleDetail,
  onToggleSidebar,
}: LibraryHeaderProps) {
  const copy = headerCopy[activePanel];
  const sidebarLabel = isSidebarVisible ? "隐藏左侧栏" : "显示左侧栏";
  const detailLabel = isDetailVisible ? "隐藏右侧栏" : "显示右侧栏";

  return (
    <header className="library-header">
      <div className="library-titlebar">
        <button
          aria-label={sidebarLabel}
          aria-pressed={isSidebarVisible}
          className={railToggleClass(isSidebarVisible, "start")}
          data-tooltip={sidebarLabel}
          onClick={onToggleSidebar}
          type="button"
        >
          {isSidebarVisible ? <PanelLeftClose size={17} /> : <PanelLeftOpen size={17} />}
        </button>
        <div>
          <p className="eyebrow">{copy.eyebrow}</p>
          <h2>{copy.title}</h2>
        </div>
      </div>
      <div className="library-header-actions">
        <span className="save-state saved">
          <Check size={15} />
          {isPending ? "处理中" : "就绪"}
        </span>
        <button
          aria-label="Debug"
          className="icon-button icon-tooltip"
          data-tooltip="Debug 控制台"
          onClick={onDebugOpen}
          type="button"
        >
          <Bug size={16} />
        </button>
        <ModelQueueMenu variant="square" />
        <button
          aria-label="导入项目备份"
          className="icon-button icon-tooltip"
          data-tooltip="导入项目备份"
          onClick={() => importInputRef.current?.click()}
          type="button"
        >
          <Upload size={16} />
        </button>
        <input
          ref={importInputRef}
          accept=".zip,application/zip"
          aria-label="选择项目备份文件"
          className="visually-hidden-file-input"
          onChange={(event) => {
            onImport(event.target.files?.[0] ?? null);
            event.currentTarget.value = "";
          }}
          type="file"
        />
        <button
          aria-label={detailLabel}
          aria-pressed={isDetailVisible}
          className={railToggleClass(isDetailVisible, "end")}
          data-tooltip={detailLabel}
          onClick={onToggleDetail}
          type="button"
        >
          {isDetailVisible ? <PanelRightClose size={17} /> : <PanelRightOpen size={17} />}
        </button>
      </div>
    </header>
  );
}

function railToggleClass(active: boolean, align: "start" | "end") {
  return [
    "icon-button",
    "icon-tooltip",
    `tooltip-align-${align}`,
    "library-rail-toggle",
    active ? "active" : "",
  ].filter(Boolean).join(" ");
}
