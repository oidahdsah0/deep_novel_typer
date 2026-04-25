"use client";

import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import type {
  ApiConfig,
  SuggestionCard,
  Perspective,
} from "@/lib/api/index";
import type { PerspectiveDraft } from "../../types";
import { PerspectiveEditor } from "./PerspectiveEditor";
import { PerspectiveList } from "./PerspectiveList";
import { PerspectiveQueueStatus } from "./PerspectiveQueueStatus";
import { PerspectiveSuggestionCards } from "./PerspectiveSuggestionCards";

export function PerspectiveRailSection({
  canRequestSuggestions,
  defaultConfigLabel,
  editingPerspectiveId,
  isBatchSuggestionPending,
  isCollapsed,
  isSuggestionAutoEnabled,
  llmConfigs,
  onCancelEditPerspective,
  onCreatePerspective,
  onDeletePerspective,
  onDraftChange,
  onEditDraftChange,
  onRequestAllEnabledSuggestions,
  onRequestPerspectiveSuggestion,
  onSavePerspective,
  onSelectPerspectiveConfig,
  onStartEditPerspective,
  onToggleCollapsed,
  onTogglePerspective,
  onToggleSuggestionAuto,
  pendingPerspectiveIds,
  perspectiveDraft,
  perspectiveEditDraft,
  perspectives,
  suggestionError,
  suggestions,
}: PerspectiveRailSectionProps) {
  const [expandedSuggestionIds, setExpandedSuggestionIds] = useState<Set<string>>(new Set());
  const pendingPerspectiveSet = new Set(pendingPerspectiveIds);
  const enabledPerspectiveIds = perspectives
    .filter((perspective) => perspective.is_enabled)
    .map((perspective) => perspective.id);
  const canRequestEnabledSuggestions = canRequestSuggestions && enabledPerspectiveIds.length > 0;
  const areAllEnabledSuggestionsPending =
    enabledPerspectiveIds.length > 0 &&
    enabledPerspectiveIds.every((perspectiveId) => pendingPerspectiveSet.has(perspectiveId));
  const areAllSuggestionsExpanded =
    suggestions.length > 0 &&
    suggestions.every((suggestion) => expandedSuggestionIds.has(suggestion.id));

  function toggleSuggestion(suggestionId: string) {
    setExpandedSuggestionIds((current) => {
      const next = new Set(current);
      if (next.has(suggestionId)) {
        next.delete(suggestionId);
      } else {
        next.add(suggestionId);
      }
      return next;
    });
  }

  function toggleAllSuggestions() {
    setExpandedSuggestionIds((current) => {
      if (suggestions.length > 0 && suggestions.every((suggestion) => current.has(suggestion.id))) {
        return new Set();
      }
      return new Set(suggestions.map((suggestion) => suggestion.id));
    });
  }

  return (
    <section className="perspective-rail-section" aria-label="AI 视角建议">
      <header
        className={
          isCollapsed
            ? "insight-header rail-collapsible-heading collapsed"
            : "insight-header rail-collapsible-heading"
        }
      >
        <button
          aria-expanded={!isCollapsed}
          className="rail-section-toggle"
          onClick={onToggleCollapsed}
          type="button"
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
          <span className="rail-section-toggle-copy">
            <span className="eyebrow">AI Perspectives</span>
            <span className="rail-section-title">视角建议</span>
          </span>
        </button>
        {isCollapsed ? null : (
          <PerspectiveQueueStatus
            areAllEnabledSuggestionsPending={areAllEnabledSuggestionsPending}
            areAllSuggestionsExpanded={areAllSuggestionsExpanded}
            canRequestEnabledSuggestions={canRequestEnabledSuggestions}
            isBatchSuggestionPending={isBatchSuggestionPending}
            isSuggestionAutoEnabled={isSuggestionAutoEnabled}
            onRequestAllEnabledSuggestions={onRequestAllEnabledSuggestions}
            onToggleAllSuggestions={toggleAllSuggestions}
            onToggleSuggestionAuto={onToggleSuggestionAuto}
            suggestionCount={suggestions.length}
          />
        )}
      </header>

      {isCollapsed ? null : (
        <>
          <div className="llm-summary" aria-label="API 配置摘要">
            <span>默认 · {defaultConfigLabel}</span>
            <span>{llmConfigs.length} 套 LLM 配置</span>
          </div>

          <PerspectiveList
            canRequestSuggestions={canRequestSuggestions}
            defaultConfigLabel={defaultConfigLabel}
            editingPerspectiveId={editingPerspectiveId}
            llmConfigs={llmConfigs}
            onCancelEditPerspective={onCancelEditPerspective}
            onDeletePerspective={onDeletePerspective}
            onEditDraftChange={onEditDraftChange}
            onRequestPerspectiveSuggestion={onRequestPerspectiveSuggestion}
            onSavePerspective={onSavePerspective}
            onSelectPerspectiveConfig={onSelectPerspectiveConfig}
            onStartEditPerspective={onStartEditPerspective}
            onTogglePerspective={onTogglePerspective}
            pendingPerspectiveIds={pendingPerspectiveSet}
            perspectiveEditDraft={perspectiveEditDraft}
            perspectives={perspectives}
          />

          <PerspectiveEditor
            defaultConfigLabel={defaultConfigLabel}
            draft={perspectiveDraft}
            llmConfigs={llmConfigs}
            mode="create"
            onChange={onDraftChange}
            onSubmit={onCreatePerspective}
          />

          <PerspectiveSuggestionCards
            expandedSuggestionIds={expandedSuggestionIds}
            onToggleSuggestion={toggleSuggestion}
            suggestionError={suggestionError}
            suggestions={suggestions}
          />
        </>
      )}
    </section>
  );
}

type PerspectiveRailSectionProps = {
  canRequestSuggestions: boolean;
  defaultConfigLabel: string;
  editingPerspectiveId: string | null;
  isBatchSuggestionPending: boolean;
  isCollapsed: boolean;
  isSuggestionAutoEnabled: boolean;
  llmConfigs: ApiConfig[];
  onCancelEditPerspective: () => void;
  onCreatePerspective: () => void;
  onDeletePerspective: (perspective: Perspective) => void;
  onDraftChange: (draft: PerspectiveDraft) => void;
  onEditDraftChange: (draft: PerspectiveDraft) => void;
  onRequestAllEnabledSuggestions: () => void;
  onRequestPerspectiveSuggestion: (perspective: Perspective) => void;
  onSavePerspective: () => void;
  onSelectPerspectiveConfig: (perspective: Perspective, apiConfigId: string | null) => void;
  onStartEditPerspective: (perspective: Perspective) => void;
  onToggleCollapsed: () => void;
  onTogglePerspective: (perspective: Perspective) => void;
  onToggleSuggestionAuto: () => void;
  pendingPerspectiveIds: string[];
  perspectiveDraft: PerspectiveDraft;
  perspectiveEditDraft: PerspectiveDraft;
  perspectives: Perspective[];
  suggestionError: string | null;
  suggestions: SuggestionCard[];
};
