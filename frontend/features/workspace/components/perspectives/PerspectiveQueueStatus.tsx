"use client";

import { PanelRight, Power, RefreshCw } from "lucide-react";

export function PerspectiveQueueStatus({
  areAllEnabledSuggestionsPending,
  areAllSuggestionsExpanded,
  canRequestEnabledSuggestions,
  isBatchSuggestionPending,
  isSuggestionAutoEnabled,
  onRequestAllEnabledSuggestions,
  onToggleAllSuggestions,
  onToggleSuggestionAuto,
  suggestionCount,
}: {
  areAllEnabledSuggestionsPending: boolean;
  areAllSuggestionsExpanded: boolean;
  canRequestEnabledSuggestions: boolean;
  isBatchSuggestionPending: boolean;
  isSuggestionAutoEnabled: boolean;
  onRequestAllEnabledSuggestions: () => void;
  onToggleAllSuggestions: () => void;
  onToggleSuggestionAuto: () => void;
  suggestionCount: number;
}) {
  return (
    <div className="header-actions">
      <button
        aria-label={isSuggestionAutoEnabled ? "关闭自动建议" : "开启自动建议"}
        aria-pressed={isSuggestionAutoEnabled}
        className={isSuggestionAutoEnabled ? "auto-suggestion-toggle active" : "auto-suggestion-toggle"}
        onClick={onToggleSuggestionAuto}
        title={isSuggestionAutoEnabled ? "关闭自动建议" : "开启自动建议"}
        type="button"
      >
        <Power size={15} />
        <span>自动</span>
      </button>
      <button
        aria-label="刷新已开启视角建议"
        className={isBatchSuggestionPending ? "icon-button busy" : "icon-button"}
        disabled={!canRequestEnabledSuggestions || areAllEnabledSuggestionsPending}
        onClick={onRequestAllEnabledSuggestions}
        title="刷新已开启视角建议"
        type="button"
      >
        <RefreshCw size={18} />
      </button>
      <button
        aria-label={areAllSuggestionsExpanded ? "收起全部建议详情" : "展开全部建议详情"}
        className="icon-button"
        disabled={suggestionCount === 0}
        onClick={onToggleAllSuggestions}
        title={areAllSuggestionsExpanded ? "收起全部建议详情" : "展开全部建议详情"}
        type="button"
      >
        <PanelRight size={18} />
      </button>
    </div>
  );
}
