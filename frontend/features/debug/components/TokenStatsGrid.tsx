"use client";

import { Eraser } from "lucide-react";
import type { DebugTokenUsage } from "@/lib/api/index";

export function TokenStatsGrid({
  onClear,
  tokenUsage,
}: {
  onClear: () => void;
  tokenUsage: DebugTokenUsage;
}) {
  return (
    <section className="debug-section">
      <div className="debug-section-heading">
        <div>
          <p className="eyebrow">Token Usage</p>
          <h2>Token 统计</h2>
        </div>
        <button className="secondary-button compact-action" onClick={onClear} type="button">
          <Eraser size={15} />
          清空统计
        </button>
      </div>
      <div className="debug-token-grid">
        <TokenCard label="今日 Token" value={tokenUsage.today} />
        <TokenCard label="近 7 日 Token" value={tokenUsage.last_7_days} />
        <TokenCard label="近 30 日 Token" value={tokenUsage.last_30_days} />
        <TokenCard label="总 Token" value={tokenUsage.total} />
      </div>
      {tokenUsage.unknown_usage_requests ? (
        <p className="debug-note">
          有 {tokenUsage.unknown_usage_requests} 次请求未返回 usage，未计入 Token 总量。
        </p>
      ) : null}
    </section>
  );
}

function TokenCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="debug-token-card">
      <span>{label}</span>
      <strong>{value.toLocaleString("zh-CN")}</strong>
    </article>
  );
}
