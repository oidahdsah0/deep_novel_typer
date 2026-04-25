"use client";

import { useEffect, useState, type PointerEvent as ReactPointerEvent } from "react";
import type {
  ApiConfig,
  GenerationPreset,
  GenerationPresetKind,
  PromptProfile,
  SuggestionCard,
  Perspective,
} from "@/lib/api/index";
import { ChapterWritingSynopsisPanel } from "@/features/workspace/components/chapters/ChapterWritingSynopsisPanel";
import type { ChapterWritingSynopsisApi } from "@/features/workspace/hooks/useChapterWritingSynopsis";
import type { PerspectiveDraft, PresetSaveState } from "../../types";
import { PerspectiveRailSection } from "./InsightRailSections";
import { QuickGenerationRailSection } from "./QuickGenerationRailSection";

const perspectiveCollapsedStorageKey = "deep-novel-typer:perspective-rail-collapsed";
const quickGenerationCollapsedStorageKey = "deep-novel-typer:quick-generation-rail-collapsed";

export function InsightRail({
  apiConfigs,
  authorPreset,
  authorPresets,
  canRequestSuggestions,
  chapterWritingSynopsis,
  editingPerspectiveId,
  isChapterResourceActive,
  isBatchSuggestionPending,
  isSuggestionAutoEnabled,
  onAddGenerationPreset,
  onCancelEditPerspective,
  onResizeStart,
  onChangeAuthorPreset,
  onChangePresetContent,
  onCreatePerspective,
  onDeleteGenerationPreset,
  onDeletePerspective,
  onDraftChange,
  onEditDraftChange,
  onRenameGenerationPreset,
  onRequestAllEnabledSuggestions,
  onRequestPerspectiveSuggestion,
  onSavePerspective,
  onSaveQuickGenerationProfile,
  onSelectPerspectiveConfig,
  onStartEditPerspective,
  onTogglePerspective,
  onToggleSuggestionAuto,
  pendingPerspectiveIds,
  perspectiveEditDraft,
  perspectiveDraft,
  perspectives,
  promptProfiles,
  presetSaveState,
  quickGenerationProfileSaveState,
  selectedAuthorPresetId,
  suggestionError,
  suggestions,
}: InsightRailProps) {
  const [isPerspectiveCollapsed, setIsPerspectiveCollapsed] = usePersistedRailCollapse(
    perspectiveCollapsedStorageKey,
  );
  const [isQuickGenerationCollapsed, setIsQuickGenerationCollapsed] =
    usePersistedRailCollapse(quickGenerationCollapsedStorageKey);
  const llmConfigs = apiConfigs.filter((config) => config.kind === "llm");
  const defaultConfigLabel = llmConfigs.find((config) => config.is_default)?.name ?? "未设置";

  return (
    <aside className="insight-rail" aria-label="创作辅助侧栏">
      <button
        className="rail-resize-handle rail-resize-handle-left"
        onPointerDown={onResizeStart}
        type="button"
        aria-label="拖拽调整右侧栏宽度"
      />

      {isChapterResourceActive ? (
        <ChapterWritingSynopsisPanel synopsis={chapterWritingSynopsis} />
      ) : null}

      <PerspectiveRailSection
        canRequestSuggestions={canRequestSuggestions}
        defaultConfigLabel={defaultConfigLabel}
        editingPerspectiveId={editingPerspectiveId}
        isBatchSuggestionPending={isBatchSuggestionPending}
        isCollapsed={isPerspectiveCollapsed}
        isSuggestionAutoEnabled={isSuggestionAutoEnabled}
        llmConfigs={llmConfigs}
        onCancelEditPerspective={onCancelEditPerspective}
        onCreatePerspective={onCreatePerspective}
        onDeletePerspective={onDeletePerspective}
        onDraftChange={onDraftChange}
        onEditDraftChange={onEditDraftChange}
        onRequestAllEnabledSuggestions={onRequestAllEnabledSuggestions}
        onRequestPerspectiveSuggestion={onRequestPerspectiveSuggestion}
        onSavePerspective={onSavePerspective}
        onSelectPerspectiveConfig={onSelectPerspectiveConfig}
        onStartEditPerspective={onStartEditPerspective}
        onToggleCollapsed={() => setIsPerspectiveCollapsed((current) => !current)}
        onTogglePerspective={onTogglePerspective}
        onToggleSuggestionAuto={onToggleSuggestionAuto}
        pendingPerspectiveIds={pendingPerspectiveIds}
        perspectiveDraft={perspectiveDraft}
        perspectiveEditDraft={perspectiveEditDraft}
        perspectives={perspectives}
        suggestionError={suggestionError}
        suggestions={suggestions}
      />

      <QuickGenerationRailSection
        authorPreset={authorPreset}
        authorPresets={authorPresets}
        isCollapsed={isQuickGenerationCollapsed}
        llmConfigs={llmConfigs}
        onAddGenerationPreset={onAddGenerationPreset}
        onChangeAuthorPreset={onChangeAuthorPreset}
        onChangePresetContent={onChangePresetContent}
        onDeleteGenerationPreset={onDeleteGenerationPreset}
        onRenameGenerationPreset={onRenameGenerationPreset}
        onSaveQuickGenerationProfile={onSaveQuickGenerationProfile}
        onToggleCollapsed={() => setIsQuickGenerationCollapsed((current) => !current)}
        presetSaveState={presetSaveState}
        promptProfiles={promptProfiles}
        quickGenerationProfileSaveState={quickGenerationProfileSaveState}
        selectedAuthorPresetId={selectedAuthorPresetId}
      />
    </aside>
  );
}

function usePersistedRailCollapse(storageKey: string) {
  const [isCollapsed, setIsCollapsed] = useState(() => readInitialRailCollapse(storageKey));

  useEffect(() => {
    window.localStorage.setItem(storageKey, isCollapsed ? "1" : "0");
  }, [isCollapsed, storageKey]);

  return [isCollapsed, setIsCollapsed] as const;
}

function readInitialRailCollapse(storageKey: string) {
  if (typeof window === "undefined") {
    return true;
  }
  const storedValue = window.localStorage.getItem(storageKey);
  return storedValue === null ? true : storedValue === "1";
}

type InsightRailProps = {
  apiConfigs: ApiConfig[];
  authorPreset: GenerationPreset | undefined;
  authorPresets: GenerationPreset[];
  canRequestSuggestions: boolean;
  chapterWritingSynopsis: ChapterWritingSynopsisApi;
  editingPerspectiveId: string | null;
  isChapterResourceActive: boolean;
  isBatchSuggestionPending: boolean;
  isSuggestionAutoEnabled: boolean;
  onAddGenerationPreset: (kind: GenerationPresetKind) => Promise<void>;
  onCancelEditPerspective: () => void;
  onChangeAuthorPreset: (presetId: string) => void;
  onChangePresetContent: (
    kind: GenerationPresetKind,
    preset: GenerationPreset,
    contentValue: string,
  ) => void;
  onResizeStart: (event: ReactPointerEvent<HTMLButtonElement>) => void;
  onCreatePerspective: () => void;
  onDeleteGenerationPreset: (preset: GenerationPreset) => Promise<void>;
  onDeletePerspective: (perspective: Perspective) => void;
  onDraftChange: (draft: PerspectiveDraft) => void;
  onEditDraftChange: (draft: PerspectiveDraft) => void;
  onRenameGenerationPreset: (preset: GenerationPreset) => Promise<void>;
  onRequestAllEnabledSuggestions: () => void;
  onRequestPerspectiveSuggestion: (perspective: Perspective) => void;
  onSavePerspective: () => void;
  onSelectPerspectiveConfig: (perspective: Perspective, apiConfigId: string | null) => void;
  onStartEditPerspective: (perspective: Perspective) => void;
  onTogglePerspective: (perspective: Perspective) => void;
  onToggleSuggestionAuto: () => void;
  pendingPerspectiveIds: string[];
  perspectiveEditDraft: PerspectiveDraft;
  perspectiveDraft: PerspectiveDraft;
  perspectives: Perspective[];
  promptProfiles: PromptProfile[];
  presetSaveState: PresetSaveState;
  quickGenerationProfileSaveState: PresetSaveState;
  selectedAuthorPresetId: string;
  onSaveQuickGenerationProfile: (patch: {
    apiConfigId?: string;
    includeChapterSynopsis?: boolean;
    systemTemplate?: string;
    temperature?: string;
    userTemplate?: string;
  }) => Promise<void>;
  suggestionError: string | null;
  suggestions: SuggestionCard[];
};
