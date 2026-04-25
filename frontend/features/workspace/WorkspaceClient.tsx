"use client";

import type { Perspective, ProjectSearchResult, WorkspaceSnapshot } from "@/lib/api/index";
import { WorkspaceGenerationDialogs } from "@/features/workspace/components/layout/WorkspaceGenerationDialogs";
import { WorkspaceMainLayout } from "@/features/workspace/components/layout/WorkspaceMainLayout";
import { WorkspacePromptDialogs } from "@/features/workspace/components/layout/WorkspacePromptDialogs";
import { WorkspaceUtilityDialogs } from "@/features/workspace/components/layout/WorkspaceUtilityDialogs";
import { useActiveResourceSave } from "@/features/workspace/hooks/useActiveResourceSave";
import { useAutosave } from "@/features/workspace/hooks/useAutosave";
import { useChapterDocxExport } from "@/features/workspace/hooks/useChapterDocxExport";
import { useChapterWritingSynopsis } from "@/features/workspace/hooks/useChapterWritingSynopsis";
import { useChapterTreeActions } from "@/features/workspace/hooks/useChapterTreeActions";
import { useChatSessions } from "@/features/workspace/hooks/useChatSessions";
import { useDocumentTreeActions } from "@/features/workspace/hooks/useDocumentTreeActions";
import { useEmbeddingToolbox } from "@/features/workspace/hooks/useEmbeddingToolbox";
import { usePendingDraftFocus } from "@/features/workspace/hooks/usePendingDraftFocus";
import { usePerspectiveActions } from "@/features/workspace/hooks/usePerspectiveActions";
import { useProjectSearch } from "@/features/workspace/hooks/useProjectSearch";
import { usePromptProfiles } from "@/features/workspace/hooks/usePromptProfiles";
import { useSaveConflictActions } from "@/features/workspace/hooks/useSaveConflictActions";
import { useSuggestionRequests } from "@/features/workspace/hooks/useSuggestionRequests";
import { useTypewriterLayoutToolbox } from "@/features/workspace/hooks/useTypewriterLayoutToolbox";
import { useVersionHistory } from "@/features/workspace/hooks/useVersionHistory";
import { useWorkspaceEditorInteractions } from "@/features/workspace/hooks/useWorkspaceEditorInteractions";
import { useWorkspaceGenerationController } from "@/features/workspace/hooks/useWorkspaceGenerationController";
import { useWorkspaceLayout } from "@/features/workspace/hooks/useWorkspaceLayout";
import {
  useWorkspaceResourceController,
  type WorkspaceResourceControllerApi,
} from "@/features/workspace/hooks/useWorkspaceResourceController";
import { flattenDocumentOptions } from "@/features/workspace/utils";
import {
  buildProjectDebugHref,
  countDraftWords,
  findDocumentNode,
  formatCount,
  isPromptRequestType,
  saveStatusLabel,
  stringMetadata,
  suggestionParagraphFromContent,
} from "@/features/workspace/workspaceClientUtils";

export function WorkspaceClient({ initialWorkspace }: { initialWorkspace: WorkspaceSnapshot }) {
  const resourceCore = useWorkspaceResourceController({ initialWorkspace });
  const { content, resource, savedContent, saveState, workspace } = resourceCore;
  const setContent = resourceCore.setContent;
  const setSaveState = resourceCore.setSaveState;
  const setWorkspace = resourceCore.setWorkspace;

  const projectId = workspace.project.id;
  const layout = useWorkspaceLayout();
  const typewriterLayoutToolbox = useTypewriterLayoutToolbox(
    workspace.typewriter_layout_settings,
  );
  const chapterWritingSynopsis = useChapterWritingSynopsis({
    projectId,
    setWorkspace,
    workspace,
  });
  const projectSearch = useProjectSearch(projectId);
  const suggestionRequests = useSuggestionRequests({
    activeChapterId: resource.type === "chapter" ? resource.id : workspace.active_chapter.id,
    activeParagraph: suggestionParagraphFromContent(
      resource.type === "chapter" ? content : workspace.active_chapter.content,
    ),
    projectId,
    setWorkspace,
  });
  const saveActive = useActiveResourceSave({
    content,
    isSuggestionAutoEnabled: suggestionRequests.isSuggestionAutoEnabled,
    projectId,
    requestEnabledPerspectiveSuggestions: suggestionRequests.requestEnabledPerspectiveSuggestions,
    resource,
    savedContent,
    setSavedContent: resourceCore.commitSaveSuccess,
    setSaveState,
    setWorkspace,
    workspace,
  });
  const resourceController: WorkspaceResourceControllerApi = {
    ...resourceCore,
    commitGeneratedContent: (nextContent) =>
      resourceCore.commitGeneratedContent(nextContent, saveActive),
    requestSave: saveActive,
  };
  const saveConflictActions = useSaveConflictActions({ content, projectId, resourceController });
  const chapterTree = useChapterTreeActions({
    flushChapterWritingSynopsis: chapterWritingSynopsis.flush,
    projectId,
    resourceController,
  });
  const documentTree = useDocumentTreeActions({
    flushChapterWritingSynopsis: chapterWritingSynopsis.flush,
    projectId,
    resourceController,
  });
  const docxExport = useChapterDocxExport({ content, projectId, saveActive, workspace });
  const editor = useWorkspaceEditorInteractions({ content, resource, setContent });
  const embeddingToolbox = useEmbeddingToolbox({
    activeSelection: editor.activeSelection,
    apiConfigs: workspace.api_configs,
    content,
    projectId,
    resource,
  });
  const chat = useChatSessions(projectId);
  const perspectiveActions = usePerspectiveActions({ projectId, setWorkspace });
  const promptProfiles = usePromptProfiles({
    projectId,
    promptProfiles: workspace.prompt_profiles.profiles,
    setWorkspace,
  });
  const generation = useWorkspaceGenerationController({
    content,
    editor,
    flushChapterWritingSynopsis: chapterWritingSynopsis.flush,
    projectId,
    promptProfiles,
    resource,
    resourceController,
    saveActive,
    setContent,
    setWorkspace,
    workspace,
  });
  const versionHistory = useVersionHistory({
    projectId,
    resourceController,
    workspace,
  });

  useAutosave({
    content,
    disabled: generation.isDraftConfirmationActive,
    saveActive,
    savedContent,
    setSaveState,
  });
  usePendingDraftFocus(editor.writingSurfaceRef, generation.pendingDraft);

  const isActiveChapterWithBackendCount =
    resource.type === "chapter" && resource.id === workspace.active_chapter.id;
  const hasUnsavedDraft = content !== savedContent;
  const contentDraftWordCount = countDraftWords(content);
  const activeWordCount = isActiveChapterWithBackendCount && !hasUnsavedDraft
    ? workspace.active_chapter.word_count
    : contentDraftWordCount;
  const draftWordCountSuffix = hasUnsavedDraft ? "（草稿）" : "";
  const activeWordCountLabel = editor.activeSelection
    ? `${formatCount(countDraftWords(editor.activeSelection.text))} / ${formatCount(contentDraftWordCount)} 字${draftWordCountSuffix}`
    : `${formatCount(activeWordCount)} 字${draftWordCountSuffix}`;
  const statusLabel = saveStatusLabel(saveState);

  function handleRequestAllEnabledSuggestions() {
    if (resource.type !== "chapter") return;
    suggestionRequests.requestEnabledPerspectiveSuggestions(
      resource.id,
      suggestionParagraphFromContent(content),
      enabledPerspectiveIds(),
    );
  }

  function handleRequestPerspectiveSuggestion(perspective: Perspective) {
    if (resource.type === "chapter") {
      suggestionRequests.requestPerspectiveSuggestion(
        resource.id,
        suggestionParagraphFromContent(content),
        perspective.id,
      );
    }
  }

  async function handleOpenProjectSearchResult(result: ProjectSearchResult) {
    if (result.resource_type === "chapter") {
      await chapterTree.openChapter(stringMetadata(result, "chapter_id") || result.resource_id);
      focusChapterMatch(projectSearch.query);
    } else if (result.resource_type === "document") {
      await openDocumentById(stringMetadata(result, "document_id") || result.resource_id);
    } else if (result.resource_type === "prompt_profile") {
      const requestType = stringMetadata(result, "request_type");
      if (isPromptRequestType(requestType)) promptProfiles.openPromptManager(requestType);
    } else if (result.resource_type === "prompt_profile_version") {
      const requestType = stringMetadata(result, "request_type");
      if (isPromptRequestType(requestType)) {
        promptProfiles.openPromptVersions(requestType, stringMetadata(result, "version_id") || undefined);
      }
    } else if (result.resource_type === "resource_version") {
      const resourceType = stringMetadata(result, "resource_type");
      const resourceId = stringMetadata(result, "resource_id");
      if (resourceType === "chapter" && resourceId) {
        await chapterTree.openChapter(resourceId);
      } else if (resourceType === "document" && resourceId) {
        await openDocumentById(resourceId);
      }
    }
  }

  async function openDocumentById(documentId: string) {
    const document = findDocumentNode(workspace.document_tree, documentId);
    if (document) await documentTree.openDocument(document);
  }

  function focusChapterMatch(query: string) {
    const normalized = query.trim();
    if (!normalized) return;
    window.setTimeout(() => {
      const textarea = editor.writingSurfaceRef.current;
      if (!textarea) return;
      const index = textarea.value.toLocaleLowerCase().indexOf(normalized.toLocaleLowerCase());
      if (index < 0) return;
      textarea.focus();
      textarea.setSelectionRange(index, index + normalized.length);
    }, 40);
  }

  function enabledPerspectiveIds() {
    return workspace.perspectives
      .filter((perspective) => perspective.is_enabled)
      .map((perspective) => perspective.id);
  }

  return (
    <main className={layout.workspaceClassName} style={layout.workspaceStyle}>
      <WorkspaceMainLayout
        activeWordCountLabel={activeWordCountLabel}
        chapterTree={chapterTree}
        chapterWritingSynopsis={chapterWritingSynopsis}
        content={content}
        debugHref={buildProjectDebugHref(projectId)}
        documentGeneration={generation.documentGeneration}
        documentTree={documentTree}
        draftGeneration={generation.draftGeneration}
        editor={editor}
        embeddingToolbox={embeddingToolbox}
        generationPresets={generation.generationPresets}
        isDraftConfirmationActive={generation.isDraftConfirmationActive}
        layout={layout}
        onChapterKeyDown={generation.handleChapterKeyDown}
        onOpenChat={chat.openChat}
        onOpenDocxExport={docxExport.handleOpenChapterDocxExportDialog}
        onOpenProjectSearchResult={(result) => void handleOpenProjectSearchResult(result)}
        onOpenPromptManager={() => promptProfiles.openPromptManager()}
        onOpenVersionDialog={() => void versionHistory.handleOpenVersionDialog()}
        onOverwriteConflict={() => void saveConflictActions.overwriteConflictResource()}
        onReloadConflict={() => void saveConflictActions.reloadConflictResource()}
        onRequestAllEnabledSuggestions={handleRequestAllEnabledSuggestions}
        onRequestPerspectiveSuggestion={handleRequestPerspectiveSuggestion}
        pendingDraft={generation.pendingDraft}
        perspectiveActions={perspectiveActions}
        projectSearch={projectSearch}
        promptProfiles={promptProfiles}
        resource={resource}
        saveState={saveState}
        statusLabel={statusLabel}
        suggestionRequests={suggestionRequests}
        typewriterLayoutToolbox={typewriterLayoutToolbox}
        workspace={workspace}
      />
      <WorkspacePromptDialogs
        apiConfigs={workspace.api_configs}
        chapters={workspace.chapters}
        docxExport={docxExport}
        promptChapterOptions={workspace.chapters.map((chapter) => ({
          id: chapter.id,
          title: chapter.title,
          meta: `${chapter.word_count} 字`,
        }))}
        promptDocumentOptions={flattenDocumentOptions(workspace.document_tree)}
        promptPreview={generation.promptPreview}
        promptProfiles={promptProfiles}
      />
      <WorkspaceGenerationDialogs
        chapterSelection={editor.chapterSelection}
        documentGeneration={generation.documentGeneration}
        documentSelection={editor.documentSelection}
        draftGeneration={generation.draftGeneration}
        generationPresets={generation.generationPresets}
        promptPreview={generation.promptPreview}
      />
      <WorkspaceUtilityDialogs
        chat={chat}
        resource={resource}
        versionHistory={versionHistory}
      />
    </main>
  );
}
