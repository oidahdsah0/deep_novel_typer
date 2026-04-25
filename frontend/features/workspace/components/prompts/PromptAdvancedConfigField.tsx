"use client";

import { CircleAlert } from "lucide-react";
import { useState } from "react";
import { materialConfigHelpText } from "../../constants";
import type { HelpTooltip, PromptProfileDraft } from "../../types";
import { clamp } from "../../utils";

export function PromptAdvancedConfigField({
  draft,
  onChangeDraft,
}: {
  draft: PromptProfileDraft;
  onChangeDraft: (patch: Partial<PromptProfileDraft>) => void;
}) {
  const [helpTooltip, setHelpTooltip] = useState<HelpTooltip | null>(null);

  function showHelpTooltip(target: HTMLElement) {
    const rect = target.getBoundingClientRect();
    const tooltipWidth = Math.min(300, window.innerWidth - 24);
    const left = clamp(
      rect.left + rect.width / 2,
      12 + tooltipWidth / 2,
      window.innerWidth - 12 - tooltipWidth / 2,
    );
    const placement = rect.top > 128 ? "top" : "bottom";
    setHelpTooltip({
      left,
      placement,
      text: materialConfigHelpText,
      top: placement === "top" ? rect.top - 8 : rect.bottom + 8,
    });
  }

  return (
    <>
      <label className="settings-field">
        <span className="settings-label-with-help">
          高级配置 JSON
          <span
            aria-label="素材配置说明"
            className="inline-help"
            onBlur={() => setHelpTooltip(null)}
            onFocus={(event) => showHelpTooltip(event.currentTarget)}
            onMouseEnter={(event) => showHelpTooltip(event.currentTarget)}
            onMouseLeave={() => setHelpTooltip(null)}
            tabIndex={0}
          >
            <CircleAlert size={14} aria-hidden="true" />
          </span>
        </span>
        <textarea
          className="prompt-config-editor"
          onChange={(event) => onChangeDraft({ configText: event.target.value })}
          value={draft.configText}
        />
      </label>
      {helpTooltip ? (
        <div
          className={`floating-help-tooltip ${helpTooltip.placement}`}
          role="tooltip"
          style={{ left: helpTooltip.left, top: helpTooltip.top }}
        >
          {helpTooltip.text}
        </div>
      ) : null}
    </>
  );
}
