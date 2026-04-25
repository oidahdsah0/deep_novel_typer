"use client";

import { Check, Clipboard } from "lucide-react";

export function DebugJsonViewer({
  copyKey,
  copiedKey,
  onCopy,
  title,
  value,
}: {
  copyKey: string;
  copiedKey: string | null;
  onCopy: (key: string, value: string) => void;
  title: string;
  value: unknown;
}) {
  const text = JSON.stringify(value, null, 2) ?? "undefined";
  return (
    <section className="debug-json-block">
      <DebugBlockHeading
        copied={copiedKey === copyKey}
        onCopy={() => onCopy(copyKey, text)}
        title={title}
      />
      <pre>{text}</pre>
    </section>
  );
}

export function DebugTextViewer({
  copyKey,
  copiedKey,
  onCopy,
  title,
  value,
}: {
  copyKey: string;
  copiedKey: string | null;
  onCopy: (key: string, value: string) => void;
  title: string;
  value: string;
}) {
  return (
    <section className="debug-json-block">
      <DebugBlockHeading
        copied={copiedKey === copyKey}
        onCopy={() => onCopy(copyKey, value)}
        title={title}
      />
      <pre>{value || "无内容"}</pre>
    </section>
  );
}

export function DebugBlockHeading({
  copied,
  onCopy,
  title,
}: {
  copied: boolean;
  onCopy: () => void;
  title: string;
}) {
  return (
    <div className="debug-block-heading">
      <h4>{title}</h4>
      <button className="debug-copy-button" onClick={onCopy} type="button" aria-label="复制">
        {copied ? <Check size={14} /> : <Clipboard size={14} />}
        {copied ? "已复制" : "复制"}
      </button>
    </div>
  );
}
