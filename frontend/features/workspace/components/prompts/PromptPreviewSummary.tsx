"use client";

import type { PromptPreviewResponse } from "@/lib/api/index";
import { promptRequestLabels } from "../../constants";
import { formatNullableNumber, formatNumber } from "./promptPreviewUtils";

export function PromptPreviewSummary({
  item,
  preview,
}: {
  item: PromptPreviewResponse["items"][number];
  preview: PromptPreviewResponse;
}) {
  const contextUsage = item.token_estimate.context_usage_ratio;
  const contextState = item.token_estimate.context_window_exceeded ? " exceeded" : "";
  return (
    <div className="preview-summary-stack">
      <section className="preview-token-grid" aria-label="Token 估算">
        <div className="preview-token-total">
          <span>输入 Token 估算</span>
          <strong>{formatNumber(item.token_estimate.input_tokens)}</strong>
          <small>按最终请求消息估算</small>
        </div>
        <div>
          <span>System</span>
          <strong>{formatNumber(item.token_estimate.system_tokens)}</strong>
        </div>
        <div>
          <span>User</span>
          <strong>{formatNumber(item.token_estimate.user_tokens)}</strong>
        </div>
        <div>
          <span>输出上限</span>
          <strong>{formatNullableNumber(item.token_estimate.output_token_budget)}</strong>
        </div>
        <div>
          <span>输入 + 输出上限</span>
          <strong>{formatNullableNumber(item.token_estimate.total_with_output_budget)}</strong>
        </div>
        <div className={`preview-token-window${contextState}`}>
          <span>上下文窗口</span>
          <strong>{formatNullableNumber(item.token_estimate.context_window_tokens)}</strong>
          <small>{contextUsage === null ? "未设置" : `${Math.round(contextUsage * 100)}%`}</small>
        </div>
      </section>
      <section className="preview-summary-grid">
        <SummaryCell label="请求类型" value={promptRequestLabels[preview.request_type]} />
        <SummaryCell label="请求组" value={item.label} />
        <SummaryCell label="API 配置" value={item.api_config?.name ?? "未设置"} />
        <SummaryCell label="模型" value={item.api_config?.model || "未设置"} />
        <SummaryCell
          label="模型上下文"
          value={formatNullableNumber(item.api_config?.context_window_tokens ?? null)}
        />
        <SummaryCell label="供应商" value={item.api_config?.provider || "未设置"} />
        <SummaryCell label="Key 状态" value={item.api_config?.configured ? "可用" : "不可用"} />
      </section>
    </div>
  );
}

function SummaryCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
