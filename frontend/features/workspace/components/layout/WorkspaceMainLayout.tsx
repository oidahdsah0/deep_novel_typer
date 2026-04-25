"use client";

import type { ProjectSearchResult, WorkspaceSnapshot } from "@/lib/api/index";
import { InsightRail } from "@/features/workspace/components/perspectives/InsightRail";
import { EmbeddingToolboxDrawer } from "@/features/workspace/components/embeddings/EmbeddingToolboxDrawer";
import { TypewriterLayoutToolbox } from "@/features/workspace/components/typewriter/TypewriterLayoutToolbox";
import type { ChapterTreeActionsApi } from "@/features/workspace/hooks/useChapterTreeActions";
import type { ChapterWritingSynopsisApi } from "@/features/workspace/hooks/useChapterWritingSynopsis";
import type { DocumentGenerationApi } from "@/features/workspace/hooks/useDocumentGeneration";
import type { DocumentTreeActionsApi } from "@/features/workspace/hooks/useDocumentTreeActions";
import type { DraftGenerationApi } from "@/features/workspace/hooks/useDraftGeneration";
import type { EmbeddingToolboxApi } from "@/features/workspace/hooks/useEmbeddingToolbox";
import type { TypewriterLayoutToolboxApi } from "@/features/workspace/hooks/useTypewriterLayoutToolbox";
import type { GenerationPresetsApi } from "@/features/workspace/hooks/useGenerationPresets";
import type { PerspectiveActionsApi } from "@/features/workspace/hooks/usePerspectiveActions";
import type { ProjectSearchApi } from "@/features/workspace/hooks/useProjectSearch";
import type { PromptProfilesApi } from "@/features/workspace/hooks/usePromptProfiles";
import type { SuggestionRequestsApi } from "@/features/workspace/hooks/useSuggestionRequests";
import type { WorkspaceEditorApi } from "@/features/workspace/hooks/useWorkspaceEditorInteractions";
import type { WorkspaceLayoutApi } from "@/features/workspace/hooks/useWorkspaceLayout";
import type {
  ActiveResource,
  PendingDraftGenerationState,
  SaveState,
  WritingEditorKeyEvent,
} from "@/features/workspace/types";
import { scrollTextareaIndexIntoView } from "@/features/workspace/workspaceClientUtils";
import { WorkspaceEditorPane } from "./WorkspaceEditorPane";
import { WorkspaceProjectRail } from "./WorkspaceProjectRail";

type WorkspaceMainLayoutProps = {
  activeWordCountLabel: string;
  chapterTree: ChapterTreeActionsApi;
  chapterWritingSynopsis: ChapterWritingSynopsisApi;
  content: string;
  debugHref: string;
  documentGeneration: DocumentGenerationApi;
  documentTree: DocumentTreeActionsApi;
  draftGeneration: DraftGenerationApi;
  editor: WorkspaceEditorApi;
  embeddingToolbox: EmbeddingToolboxApi;
  generationPresets: GenerationPresetsApi;
  isDraftConfirmationActive: boolean;
  layout: WorkspaceLayoutApi;
  onChapterKeyDown: (event: WritingEditorKeyEvent) => void;
  onOpenProjectSearchResult: (result: ProjectSearchResult) => void;
  onRequestAllEnabledSuggestions: () => void;
  onRequestPerspectiveSuggestion: Parameters<
    typeof InsightRail
  >[0]["onRequestPerspectiveSuggestion"];
  onOpenChat: () => void;
  onOpenDocxExport: () => void;
  onOpenPromptManager: () => void;
  onOpenVersionDialog: () => void;
  onOverwriteConflict: () => void;
  onReloadConflict: () => void;
  pendingDraft: PendingDraftGenerationState | null;
  perspectiveActions: PerspectiveActionsApi;
  projectSearch: ProjectSearchApi;
  promptProfiles: PromptProfilesApi;
  resource: ActiveResource;
  saveState: SaveState;
  statusLabel: string;
  suggestionRequests: SuggestionRequestsApi;
  typewriterLayoutToolbox: TypewriterLayoutToolboxApi;
  workspace: WorkspaceSnapshot;
};

export function WorkspaceMainLayout({
  activeWordCountLabel,
  chapterTree,
  chapterWritingSynopsis,
  content,
  debugHref,
  documentGeneration,
  documentTree,
  draftGeneration,
  editor,
  embeddingToolbox,
  generationPresets,
  isDraftConfirmationActive,
  layout,
  onChapterKeyDown,
  onOpenChat,
  onOpenDocxExport,
  onOpenProjectSearchResult,
  onOpenPromptManager,
  onOpenVersionDialog,
  onOverwriteConflict,
  onReloadConflict,
  onRequestAllEnabledSuggestions,
  onRequestPerspectiveSuggestion,
  pendingDraft,
  perspectiveActions,
  projectSearch,
  promptProfiles,
  resource,
  saveState,
  statusLabel,
  suggestionRequests,
  typewriterLayoutToolbox,
  workspace,
}: WorkspaceMainLayoutProps) {
  function focusEmbeddingTextRange(start: number, end: number) {
    if (resource.type !== "chapter") return;
    const textarea = editor.writingSurfaceRef.current;
    if (!textarea) return;
    const safeStart = Math.max(0, Math.min(textarea.value.length, start));
    const safeEnd = Math.max(safeStart, Math.min(textarea.value.length, end));
    textarea.focus();
    textarea.setSelectionRange(safeStart, safeEnd);
    scrollTextareaIndexIntoView(textarea, safeStart);
  }

  return (
    <>
      {layout.isProjectRailVisible ? (
        <WorkspaceProjectRail
          activeResource={resource}
          chapterDraft={chapterTree.chapterDraft}
          documentDraft={documentTree.documentDraft}
          expandedChapterIds={chapterTree.expandedChapterIds}
          expandedDocumentIds={documentTree.expandedDocumentIds}
          isChapterDraftSaving={chapterTree.isChapterDraftSaving}
          isDocumentDraftSaving={documentTree.isDocumentDraftSaving}
          isProjectSearchLoading={projectSearch.isLoading}
          onDeleteChapterNode={(node) => void chapterTree.handleDeleteChapterNode(node)}
          onDeleteDocumentNode={(node) => void documentTree.handleDeleteDocumentNode(node)}
          onMoveChapterNode={(nodeId, target) => void chapterTree.handleMoveChapterNode(nodeId, target)}
          onMoveDocumentNode={(nodeId, target) => void documentTree.handleMoveDocumentNode(nodeId, target)}
          onOpenChapterNode={(node) => void chapterTree.openChapterNode(node)}
          onOpenDocument={(document) => void documentTree.openDocument(document)}
          onOpenSearchResult={onOpenProjectSearchResult}
          onRenameChapterNode={chapterTree.handleRenameChapterNode}
          onRenameDocumentNode={documentTree.handleRenameDocumentNode}
          onResizeStart={layout.handleRailResizePointerDown}
          onStartCreateChapterNode={chapterTree.handleStartCreateChapterNode}
          onStartCreateDocumentNode={documentTree.handleStartCreateDocumentNode}
          onSubmitChapterDraft={() => void chapterTree.handleSubmitChapterDraft()}
          onSubmitDocumentDraft={() => void documentTree.handleSubmitDocumentDraft()}
          projectSearchGroups={projectSearch.groups}
          projectSearchQuery={projectSearch.query}
          projectSearchScope={projectSearch.scope}
          setChapterDraft={chapterTree.setChapterDraft}
          setDocumentDraft={documentTree.setDocumentDraft}
          setProjectSearchQuery={projectSearch.setQuery}
          setProjectSearchScope={projectSearch.setScope}
          workspace={workspace}
        />
      ) : null}
      <WorkspaceEditorPane
        activeWordCountLabel={activeWordCountLabel}
        chapterSelection={editor.chapterSelection}
        content={content}
        debugHref={debugHref}
        documentSelection={editor.documentSelection}
        draftMenuPosition={editor.draftMenuPosition}
        embeddingToolbox={embeddingToolbox}
        isDraftConfirmationActive={isDraftConfirmationActive}
        isInsightRailVisible={layout.isInsightRailVisible}
        isProjectRailVisible={layout.isProjectRailVisible}
        markdownViewMode={editor.markdownViewMode}
        onAcceptDraft={draftGeneration.handleAcceptDraft}
        onBlueprint={draftGeneration.handleOpenChapterBlueprintDialog}
        onChangeChapterContent={editor.handleChapterContentChange}
        onChangeDocumentContent={editor.handleDocumentContentChange}
        onChangeMarkdownViewMode={editor.setMarkdownViewMode}
        onChat={onOpenChat}
        onContinueDocument={documentGeneration.handleOpenDocumentContinuationDialog}
        onDocumentSelectionChange={editor.handleDocumentSelectionChange}
        onOpenDocxExport={onOpenDocxExport}
        onOpenGenerationDialog={draftGeneration.handleOpenGenerationDialog}
        onOpenPolish={draftGeneration.handleOpenPolishDialog}
        onOpenPromptManager={onOpenPromptManager}
        onOpenVersionDialog={onOpenVersionDialog}
        onOverwriteConflict={onOverwriteConflict}
        onPolishDocumentSelection={documentGeneration.handleOpenDocumentPolishDialog}
        onReloadConflict={onReloadConflict}
        onRejectDraft={draftGeneration.handleDiscardDraft}
        onSelectionChange={editor.handleChapterSelectionChange}
        onSetInsightRailVisible={layout.setIsInsightRailVisible}
        onSetProjectRailVisible={layout.setIsProjectRailVisible}
        onWritingBlur={editor.handleWritingBlur}
        onWritingKeyDown={onChapterKeyDown}
        onWritingScroll={editor.handleWritingScroll}
        pendingDraft={pendingDraft}
        projectSubtitle={workspace.project.subtitle}
        projectUpdatedAt={workspace.project.updated_at}
        resource={resource}
        saveState={saveState}
        statusLabel={statusLabel}
        typewriterLayoutToolbox={typewriterLayoutToolbox}
        writingMirrorRef={editor.writingMirrorRef}
        writingSurfaceRef={editor.writingSurfaceRef}
      />
      {layout.isInsightRailVisible ? (
        <InsightRail
          apiConfigs={workspace.api_configs}
          authorPreset={generationPresets.selectedAuthorPreset}
          authorPresets={generationPresets.authorPresets}
          canRequestSuggestions={resource.type === "chapter"}
          chapterWritingSynopsis={chapterWritingSynopsis}
          editingPerspectiveId={perspectiveActions.editingPerspectiveId}
          isChapterResourceActive={resource.type === "chapter"}
          isBatchSuggestionPending={suggestionRequests.isBatchSuggestionPending}
          isSuggestionAutoEnabled={suggestionRequests.isSuggestionAutoEnabled}
          onAddGenerationPreset={generationPresets.handleCreateGenerationPreset}
          onCancelEditPerspective={perspectiveActions.handleCancelEditPerspective}
          onChangeAuthorPreset={generationPresets.setSelectedAuthorPresetId}
          onChangePresetContent={generationPresets.handlePresetContentChange}
          onCreatePerspective={perspectiveActions.handleCreatePerspective}
          onDeleteGenerationPreset={generationPresets.handleDeleteGenerationPreset}
          onDeletePerspective={perspectiveActions.handleDeletePerspective}
          onDraftChange={perspectiveActions.setPerspectiveDraft}
          onEditDraftChange={perspectiveActions.setPerspectiveEditDraft}
          onRenameGenerationPreset={generationPresets.handleRenameGenerationPreset}
          onRequestAllEnabledSuggestions={onRequestAllEnabledSuggestions}
          onRequestPerspectiveSuggestion={onRequestPerspectiveSuggestion}
          onResizeStart={layout.handleInsightResizePointerDown}
          onSavePerspective={perspectiveActions.handleSavePerspective}
          onSelectPerspectiveConfig={perspectiveActions.handleSelectPerspectiveConfig}
          onStartEditPerspective={perspectiveActions.handleStartEditPerspective}
          onTogglePerspective={perspectiveActions.handleTogglePerspective}
          onToggleSuggestionAuto={() =>
            suggestionRequests.setIsSuggestionAutoEnabled((current) => !current)
          }
          pendingPerspectiveIds={suggestionRequests.pendingPerspectiveIds}
          perspectiveDraft={perspectiveActions.perspectiveDraft}
          perspectiveEditDraft={perspectiveActions.perspectiveEditDraft}
          perspectives={workspace.perspectives}
          presetSaveState={generationPresets.presetSaveState}
          promptProfiles={workspace.prompt_profiles.profiles}
          quickGenerationProfileSaveState={promptProfiles.quickGenerationProfileSaveState}
          onSaveQuickGenerationProfile={promptProfiles.saveQuickGenerationProfile}
          selectedAuthorPresetId={generationPresets.selectedAuthorPresetId}
          suggestionError={suggestionRequests.suggestionError}
          suggestions={workspace.suggestions}
        />
      ) : null}
      <EmbeddingToolboxDrawer
        activeSelection={editor.activeSelection}
        onFocusTextRange={focusEmbeddingTextRange}
        resource={resource}
        toolbox={embeddingToolbox}
      />
      <TypewriterLayoutToolbox toolbox={typewriterLayoutToolbox} />
    </>
  );
}
