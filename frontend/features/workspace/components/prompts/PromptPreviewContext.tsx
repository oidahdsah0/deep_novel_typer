"use client";

import type { PromptPreviewResponse } from "@/lib/api/index";
import { formatNumber } from "./promptPreviewUtils";
import { PromptPreviewTextBlock } from "./PromptPreviewTextBlock";

export function PromptPreviewContext({
  contextPack,
  onCopy,
}: {
  contextPack: PromptPreviewResponse["items"][number]["context_pack"];
  onCopy: (value: string) => void;
}) {
  if (!contextPack) {
    return (
      <div className="preview-warning-list">
        <p>没有结构化 Context Pack。</p>
      </div>
    );
  }
  const text = JSON.stringify(contextPack, null, 2);
  return (
    <section className="preview-context-panel">
      <div className="preview-summary-grid">
        <ContextCell label="Context Token" value={formatNumber(contextPack.budget.input_tokens)} />
        <ContextCell label="Focus" value={formatNumber(contextPack.budget.focus_tokens)} />
        <ContextCell label="Materials" value={formatNumber(contextPack.budget.material_tokens)} />
        <ContextCell label="Agents" value={formatNumber(contextPack.budget.agent_tokens)} />
        <ContextCell label="素材块" value={String(contextPack.materials.length)} />
        <ContextCell label="截断素材" value={String(contextPack.budget.truncated_materials)} />
      </div>
      <PromptPreviewTextBlock
        label="Structured Context Pack"
        onCopy={() => onCopy(text)}
        value={text}
      />
    </section>
  );
}

function ContextCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
