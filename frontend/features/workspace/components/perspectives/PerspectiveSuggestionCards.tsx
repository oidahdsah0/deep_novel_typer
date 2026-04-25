"use client";

import { ChevronDown, Sparkles } from "lucide-react";
import type { SuggestionCard } from "@/lib/api/index";
import { severityLabels, sourceLabels } from "../../constants";

export function PerspectiveSuggestionCards({
  expandedSuggestionIds,
  onToggleSuggestion,
  suggestionError,
  suggestions,
}: {
  expandedSuggestionIds: Set<string>;
  onToggleSuggestion: (suggestionId: string) => void;
  suggestionError: string | null;
  suggestions: SuggestionCard[];
}) {
  return (
    <>
      {suggestionError ? <div className="suggestion-error">{suggestionError}</div> : null}
      <div className="suggestion-list">
        {suggestions.map((suggestion) => (
          <PerspectiveSuggestionCard
            expanded={expandedSuggestionIds.has(suggestion.id)}
            key={suggestion.id}
            onToggle={() => onToggleSuggestion(suggestion.id)}
            suggestion={suggestion}
          />
        ))}
      </div>
    </>
  );
}

function PerspectiveSuggestionCard({
  expanded,
  onToggle,
  suggestion,
}: {
  expanded: boolean;
  onToggle: () => void;
  suggestion: SuggestionCard;
}) {
  const detail = suggestion.detail?.trim() || suggestion.body;

  return (
    <article
      className={
        expanded
          ? `suggestion-card ${suggestion.severity} expanded`
          : `suggestion-card ${suggestion.severity}`
      }
    >
      <div className="suggestion-meta">
        <span>
          <Sparkles size={14} />
          {suggestion.perspective_name}
        </span>
        <strong>
          {sourceLabels[suggestion.source ?? "local"]} · {severityLabels[suggestion.severity]}
        </strong>
      </div>
      <button
        aria-expanded={expanded}
        className="suggestion-open-button"
        onClick={onToggle}
        type="button"
      >
        <span>{suggestion.title}</span>
        <ChevronDown size={16} />
      </button>
      <p className="suggestion-summary">{suggestion.body}</p>
      {expanded ? (
        <div className="suggestion-detail">
          <p>{detail}</p>
          <dl>
            <div>
              <dt>视角</dt>
              <dd>{suggestion.perspective_name}</dd>
            </div>
            <div>
              <dt>模型</dt>
              <dd>{suggestion.model ?? "本地兜底"}</dd>
            </div>
          </dl>
        </div>
      ) : null}
    </article>
  );
}
