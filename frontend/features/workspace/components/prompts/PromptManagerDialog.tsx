"use client";

import { X } from "lucide-react";
import type { ApiConfig, PromptRequestType } from "@/lib/api/index";
import { usePromptDialogResize } from "@/features/workspace/hooks/prompts/usePromptDialogResize";
import { promptPlaceholderOptions } from "../../constants";
import type { PresetSaveState, PromptMaterialOption, PromptProfileDraft } from "../../types";
import { PromptAdvancedConfigField } from "./PromptAdvancedConfigField";
import { PromptConfigToolbar } from "./PromptConfigToolbar";
import { PromptManagerActions } from "./PromptManagerActions";
import { ChapterPromptMaterialPanel, DocumentPromptMaterialPanel } from "./PromptMaterialPanel";
import { PromptOutputContractPanel } from "./PromptOutputContractPanel";
import { PromptProfileTabs } from "./PromptProfileTabs";
import { PromptTemplateEditor } from "./PromptTemplateEditor";

export function PromptManagerDialog({
  activeRequestType,
  apiConfigs,
  chapterOptions,
  documentOptions,
  draft,
  isPreviewing,
  onChangeDraft,
  onClose,
  onOpenHistory,
  onPreview,
  onSave,
  onSelectRequestType,
  onToggleChapter,
  onToggleDocument,
  saveState,
}: {
  activeRequestType: PromptRequestType;
  apiConfigs: ApiConfig[];
  chapterOptions: PromptMaterialOption[];
  documentOptions: PromptMaterialOption[];
  draft: PromptProfileDraft;
  isPreviewing: boolean;
  onChangeDraft: (patch: Partial<PromptProfileDraft>) => void;
  onClose: () => void;
  onOpenHistory: () => void;
  onPreview: () => void;
  onSave: () => void;
  onSelectRequestType: (requestType: PromptRequestType) => void;
  onToggleChapter: (chapterId: string) => void;
  onToggleDocument: (documentId: string) => void;
  saveState: PresetSaveState;
}) {
  const { dialogStyle, handleResizeStart } = usePromptDialogResize();

  return (
    <div className="modal-backdrop generation-backdrop" role="presentation">
      <section
        aria-label="请求管理"
        className="settings-dialog prompt-manager-dialog"
        role="dialog"
        style={dialogStyle}
      >
        <header className="settings-heading">
          <div>
            <p className="eyebrow">Request Profiles</p>
            <h2>请求管理</h2>
          </div>
          <button className="icon-button" onClick={onClose} type="button" aria-label="关闭">
            <X size={18} />
          </button>
        </header>

        <PromptProfileTabs
          activeRequestType={activeRequestType}
          onSelectRequestType={onSelectRequestType}
        />

        <div className="prompt-manager-grid">
          <ChapterPromptMaterialPanel
            draft={draft}
            onChangeDraft={onChangeDraft}
            onToggleChapter={onToggleChapter}
            options={chapterOptions}
          />
          <DocumentPromptMaterialPanel
            draft={draft}
            onToggleDocument={onToggleDocument}
            options={documentOptions}
          />
          <section className="prompt-template-panel" aria-label="提示词模板">
            <PromptConfigToolbar
              apiConfigs={apiConfigs}
              draft={draft}
              onChangeDraft={onChangeDraft}
            />
            <PromptOutputContractPanel draft={draft} onChangeDraft={onChangeDraft} />
            <PromptTemplateEditor
              activeTags={promptPlaceholderOptions[activeRequestType]}
              draft={draft}
              onChangeDraft={onChangeDraft}
            />
            <PromptAdvancedConfigField draft={draft} onChangeDraft={onChangeDraft} />
          </section>
        </div>

        <PromptManagerActions
          isPreviewing={isPreviewing}
          onClose={onClose}
          onOpenHistory={onOpenHistory}
          onPreview={onPreview}
          onSave={onSave}
          saveState={saveState}
        />
        <button
          aria-label="拖拽调整请求管理弹窗大小"
          className="prompt-dialog-resize-handle"
          onPointerDown={handleResizeStart}
          type="button"
        />
      </section>
    </div>
  );
}
