"use client";

import { AlertCircle, Check, Eye, Sparkles, X } from "lucide-react";
import type { GeneratedDraft, GenerationPreset, GenerationPresetKind } from "@/lib/api/index";
import { presetSaveLabels, sourceLabels } from "../../constants";
import type { PresetSaveState } from "../../types";
import { PresetEditor } from "./PresetEditor";

export function PolishDialog({
  error,
  isGenerating,
  isPreviewing,
  onAccept,
  onAddPreset,
  onChangePolishPreset,
  onChangePresetContent,
  onClose,
  onDeletePreset,
  onDiscard,
  onGenerate,
  onPreview,
  onRenamePreset,
  polishPreset,
  polishPresets,
  presetSaveState,
  result,
  selectedPolishPresetId,
  selectedText,
}: {
  error: string | null;
  isGenerating: boolean;
  isPreviewing: boolean;
  onAccept: () => void;
  onAddPreset: (kind: GenerationPresetKind) => void;
  onChangePolishPreset: (presetId: string) => void;
  onChangePresetContent: (
    kind: GenerationPresetKind,
    preset: GenerationPreset,
    contentValue: string,
  ) => void;
  onClose: () => void;
  onDeletePreset: (preset: GenerationPreset) => void;
  onDiscard: () => void;
  onGenerate: () => void;
  onPreview: () => void;
  onRenamePreset: (preset: GenerationPreset) => void;
  polishPreset: GenerationPreset | undefined;
  polishPresets: GenerationPreset[];
  presetSaveState: PresetSaveState;
  result: GeneratedDraft | null;
  selectedPolishPresetId: string;
  selectedText: string;
}) {
  const canGenerate = Boolean(polishPreset && selectedText.trim() && !isGenerating);

  return (
    <div className="modal-backdrop generation-backdrop" role="presentation">
      <section
        aria-label="润色选中"
        className="settings-dialog generation-dialog polish-dialog"
        role="dialog"
      >
        <header className="settings-heading">
          <div>
            <p className="eyebrow">Selection Polish</p>
            <h2>润色选中</h2>
          </div>
          <button
            aria-label="关闭"
            className="icon-button"
            disabled={isGenerating || Boolean(result)}
            onClick={onClose}
            type="button"
          >
            <X size={18} />
          </button>
        </header>

        <section className="selection-summary" aria-label="当前选区">
          <span>当前选区</span>
          <p>{selectedText}</p>
        </section>

        <PresetEditor
          kind="polish_mode"
          label="润色方式"
          onAddPreset={onAddPreset}
          onChangePreset={onChangePolishPreset}
          onChangePresetContent={onChangePresetContent}
          onDeletePreset={onDeletePreset}
          onRenamePreset={onRenamePreset}
          placeholder="选择润色方式后可直接修改提示词。"
          preset={polishPreset}
          presets={polishPresets}
          selectedPresetId={selectedPolishPresetId}
        />

        {presetSaveState !== "idle" ? (
          <div className={`preset-save-hint ${presetSaveState}`}>
            <Check size={14} />
            {presetSaveLabels[presetSaveState]}
          </div>
        ) : null}

        {error ? (
          <div className="generation-error" role="alert">
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        ) : null}

        {result ? (
          <section className="generated-draft visible" aria-label="润色结果">
            <div className="generated-draft-meta">
              <Sparkles size={14} />
              <span>
                {sourceLabels[result.source]} · {result.model ?? "本地兜底"}
              </span>
            </div>
            <div className="generated-draft-text">{result.text}</div>
          </section>
        ) : null}

        {result ? (
          <div className="dialog-actions">
            <button className="secondary-button" onClick={onDiscard} type="button">
              废弃
            </button>
            <button className="primary-button" onClick={onAccept} type="button">
              <Check size={16} />
              采纳
            </button>
          </div>
        ) : (
          <div className="dialog-actions">
            <button
              className="secondary-button"
              disabled={isGenerating}
              onClick={onClose}
              type="button"
            >
              取消
            </button>
            <button
              className="secondary-button"
              disabled={isPreviewing || isGenerating}
              onClick={onPreview}
              type="button"
            >
              <Eye size={16} />
              {isPreviewing ? "预览中" : "预览"}
            </button>
            <button
              className="primary-button"
              disabled={!canGenerate}
              onClick={onGenerate}
              type="button"
            >
              <Sparkles size={16} />
              {isGenerating ? "润色中" : "生成"}
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
