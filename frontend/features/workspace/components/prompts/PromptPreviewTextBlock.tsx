"use client";

import { Copy } from "lucide-react";

export function PromptPreviewTextBlock({
  label,
  onCopy,
  value,
}: {
  label: string;
  onCopy: () => void;
  value: string;
}) {
  return (
    <section className="preview-text-block">
      <div className="preview-block-heading">
        <span>{label}</span>
        <button className="icon-button" onClick={onCopy} type="button" aria-label={`复制 ${label}`}>
          <Copy size={15} />
        </button>
      </div>
      <textarea readOnly value={value || "无内容"} />
    </section>
  );
}
