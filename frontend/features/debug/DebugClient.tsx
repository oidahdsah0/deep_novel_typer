"use client";

import { ArrowLeft, Database, Trash2 } from "lucide-react";
import Link from "next/link";
import type { DebugSnapshot } from "@/lib/api/index";
import { DebugScopeSwitcher } from "@/features/debug/components/DebugScopeSwitcher";
import { RequestLogDetail } from "@/features/debug/components/RequestLogDetail";
import { RequestLogList } from "@/features/debug/components/RequestLogList";
import { TokenStatsGrid } from "@/features/debug/components/TokenStatsGrid";
import { useDebugLogs } from "@/features/debug/hooks/useDebugLogs";
import { useDebugScope } from "@/features/debug/hooks/useDebugScope";

export function DebugClient({
  activeProjectId,
  returnProjectId,
  initialSnapshot,
}: {
  activeProjectId: string | null;
  returnProjectId: string | null;
  initialSnapshot: DebugSnapshot;
}) {
  const scope = useDebugScope({ activeProjectId, returnProjectId });
  const debug = useDebugLogs({ activeProjectId, initialSnapshot });

  return (
    <main className="debug-shell">
      <header className="debug-header">
        <div className="debug-titlebar">
          <Link className="icon-button" href={scope.backHref} title="返回">
            <ArrowLeft size={18} />
          </Link>
          <div>
            <span className="eyebrow">DEBUG CENTER</span>
            <h1>请求调试</h1>
            <p>{scope.scoped ? `当前项目：${activeProjectId}` : "全部项目请求与 Token 消耗"}</p>
          </div>
        </div>

        <DebugScopeSwitcher
          allDebugHref={scope.allDebugHref}
          onRefresh={debug.refresh}
          projectDebugHref={scope.projectDebugHref}
          scoped={scope.scoped}
          sourceProjectId={scope.sourceProjectId}
        />
      </header>

      <TokenStatsGrid tokenUsage={debug.snapshot.token_usage} onClear={debug.clearTokenUsage} />

      <section className="debug-section debug-log-section">
        <header className="debug-section-heading">
          <div>
            <span className="eyebrow">RAW REQUEST LOG</span>
            <h2>最近 50 次请求</h2>
            <p>完整保留原始请求和原始返回，同时提供可读化拆解。</p>
          </div>
          <div className="debug-clear-actions">
            <button className="secondary-button" onClick={debug.clearRequestLogs} type="button">
              <Trash2 size={16} />
              清空 Log
            </button>
            <button className="danger-button" onClick={debug.clearAll} type="button">
              <Database size={16} />
              清空全部
            </button>
          </div>
        </header>

        <div className="debug-log-layout">
          <RequestLogList logs={debug.snapshot.request_logs} expandedId={debug.expandedId} onSelectLog={debug.setExpandedId} />
          <RequestLogDetail log={debug.expandedLog} />
        </div>
      </section>

      {debug.isPending ? <div className="debug-pending">处理中...</div> : null}
    </main>
  );
}
