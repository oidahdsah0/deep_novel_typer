"use client";

import { Check, Eye, History, Save } from "lucide-react";
import { presetSaveLabels } from "../../constants";
import type { PresetSaveState } from "../../types";

export function PromptManagerActions({
  isPreviewing,
  onClose,
  onOpenHistory,
  onPreview,
  onSave,
  saveState,
}: {
  isPreviewing: boolean;
  onClose: () => void;
  onOpenHistory: () => void;
  onPreview: () => void;
  onSave: () => void;
  saveState: PresetSaveState;
}) {
  return (
    <div className="dialog-actions">
      {saveState !== "idle" ? (
        <span className={`preset-save-hint ${saveState}`}>
          <Check size={14} />
          {presetSaveLabels[saveState]}
        </span>
      ) : null}
      <button className="secondary-button" onClick={onClose} type="button">
        关闭
      </button>
      <button className="secondary-button" onClick={onOpenHistory} type="button">
        <History size={16} />
        历史
      </button>
      <button
        className="secondary-button"
        disabled={isPreviewing}
        onClick={onPreview}
        type="button"
      >
        <Eye size={16} />
        {isPreviewing ? "预览中" : "预览请求"}
      </button>
      <button className="primary-button" onClick={onSave} type="button">
        <Save size={16} />
        保存请求配置
      </button>
    </div>
  );
}
