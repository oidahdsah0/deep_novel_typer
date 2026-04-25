"use client";

import { useState } from "react";
import type { DebugRequestLog } from "@/lib/api/index";
import { detailTabsForKind, formatDateTime, formatTokens, requestTypeLabels } from "@/features/debug/debugTypes";
import type { DebugDetailTab } from "@/features/debug/debugTypes";
import { DebugReadablePanel } from "./DebugReadablePanel";

type RequestLogDetailProps = {
  log: DebugRequestLog | null;
};

export function RequestLogDetail({ log }: RequestLogDetailProps) {
  const [activeTab, setActiveTab] = useState<DebugDetailTab>("summary");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyText = async (key: string, value: string) => {
    await navigator.clipboard.writeText(value);
    setCopiedKey(key);
    window.setTimeout(() => setCopiedKey(null), 1200);
  };

  if (!log) {
    return (
      <article className="debug-log-detail">
        <p className="debug-empty">没有可查看的请求记录。</p>
      </article>
    );
  }
  const tabs = detailTabsForKind(log.model_kind);
  const selectedTab = tabs.some((tab) => tab.id === activeTab) ? activeTab : "summary";

  return (
    <article className="debug-log-detail">
      <header className="debug-log-detail-header">
        <div>
          <span className={`debug-status ${log.status}`}>{log.status}</span>
          <h2>{requestTypeLabels[log.request_type] ?? log.request_type}</h2>
          <p>
            {log.model_kind} · {log.provider} / {log.model} · {formatDateTime(log.created_at)}
          </p>
        </div>
        <div className="debug-log-meta">
          <span>{formatTokens(log.total_tokens)} tokens</span>
          <span>{log.duration_ms == null ? "未记录耗时" : `${log.duration_ms} ms`}</span>
        </div>
      </header>

      {log.error_message ? <p className="debug-error">{log.error_message}</p> : null}

      <div className="debug-readable-tabs" role="tablist">
        {tabs.map((tab) => (
          <button
            aria-selected={selectedTab === tab.id}
            className={selectedTab === tab.id ? "active" : ""}
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            role="tab"
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="debug-readable-panel">
        <DebugReadablePanel activeTab={selectedTab} copiedKey={copiedKey} log={log} onCopy={copyText} />
      </div>
    </article>
  );
}
