"use client";

import { AlertCircle, Check, Eye, Sparkles, WandSparkles, X } from "lucide-react";
import type { GeneratedDraft, GenerationPreset, GenerationPresetKind } from "@/lib/api/index";
import { documentActionLabels, presetSaveLabels, sourceLabels } from "../../constants";
import type { DocumentGenerationAction, PresetSaveState } from "../../types";
import { PresetEditor } from "./PresetEditor";

export function DocumentGenerationDialog({
  action,
  documentGenerationPreset,
  documentGenerationPresets,
  documentPolishPreset,
  documentPolishPresets,
  editorPreset,
  editorPresets,
  error,
  isGenerating,
  isPreviewing,
  onAccept,
  onAddPreset,
  onChangeDocumentGenerationPreset,
  onChangeDocumentPolishPreset,
  onChangeEditorPreset,
  onChangePresetContent,
  onClose,
  onDeletePreset,
  onDiscard,
  onGenerate,
  onPreview,
  onRenamePreset,
  presetSaveState,
  result,
  selectedDocumentGenerationPresetId,
  selectedDocumentPolishPresetId,
  selectedEditorPresetId,
  selectedText,
}: {
  action: DocumentGenerationAction;
  documentGenerationPreset: GenerationPreset | undefined;
  documentGenerationPresets: GenerationPreset[];
  documentPolishPreset: GenerationPreset | undefined;
  documentPolishPresets: GenerationPreset[];
  editorPreset: GenerationPreset | undefined;
  editorPresets: GenerationPreset[];
  error: string | null;
  isGenerating: boolean;
  isPreviewing: boolean;
  onAccept: () => void;
  onAddPreset: (kind: GenerationPresetKind) => void;
  onChangeDocumentGenerationPreset: (presetId: string) => void;
  onChangeDocumentPolishPreset: (presetId: string) => void;
  onChangeEditorPreset: (presetId: string) => void;
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
  presetSaveState: PresetSaveState;
  result: GeneratedDraft | null;
  selectedDocumentGenerationPresetId: string;
  selectedDocumentPolishPresetId: string;
  selectedEditorPresetId: string;
  selectedText: string;
}) {
  const isPolish = action === "polish_selection";
  const canGenerate = isPolish
    ? Boolean(documentPolishPreset && editorPreset && selectedText.trim() && !isGenerating)
    : Boolean(documentGenerationPreset && editorPreset && !isGenerating);

  return (
    <div className="modal-backdrop generation-backdrop" role="presentation">
      <section
        aria-label={documentActionLabels[action]}
        className="settings-dialog generation-dialog document-generation-dialog"
        role="dialog"
      >
        <header className="settings-heading">
          <div>
            <p className="eyebrow">Document Generator</p>
            <h2>{documentActionLabels[action]}</h2>
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

        {isPolish ? (
          <section className="selection-summary" aria-label="当前资料选区">
            <span>当前选区</span>
            <p>{selectedText}</p>
          </section>
        ) : null}

        {isPolish ? (
          <PresetEditor
            kind="document_polish_mode"
            label="资料润色方式"
            onAddPreset={onAddPreset}
            onChangePreset={onChangeDocumentPolishPreset}
            onChangePresetContent={onChangePresetContent}
            onDeletePreset={onDeletePreset}
            onRenamePreset={onRenamePreset}
            placeholder="选择资料润色方式后可直接修改提示词。"
            preset={documentPolishPreset}
            presets={documentPolishPresets}
            selectedPresetId={selectedDocumentPolishPresetId}
          />
        ) : (
          <PresetEditor
            kind="document_generation_mode"
            label="资料生成方式"
            onAddPreset={onAddPreset}
            onChangePreset={onChangeDocumentGenerationPreset}
            onChangePresetContent={onChangePresetContent}
            onDeletePreset={onDeletePreset}
            onRenamePreset={onRenamePreset}
            placeholder="选择资料生成方式后可直接修改提示词。"
            preset={documentGenerationPreset}
            presets={documentGenerationPresets}
            selectedPresetId={selectedDocumentGenerationPresetId}
          />
        )}

        <PresetEditor
          kind="editor_persona"
          label="资料编辑人格"
          onAddPreset={onAddPreset}
          onChangePreset={onChangeEditorPreset}
          onChangePresetContent={onChangePresetContent}
          onDeletePreset={onDeletePreset}
          onRenamePreset={onRenamePreset}
          placeholder="填写资料编辑人格或人格设定 Skill。"
          preset={editorPreset}
          presets={editorPresets}
          selectedPresetId={selectedEditorPresetId}
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
          <section className="generated-draft visible" aria-label="生成结果">
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
              <WandSparkles size={16} />
              {isGenerating ? "生成中" : "生成"}
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
