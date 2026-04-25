"use client";

import type { PromptProfileDraft } from "../../types";

export function PromptOutputContractPanel({
  draft,
  onChangeDraft,
}: {
  draft: PromptProfileDraft;
  onChangeDraft: (patch: Partial<PromptProfileDraft>) => void;
}) {
  return (
    <label className="settings-field">
      <span>输出契约（附加到 System，可编辑）</span>
      <textarea
        className="prompt-contract-editor"
        onChange={(event) => onChangeDraft({ output_contract: event.target.value })}
        value={draft.output_contract}
      />
    </label>
  );
}
