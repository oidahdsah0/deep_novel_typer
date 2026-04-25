"use client";

import { AlertCircle, Check, Eye, ListChecks, Sparkles, X } from "lucide-react";
import type {
  GeneratedChapterBlueprint,
  GenerationPreset,
  GenerationPresetKind,
} from "@/lib/api/index";
import { presetSaveLabels, sourceLabels } from "../../constants";
import type { PresetSaveState } from "../../types";
import { renderChapterBlueprintPoints } from "../../utils";
import { PresetEditor } from "./PresetEditor";

export function ChapterBlueprintDialog({
  authorPreset,
  authorPresets,
  blueprintPreset,
  blueprintPresets,
  error,
  isGenerating,
  isPreviewing,
  onAccept,
  onAddPreset,
  onChangeAuthorPreset,
  onChangeBlueprintPreset,
  onChangePresetContent,
  onClose,
  onDeletePreset,
  onDiscard,
  onGenerate,
  onPreview,
  onRenamePreset,
  presetSaveState,
  result,
  selectedAuthorPresetId,
  selectedBlueprintPresetId,
}: {
  authorPreset: GenerationPreset | undefined;
  authorPresets: GenerationPreset[];
  blueprintPreset: GenerationPreset | undefined;
  blueprintPresets: GenerationPreset[];
  error: string | null;
  isGenerating: boolean;
  isPreviewing: boolean;
  onAccept: () => void;
  onAddPreset: (kind: GenerationPresetKind) => void;
  onChangeAuthorPreset: (presetId: string) => void;
  onChangeBlueprintPreset: (presetId: string) => void;
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
  result: GeneratedChapterBlueprint | null;
  selectedAuthorPresetId: string;
  selectedBlueprintPresetId: string;
}) {
  const canGenerate = Boolean(blueprintPreset && authorPreset && !isGenerating);

  return (
    <div className="modal-backdrop generation-backdrop" role="presentation">
      <section
        aria-label="章节基础铺设"
        className="settings-dialog generation-dialog chapter-blueprint-dialog"
        role="dialog"
      >
        <header className="settings-heading">
          <div>
            <p className="eyebrow">Chapter Blueprint</p>
            <h2>章节基础铺设</h2>
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

        <PresetEditor
          kind="chapter_blueprint_mode"
          label="铺设方式"
          onAddPreset={onAddPreset}
          onChangePreset={onChangeBlueprintPreset}
          onChangePresetContent={onChangePresetContent}
          onDeletePreset={onDeletePreset}
          onRenamePreset={onRenamePreset}
          placeholder="选择铺设方式后可直接修改提示词。"
          preset={blueprintPreset}
          presets={blueprintPresets}
          selectedPresetId={selectedBlueprintPresetId}
        />

        <PresetEditor
          kind="author_persona"
          label="执笔作者人格"
          onAddPreset={onAddPreset}
          onChangePreset={onChangeAuthorPreset}
          onChangePresetContent={onChangePresetContent}
          onDeletePreset={onDeletePreset}
          onRenamePreset={onRenamePreset}
          placeholder="填写作者人格或人格设定 Skill。"
          preset={authorPreset}
          presets={authorPresets}
          selectedPresetId={selectedAuthorPresetId}
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
          <section className="generated-draft visible" aria-label="铺设要点">
            <div className="generated-draft-meta">
              <ListChecks size={14} />
              <span>
                {sourceLabels[result.source]} · {result.model ?? "本地兜底"}
              </span>
            </div>
            <div className="generated-draft-text blueprint-points">
              {renderChapterBlueprintPoints(result.points)}
            </div>
          </section>
        ) : null}

        {result ? (
          <div className="dialog-actions">
            <button className="secondary-button" onClick={onDiscard} type="button">
              废弃
            </button>
            <button className="primary-button" onClick={onAccept} type="button">
              <Check size={16} />
              采纳并插入光标处
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
              {isGenerating ? "生成中" : "生成铺设"}
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
