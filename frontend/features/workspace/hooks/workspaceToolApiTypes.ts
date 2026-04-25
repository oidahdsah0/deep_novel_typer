import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import type {
  ApiConfig,
  ChatMessage,
  ChatSessionSummary,
  ClusterResponse,
  EmbeddingTag,
  EmbeddingTagInput,
  EmbeddingTagUpdate,
  GenerationPreset,
  GenerationPresetKind,
  GenerationPresetUpdate,
  HeatmapResponse,
  TypewriterLayoutSettings,
  TypewriterLayoutSettingsInput,
} from "@/lib/api/index";
import type { PresetSaveState } from "../types";
import type {
  EmbeddingRangeMode,
  EmbeddingToolboxTab,
} from "./embeddingToolboxTypes";
import type { EmbeddingAppliedSettings } from "./useEmbeddingSettings";

export type GenerationPresetsApi = {
  authorPresets: GenerationPreset[];
  chapterBlueprintPresets: GenerationPreset[];
  documentGenerationPresets: GenerationPreset[];
  documentPolishPresets: GenerationPreset[];
  editorPresets: GenerationPreset[];
  flushPresetSave: (
    kind: GenerationPresetKind,
    presetId: string,
    expectedVersion?: number,
  ) => Promise<void>;
  handleCreateGenerationPreset: (kind: GenerationPresetKind) => Promise<void>;
  handleDeleteGenerationPreset: (preset: GenerationPreset) => Promise<void>;
  handlePresetContentChange: (
    kind: GenerationPresetKind,
    preset: GenerationPreset,
    contentValue: string,
  ) => void;
  handleRenameGenerationPreset: (preset: GenerationPreset) => Promise<void>;
  pendingPresetPatches: MutableRefObject<Record<string, GenerationPresetUpdate>>;
  polishPresets: GenerationPreset[];
  presetSaveKey: (kind: GenerationPresetKind, presetId: string) => string;
  presetSaveState: PresetSaveState;
  quickGenerationPresets: GenerationPreset[];
  selectedAuthorPreset: GenerationPreset | undefined;
  selectedAuthorPresetId: string;
  selectedChapterBlueprintPreset: GenerationPreset | undefined;
  selectedChapterBlueprintPresetId: string;
  selectedDocumentGenerationPreset: GenerationPreset | undefined;
  selectedDocumentGenerationPresetId: string;
  selectedDocumentPolishPreset: GenerationPreset | undefined;
  selectedDocumentPolishPresetId: string;
  selectedEditorPreset: GenerationPreset | undefined;
  selectedEditorPresetId: string;
  selectedPolishPreset: GenerationPreset | undefined;
  selectedPolishPresetId: string;
  selectedQuickGenerationPreset: GenerationPreset | undefined;
  selectedQuickGenerationPresetId: string;
  selectedWritingPreset: GenerationPreset | undefined;
  selectedWritingPresetId: string;
  setSelectedAuthorPresetId: Dispatch<SetStateAction<string>>;
  setSelectedChapterBlueprintPresetId: Dispatch<SetStateAction<string>>;
  setSelectedDocumentGenerationPresetId: Dispatch<SetStateAction<string>>;
  setSelectedDocumentPolishPresetId: Dispatch<SetStateAction<string>>;
  setSelectedEditorPresetId: Dispatch<SetStateAction<string>>;
  setSelectedPolishPresetId: Dispatch<SetStateAction<string>>;
  setSelectedQuickGenerationPresetId: Dispatch<SetStateAction<string>>;
  setSelectedWritingPresetId: Dispatch<SetStateAction<string>>;
  writingPresets: GenerationPreset[];
};

export type EmbeddingToolboxApi = {
  activeClusterTagId: string | null;
  activeHeatmapTagId: string | null;
  activeTab: EmbeddingToolboxTab;
  analyzeClusters: (
    appliedSettings?: EmbeddingAppliedSettings,
    forceReembed?: boolean,
  ) => Promise<void>;
  analyzeHeatmap: (
    appliedSettings?: EmbeddingAppliedSettings,
    forceReembed?: boolean,
  ) => Promise<void>;
  clusters: ClusterResponse | null;
  draftSettings: EmbeddingAppliedSettings;
  embeddingConfigs: ApiConfig[];
  error: string | null;
  hasUnsavedSettings: boolean;
  heatmap: HeatmapResponse | null;
  isAnalyzing: boolean;
  isClusterMapOpen: boolean;
  isHeatmapVisible: boolean;
  isLoadingSettings: boolean;
  isLoadingTags: boolean;
  isOpen: boolean;
  isSavingSettings: boolean;
  isSavingTag: boolean;
  notice: string | null;
  rangeMode: EmbeddingRangeMode;
  reloadTags: () => Promise<void>;
  removeTag: (tag: EmbeddingTag) => Promise<void>;
  saveNewTag: (input: EmbeddingTagInput) => Promise<void>;
  saveSettingsAndReembed: () => Promise<void>;
  saveTag: (tagId: string, input: EmbeddingTagUpdate) => Promise<void>;
  selectedTagIds: string[];
  setActiveClusterTagId: Dispatch<SetStateAction<string | null>>;
  setActiveHeatmapTagId: Dispatch<SetStateAction<string | null>>;
  setActiveTab: Dispatch<SetStateAction<EmbeddingToolboxTab>>;
  setDraftSettings: Dispatch<SetStateAction<EmbeddingAppliedSettings>>;
  setIsClusterMapOpen: Dispatch<SetStateAction<boolean>>;
  setIsHeatmapVisible: Dispatch<SetStateAction<boolean>>;
  setIsOpen: Dispatch<SetStateAction<boolean>>;
  setRangeMode: Dispatch<SetStateAction<EmbeddingRangeMode>>;
  tags: EmbeddingTag[];
  toggleSelectedTag: (tagId: string) => void;
};

export type TypewriterLayoutToolboxApi = {
  draftSettings: TypewriterLayoutSettingsInput;
  error: string | null;
  hasUnsavedSettings: boolean;
  isOpen: boolean;
  isSaving: boolean;
  notice: string | null;
  savedSettings: TypewriterLayoutSettings;
  resetDraftToDefault: () => void;
  saveSettings: () => Promise<void>;
  setDraftSettings: Dispatch<SetStateAction<TypewriterLayoutSettingsInput>>;
  setIsOpen: Dispatch<SetStateAction<boolean>>;
};

export type ChatSessionsApi = {
  activeSessionId: string | null;
  clearMessages: () => void;
  closeChat: () => void;
  createSession: (activate?: boolean) => Promise<ChatSessionSummary | null>;
  error: string | null;
  isLoading: boolean;
  isOpen: boolean;
  isSessionsLoading: boolean;
  loadSessions: () => Promise<void>;
  messages: ChatMessage[];
  openChat: () => Promise<void>;
  removeSession: (sessionId: string) => Promise<void>;
  renameSession: (sessionId: string, title: string) => Promise<void>;
  selectSession: (sessionId: string) => Promise<void>;
  sendMessage: (content: string, chapterId?: string) => Promise<void>;
  sessions: ChatSessionSummary[];
};
