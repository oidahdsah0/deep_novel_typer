"use client";

import { Pencil, RefreshCw, ToggleLeft, ToggleRight, Trash2 } from "lucide-react";
import type { ApiConfig, Perspective } from "@/lib/api/index";
import type { PerspectiveDraft } from "../../types";
import { PerspectiveApiSelector } from "./PerspectiveApiSelector";
import { PerspectiveEditor } from "./PerspectiveEditor";

export function PerspectiveList({
  canRequestSuggestions,
  defaultConfigLabel,
  editingPerspectiveId,
  llmConfigs,
  onCancelEditPerspective,
  onDeletePerspective,
  onEditDraftChange,
  onRequestPerspectiveSuggestion,
  onSavePerspective,
  onSelectPerspectiveConfig,
  onStartEditPerspective,
  onTogglePerspective,
  pendingPerspectiveIds,
  perspectiveEditDraft,
  perspectives,
}: {
  canRequestSuggestions: boolean;
  defaultConfigLabel: string;
  editingPerspectiveId: string | null;
  llmConfigs: ApiConfig[];
  onCancelEditPerspective: () => void;
  onDeletePerspective: (perspective: Perspective) => void;
  onEditDraftChange: (draft: PerspectiveDraft) => void;
  onRequestPerspectiveSuggestion: (perspective: Perspective) => void;
  onSavePerspective: () => void;
  onSelectPerspectiveConfig: (perspective: Perspective, apiConfigId: string | null) => void;
  onStartEditPerspective: (perspective: Perspective) => void;
  onTogglePerspective: (perspective: Perspective) => void;
  pendingPerspectiveIds: Set<string>;
  perspectiveEditDraft: PerspectiveDraft;
  perspectives: Perspective[];
}) {
  return (
    <div className="perspective-list">
      {perspectives.map((perspective) => (
        <PerspectiveListItem
          canRequestSuggestions={canRequestSuggestions}
          defaultConfigLabel={defaultConfigLabel}
          isEditing={editingPerspectiveId === perspective.id}
          key={perspective.id}
          llmConfigs={llmConfigs}
          onCancelEditPerspective={onCancelEditPerspective}
          onDeletePerspective={onDeletePerspective}
          onEditDraftChange={onEditDraftChange}
          onRequestPerspectiveSuggestion={onRequestPerspectiveSuggestion}
          onSavePerspective={onSavePerspective}
          onSelectPerspectiveConfig={onSelectPerspectiveConfig}
          onStartEditPerspective={onStartEditPerspective}
          onTogglePerspective={onTogglePerspective}
          pending={pendingPerspectiveIds.has(perspective.id)}
          perspective={perspective}
          perspectiveEditDraft={perspectiveEditDraft}
        />
      ))}
    </div>
  );
}

function PerspectiveListItem({
  canRequestSuggestions,
  defaultConfigLabel,
  isEditing,
  llmConfigs,
  onCancelEditPerspective,
  onDeletePerspective,
  onEditDraftChange,
  onRequestPerspectiveSuggestion,
  onSavePerspective,
  onSelectPerspectiveConfig,
  onStartEditPerspective,
  onTogglePerspective,
  pending,
  perspective,
  perspectiveEditDraft,
}: {
  canRequestSuggestions: boolean;
  defaultConfigLabel: string;
  isEditing: boolean;
  llmConfigs: ApiConfig[];
  onCancelEditPerspective: () => void;
  onDeletePerspective: (perspective: Perspective) => void;
  onEditDraftChange: (draft: PerspectiveDraft) => void;
  onRequestPerspectiveSuggestion: (perspective: Perspective) => void;
  onSavePerspective: () => void;
  onSelectPerspectiveConfig: (perspective: Perspective, apiConfigId: string | null) => void;
  onStartEditPerspective: (perspective: Perspective) => void;
  onTogglePerspective: (perspective: Perspective) => void;
  pending: boolean;
  perspective: Perspective;
  perspectiveEditDraft: PerspectiveDraft;
}) {
  return (
    <div className="perspective-item">
      <div className={perspective.is_enabled ? "perspective-row enabled" : "perspective-row disabled"}>
        <button
          aria-pressed={perspective.is_enabled}
          className={
            perspective.is_enabled ? "perspective-toggle enabled" : "perspective-toggle disabled"
          }
          onClick={() => onTogglePerspective(perspective)}
          type="button"
        >
          {perspective.is_enabled ? <ToggleRight size={18} /> : <ToggleLeft size={18} />}
          <span>{perspective.name}</span>
        </button>
        <PerspectiveApiSelector
          ariaLabel={`${perspective.name} API 配置`}
          className="perspective-api-select"
          defaultConfigLabel={defaultConfigLabel}
          disabled={isEditing}
          llmConfigs={llmConfigs}
          onChange={(apiConfigId) => onSelectPerspectiveConfig(perspective, apiConfigId)}
          value={perspective.api_config_id}
        />
        <div className="perspective-row-actions">
          <button
            aria-label={`刷新 ${perspective.name} 建议`}
            className="tiny-action"
            disabled={!canRequestSuggestions || pending}
            onClick={() => onRequestPerspectiveSuggestion(perspective)}
            title={`刷新 ${perspective.name} 建议`}
            type="button"
          >
            <RefreshCw size={14} />
          </button>
          <button
            aria-label={`编辑 ${perspective.name}`}
            className={isEditing ? "tiny-action active" : "tiny-action"}
            onClick={() => onStartEditPerspective(perspective)}
            title={`编辑 ${perspective.name}`}
            type="button"
          >
            <Pencil size={14} />
          </button>
          <button
            aria-label={`删除 ${perspective.name}`}
            className="tiny-danger"
            onClick={() => onDeletePerspective(perspective)}
            type="button"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      {isEditing ? (
        <PerspectiveEditor
          defaultConfigLabel={defaultConfigLabel}
          draft={perspectiveEditDraft}
          llmConfigs={llmConfigs}
          mode="edit"
          onCancel={onCancelEditPerspective}
          onChange={onEditDraftChange}
          onSubmit={onSavePerspective}
        />
      ) : null}
    </div>
  );
}
