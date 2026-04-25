"use client";

import { CircleAlert } from "lucide-react";

export function PromptPreviewWarnings({ warnings }: { warnings: string[] }) {
  return (
    <div className="preview-warning-list">
      {warnings.length ? (
        warnings.map((warning) => (
          <p key={warning}>
            <CircleAlert size={14} />
            {warning}
          </p>
        ))
      ) : (
        <p>没有警告。</p>
      )}
    </div>
  );
}
