"use client";

import { Activity } from "lucide-react";
import type { DebugRequestLog } from "@/lib/api/index";
import { formatDateTime, formatTokens, requestTypeLabels } from "../debugTypes";

export function RequestLogList({
  expandedId,
  logs,
  onSelectLog,
}: {
  expandedId: string;
  logs: DebugRequestLog[];
  onSelectLog: (logId: string) => void;
}) {
  return (
    <div className="debug-log-list" aria-label="请求 Log 列表">
      {logs.length ? (
        logs.map((log) => (
          <button
            className={log.id === expandedId ? "debug-log-row active" : "debug-log-row"}
            key={log.id}
            onClick={() => onSelectLog(log.id)}
            type="button"
          >
            <span className={`debug-status ${log.status}`}>{log.status}</span>
            <strong>{requestTypeLabels[log.request_type] ?? log.request_type}</strong>
            <small>{formatDateTime(log.created_at)} · {log.model_kind}</small>
            <span className="debug-log-token">{formatTokens(log.total_tokens)}</span>
            <span className="debug-log-duration">{log.duration_ms ?? 0} ms</span>
          </button>
        ))
      ) : (
        <div className="debug-empty">
          <Activity size={18} />
          暂无请求 Log。
        </div>
      )}
    </div>
  );
}
