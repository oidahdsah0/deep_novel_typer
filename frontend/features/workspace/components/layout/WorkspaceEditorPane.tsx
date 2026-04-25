"use client";

import type { RefObject } from "react";
import { MarkdownDocumentPane } from "@/features/workspace/components/documents/MarkdownDocumentPane";
import { DraftQuickMenu } from "@/features/workspace/components/editor/DraftQuickMenu";
import { EmbeddingHeatmapOverlay } from "@/features/workspace/components/embeddings/EmbeddingHeatmapOverlay";
import { useEditorHeatmap } from "@/features/workspace/components/embeddings/useEditorHeatmap";
import { PendingDraftConfirmation } from "@/features/workspace/components/editor/PendingDraftConfirmation";
import { TypewriterTextEditor } from "@/features/workspace/components/editor/TypewriterTextEditor";
import type { EmbeddingToolboxApi } from "@/features/workspace/hooks/useEmbeddingToolbox";
import type { TypewriterLayoutToolboxApi } from "@/features/workspace/hooks/useTypewriterLayoutToolbox";
import type {
  ActiveResource,
  ChapterSelection,
  FloatingMenuPosition,
  MarkdownViewMode,
  PendingDraftGenerationState,
  SaveState,
  WritingEditorHandle,
  WritingEditorKeyEvent,
} from "@/features/workspace/types";
import { WorkspaceEditorTopbar } from "./WorkspaceEditorTopbar";

type WorkspaceEditorPaneProps = {
  activeWordCountLabel: string;
  chapterSelection: ChapterSelection | null;
  content: string;
  debugHref: string;
  documentSelection: ChapterSelection | null;
  draftMenuPosition: FloatingMenuPosition;
  embeddingToolbox: EmbeddingToolboxApi;
  isDraftConfirmationActive: boolean;
  isInsightRailVisible: boolean;
  isProjectRailVisible: boolean;
  markdownViewMode: MarkdownViewMode;
  onAcceptDraft: () => void;
  onBlueprint: () => void;
  onChangeChapterContent: (content: string) => void;
  onChangeDocumentContent: (content: string) => void;
  onChangeMarkdownViewMode: (mode: MarkdownViewMode) => void;
  onChat: () => void;
  onContinueDocument: () => void;
  onOpenDocxExport: () => void;
  onOpenGenerationDialog: (action: "next_paragraph" | "next_section") => void;
  onOpenPolish: () => void;
  onOpenPromptManager: () => void;
  onOpenVersionDialog: () => void;
  onOverwriteConflict: () => void;
  onPolishDocumentSelection: () => void;
  onReloadConflict: () => void;
  onRejectDraft: () => void;
  onSelectionChange: () => void;
  onDocumentSelectionChange: (selection: ChapterSelection | null) => void;
  onSetInsightRailVisible: (next: (current: boolean) => boolean) => void;
  onSetProjectRailVisible: (next: (current: boolean) => boolean) => void;
  onWritingBlur: () => void;
  onWritingKeyDown: (event: WritingEditorKeyEvent) => void;
  onWritingScroll: () => void;
  pendingDraft: PendingDraftGenerationState | null;
  projectSubtitle: string;
  projectUpdatedAt: string;
  resource: ActiveResource;
  saveState: SaveState;
  statusLabel: string;
  typewriterLayoutToolbox: TypewriterLayoutToolboxApi;
  writingMirrorRef: RefObject<HTMLDivElement | null>;
  writingSurfaceRef: RefObject<WritingEditorHandle | null>;
};

export function WorkspaceEditorPane({
  activeWordCountLabel,
  chapterSelection,
  content,
  debugHref,
  documentSelection,
  draftMenuPosition,
  embeddingToolbox,
  isDraftConfirmationActive,
  isInsightRailVisible,
  isProjectRailVisible,
  markdownViewMode,
  onAcceptDraft,
  onBlueprint,
  onChangeChapterContent,
  onChangeDocumentContent,
  onChangeMarkdownViewMode,
  onChat,
  onContinueDocument,
  onOpenDocxExport,
  onOpenGenerationDialog,
  onOpenPolish,
  onOpenPromptManager,
  onOpenVersionDialog,
  onOverwriteConflict,
  onPolishDocumentSelection,
  onReloadConflict,
  onRejectDraft,
  onSelectionChange,
  onDocumentSelectionChange,
  onSetInsightRailVisible,
  onSetProjectRailVisible,
  onWritingBlur,
  onWritingKeyDown,
  onWritingScroll,
  pendingDraft,
  projectSubtitle,
  projectUpdatedAt,
  resource,
  saveState,
  statusLabel,
  typewriterLayoutToolbox,
  writingMirrorRef,
  writingSurfaceRef,
}: WorkspaceEditorPaneProps) {
  const activeHeatmap = embeddingToolbox.isHeatmapVisible ? embeddingToolbox.heatmap : null;
  const editorHeatmap = useEditorHeatmap({
    activeTagId: embeddingToolbox.activeHeatmapTagId,
    content,
    heatmap: activeHeatmap,
    tags: embeddingToolbox.tags,
  });

  return (
    <section className="editor-pane" aria-label="正文编辑区">
      <WorkspaceEditorTopbar
        activeWordCountLabel={activeWordCountLabel}
        debugHref={debugHref}
        isInsightRailVisible={isInsightRailVisible}
        isEmbeddingToolboxOpen={embeddingToolbox.isOpen}
        isProjectRailVisible={isProjectRailVisible}
        isTypewriterToolboxOpen={typewriterLayoutToolbox.isOpen}
        onOpenDocxExport={onOpenDocxExport}
        onOpenPromptManager={onOpenPromptManager}
        onOpenVersionDialog={onOpenVersionDialog}
        onOverwriteConflict={onOverwriteConflict}
        onToggleEmbeddingToolbox={() => embeddingToolbox.setIsOpen((current) => !current)}
        onToggleTypewriterToolbox={() => typewriterLayoutToolbox.setIsOpen((current) => !current)}
        onReloadConflict={onReloadConflict}
        onSetInsightRailVisible={onSetInsightRailVisible}
        onSetProjectRailVisible={onSetProjectRailVisible}
        projectSubtitle={projectSubtitle}
        projectUpdatedAt={projectUpdatedAt}
        resource={resource}
        saveState={saveState}
        statusLabel={statusLabel}
      />

      {resource.type === "chapter" ? (
        <div className="writing-stage">
          <TypewriterTextEditor
            firstLineIndentChars={typewriterLayoutToolbox.savedSettings.first_line_indent_chars}
            fontSizePx={typewriterLayoutToolbox.savedSettings.font_size_px}
            highlights={editorHeatmap.highlights}
            isReadOnly={isDraftConfirmationActive}
            lineHeightMultiplier={typewriterLayoutToolbox.savedSettings.line_height_multiplier}
            onBlur={onWritingBlur}
            onChange={onChangeChapterContent}
            onFocus={onSelectionChange}
            onHighlightPointerEnter={editorHeatmap.handleHighlightEnter}
            onHighlightPointerLeave={editorHeatmap.clearHover}
            onKeyDown={(event) => {
              onWritingKeyDown(event);
              window.requestAnimationFrame(onSelectionChange);
            }}
            onScroll={onWritingScroll}
            onSelectionChange={onSelectionChange}
            paragraphGapLines={typewriterLayoutToolbox.savedSettings.paragraph_gap_lines}
            ref={writingSurfaceRef}
            value={content}
          />
          <div aria-hidden className="writing-mirror" ref={writingMirrorRef}>
            {content || " "}
          </div>
          <EmbeddingHeatmapOverlay
            heatmap={activeHeatmap}
            hover={editorHeatmap.hover}
          />
          <DraftQuickMenu
            hasSelection={Boolean(chapterSelection)}
            left={draftMenuPosition.left}
            onBlueprint={onBlueprint}
            onChat={onChat}
            onNextParagraph={() => onOpenGenerationDialog("next_paragraph")}
            onNextSection={() => onOpenGenerationDialog("next_section")}
            onPolish={onOpenPolish}
            top={draftMenuPosition.top}
            visible={draftMenuPosition.visible && !isDraftConfirmationActive}
          />
          {pendingDraft ? (
            <PendingDraftConfirmation
              onAccept={onAcceptDraft}
              onReject={onRejectDraft}
              pending={pendingDraft}
            />
          ) : null}
        </div>
      ) : (
        <MarkdownDocumentPane
          content={content}
          hasSelection={Boolean(documentSelection)}
          mode={markdownViewMode}
          onChange={onChangeDocumentContent}
          onContinue={onContinueDocument}
          onModeChange={onChangeMarkdownViewMode}
          onPolishSelection={onPolishDocumentSelection}
          onSelectionChange={onDocumentSelectionChange}
        />
      )}
    </section>
  );
}
