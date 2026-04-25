import type {
  CSSProperties,
  Dispatch,
  PointerEvent as ReactPointerEvent,
  RefObject,
  SetStateAction,
} from "react";
import type {
  DraftGenerationAction,
  Perspective,
  ProjectSearchResourceType,
  ProjectSearchResult,
  ProjectSearchScope,
  PromptPreviewProfileOverride,
  PromptPreviewResponse,
  PromptProfileVersion,
  PromptProfileVersionDetail,
  PromptRequestType,
  SuggestionRequestTrigger,
} from "@/lib/api/index";
import type {
  ChapterSelection,
  DraftInsertionContext,
  FloatingMenuPosition,
  MarkdownViewMode,
  PerspectiveDraft,
  PresetSaveState,
  PromptProfileDraft,
  WritingCaretPosition,
  WritingEditorHandle,
} from "../types";

export type WorkspaceEditorApi = {
  activeSelection: ChapterSelection | null;
  chapterSelection: ChapterSelection | null;
  documentSelection: ChapterSelection | null;
  draftMenuPosition: FloatingMenuPosition;
  handleChapterContentChange: (nextContent: string) => void;
  handleChapterSelectionChange: () => void;
  handleDocumentContentChange: (nextContent: string) => void;
  handleDocumentSelectionChange: (nextSelection: ChapterSelection | null) => void;
  handlePolishAcceptedSelection: (start: number, end: number) => void;
  handleWritingBlur: () => void;
  handleWritingScroll: () => void;
  markdownViewMode: MarkdownViewMode;
  readChapterSelection: () => ChapterSelection | null;
  readDraftInsertionContext: () => DraftInsertionContext;
  selectionMenuPosition: FloatingMenuPosition;
  setChapterSelection: Dispatch<SetStateAction<ChapterSelection | null>>;
  setDocumentSelection: Dispatch<SetStateAction<ChapterSelection | null>>;
  setMarkdownViewMode: Dispatch<SetStateAction<MarkdownViewMode>>;
  setSelectionMenuPosition: Dispatch<SetStateAction<FloatingMenuPosition>>;
  updateDraftMenuPosition: () => void;
  updateSelectionMenuPosition: (selection?: ChapterSelection | null) => void;
  writingCaretPosition: WritingCaretPosition;
  writingMirrorRef: RefObject<HTMLDivElement | null>;
  writingSurfaceRef: RefObject<WritingEditorHandle | null>;
};

export type WorkspaceLayoutApi = {
  handleInsightResizePointerDown: (event: ReactPointerEvent<HTMLButtonElement>) => void;
  handleRailResizePointerDown: (event: ReactPointerEvent<HTMLButtonElement>) => void;
  isInsightRailVisible: boolean;
  isProjectRailVisible: boolean;
  setIsInsightRailVisible: Dispatch<SetStateAction<boolean>>;
  setIsProjectRailVisible: Dispatch<SetStateAction<boolean>>;
  workspaceClassName: string;
  workspaceStyle: CSSProperties;
};

export type PerspectiveActionsApi = {
  editingPerspectiveId: string | null;
  handleCancelEditPerspective: () => void;
  handleCreatePerspective: () => void;
  handleDeletePerspective: (perspective: Perspective) => Promise<void>;
  handleSavePerspective: () => void;
  handleSelectPerspectiveConfig: (
    perspective: Perspective,
    apiConfigId: string | null,
  ) => void;
  handleStartEditPerspective: (perspective: Perspective) => void;
  handleTogglePerspective: (perspective: Perspective) => void;
  perspectiveEditDraft: PerspectiveDraft;
  perspectiveDraft: PerspectiveDraft;
  setPerspectiveEditDraft: Dispatch<SetStateAction<PerspectiveDraft>>;
  setPerspectiveDraft: Dispatch<SetStateAction<PerspectiveDraft>>;
};

export type ProjectSearchGroup = {
  key: ProjectSearchResourceType;
  label: string;
  results: ProjectSearchResult[];
};

export type ProjectSearchApi = {
  groups: ProjectSearchGroup[];
  isLoading: boolean;
  query: string;
  results: ProjectSearchResult[];
  scope: ProjectSearchScope;
  setQuery: Dispatch<SetStateAction<string>>;
  setScope: Dispatch<SetStateAction<ProjectSearchScope>>;
};

export type SuggestionRequestsApi = {
  isBatchSuggestionPending: boolean;
  isSuggestionAutoEnabled: boolean;
  pendingPerspectiveIds: string[];
  requestEnabledPerspectiveSuggestions: (
    chapterId: string,
    paragraph: string,
    perspectiveIds: string[],
    trigger?: SuggestionRequestTrigger,
  ) => void;
  requestPerspectiveSuggestion: (
    chapterId: string,
    paragraph: string,
    perspectiveId: string,
    trigger?: SuggestionRequestTrigger,
  ) => void;
  setIsSuggestionAutoEnabled: (nextValue: SetStateAction<boolean>) => void;
  suggestionError: string | null;
};

export type ChapterDocxExportDialogState = {
  selectedChapterIds: string[];
  isExporting: boolean;
  error: string | null;
} | null;

export type ChapterDocxExportApi = {
  docxExportDialog: ChapterDocxExportDialogState;
  handleClearDocxExportChapters: () => void;
  handleExportSelectedChaptersDocx: () => Promise<void>;
  handleOpenChapterDocxExportDialog: () => void;
  handleSelectAllDocxExportChapters: () => void;
  handleToggleDocxExportChapter: (chapterId: string) => void;
  setDocxExportDialog: Dispatch<SetStateAction<ChapterDocxExportDialogState>>;
};

export type PromptProfilesApi = {
  activePromptRequestType: PromptRequestType;
  buildPromptProfileOverride: (
    draft: PromptProfileDraft,
  ) => PromptPreviewProfileOverride | null;
  handleOpenPromptVersions: () => void;
  handleRestorePromptProfileVersion: (version: PromptProfileVersionDetail) => Promise<void>;
  handleSavePromptProfile: () => Promise<void>;
  handleSelectPromptRequestType: (requestType: PromptRequestType) => void;
  handleSelectPromptVersion: (version: PromptProfileVersion) => Promise<void>;
  isPromptManagerOpen: boolean;
  isPromptVersionDialogOpen: boolean;
  isPromptVersionLoading: boolean;
  openPromptManager: (requestType?: PromptRequestType) => void;
  openPromptVersions: (requestType: PromptRequestType, selectedVersionId?: string) => void;
  patchPromptDraft: (patch: Partial<PromptProfileDraft>) => void;
  promptDraft: PromptProfileDraft | null;
  promptSaveState: PresetSaveState;
  promptVersions: PromptProfileVersion[];
  quickGenerationProfileSaveState: PresetSaveState;
  saveQuickGenerationProfile: (options: {
    apiConfigId?: string;
    includeChapterSynopsis?: boolean;
    systemTemplate?: string;
    temperature?: string;
    userTemplate?: string;
  }) => Promise<void>;
  selectedPromptVersion: PromptProfileVersionDetail | null;
  setIsPromptManagerOpen: Dispatch<SetStateAction<boolean>>;
  setIsPromptVersionDialogOpen: Dispatch<SetStateAction<boolean>>;
  setPromptSaveState: Dispatch<SetStateAction<PresetSaveState>>;
  togglePromptChapter: (chapterId: string) => void;
  togglePromptDocument: (documentId: string) => void;
};

export type PromptPreviewApi = {
  handlePreviewDraftGeneration: (
    action: DraftGenerationAction,
    draftAnchorOverride?: DraftInsertionContext | null,
  ) => Promise<void>;
  handlePreviewPrompt: (
    requestType: PromptRequestType,
    profileOverride?: PromptPreviewProfileOverride | null,
    draftAnchorOverride?: DraftInsertionContext | null,
  ) => Promise<void>;
  handlePreviewPromptManager: () => void;
  isPromptPreviewLoading: boolean;
  promptPreview: PromptPreviewResponse | null;
  setPromptPreview: Dispatch<SetStateAction<PromptPreviewResponse | null>>;
};
