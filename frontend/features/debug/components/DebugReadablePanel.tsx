"use client";

import type { DebugReadableMessage, DebugRequestLog } from "@/lib/api/index";
import type { DebugDetailTab } from "@/features/debug/debugTypes";
import { formatFullDateTime, formatTokens, requestTypeLabels } from "@/features/debug/debugTypes";
import { DebugBlockHeading, DebugJsonViewer, DebugTextViewer } from "./DebugJsonViewer";

type DebugReadablePanelProps = {
  activeTab: DebugDetailTab;
  copiedKey: string | null;
  log: DebugRequestLog;
  onCopy: (key: string, value: string) => void;
};

type DebugReadableContentProps = Omit<DebugReadablePanelProps, "activeTab">;

export function DebugReadablePanel({ activeTab, copiedKey, log, onCopy }: DebugReadablePanelProps) {
  if (activeTab === "summary") {
    return <SummaryPanel log={log} />;
  }

  if (activeTab === "context") {
    return <ContextPanel copiedKey={copiedKey} log={log} onCopy={onCopy} />;
  }

  if (activeTab === "system") {
    return <MessageList copiedKey={copiedKey} messages={log.debug_readable.system_messages} onCopy={onCopy} />;
  }

  if (activeTab === "user") {
    return <MessageList copiedKey={copiedKey} messages={log.debug_readable.user_messages} onCopy={onCopy} />;
  }

  if (activeTab === "options") {
    return (
      <DebugJsonViewer
        copiedKey={copiedKey}
        copyKey={`${log.id}-options`}
        onCopy={onCopy}
        title="请求参数"
        value={log.debug_readable.request_options}
      />
    );
  }

  if (activeTab === "parsed") {
    return <ParsedPanel copiedKey={copiedKey} log={log} onCopy={onCopy} />;
  }

  if (activeTab === "request") {
    return (
      <DebugJsonViewer
      copiedKey={copiedKey}
      copyKey={`${log.id}-request`}
      onCopy={onCopy}
      title="原始请求"
      value={log.request_body}
    />
    );
  }

  return (
    <DebugJsonViewer
      copiedKey={copiedKey}
      copyKey={`${log.id}-response`}
      onCopy={onCopy}
      title="原始返回"
      value={log.response_body}
    />
  );
}

function SummaryPanel({ log }: { log: DebugRequestLog }) {
  const readable = log.debug_readable;

  return (
    <div className="debug-summary-panel">
      <div className="debug-summary-grid">
        <SummaryItem label="请求类型" value={requestTypeLabels[log.request_type] ?? log.request_type} />
        <SummaryItem label="模型类型" value={log.model_kind} />
        <SummaryItem label="Provider" value={log.provider || "未记录"} />
        <SummaryItem label="Model" value={log.model || "未记录"} />
        <SummaryItem label="状态" value={log.status} />
        <SummaryItem label="时间" value={formatFullDateTime(log.created_at)} />
        <SummaryItem label="耗时" value={log.duration_ms == null ? "未记录" : `${log.duration_ms} ms`} />
        <SummaryItem label="Token" value={formatTokens(log.total_tokens)} />
        <SummaryItem label="System 消息" value={`${readable.system_messages.length} 条`} />
        <SummaryItem label="User 消息" value={`${readable.user_messages.length} 条`} />
        <SummaryItem label="资料素材" value={`${readable.context_materials.length} 项`} />
      </div>
      {log.model_kind === "embedding" ? <EmbeddingSummaryItems summary={readable.embedding_summary} /> : null}
      {log.error_message ? <p className="debug-error">{log.error_message}</p> : null}
      {readable.schema_error ? <p className="debug-error">Schema 校验：{readable.schema_error}</p> : null}
    </div>
  );
}

function EmbeddingSummaryItems({ summary }: { summary: Record<string, unknown> }) {
  const items = [
    ["Run", summary.run_id],
    ["批次", summary.batch_label],
    ["资源", [summary.resource_type, summary.resource_id].filter(Boolean).join(" / ")],
    ["切片", summary.segmentation_mode],
    ["算法", summary.algorithm],
    ["Input", summary.input_count],
    ["向量", summary.embedding_count],
    ["维度", summary.embedding_dimensions],
  ].filter((item) => item[1] !== undefined && item[1] !== "");

  if (items.length === 0) {
    return null;
  }
  return (
    <div className="debug-summary-grid">
      {items.map(([label, value]) => (
        <SummaryItem key={String(label)} label={String(label)} value={formatSummaryValue(value)} />
      ))}
    </div>
  );
}

function formatSummaryValue(value: unknown) {
  if (value === null || value === undefined) {
    return "未记录";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number") {
    return value.toLocaleString("zh-CN");
  }
  return JSON.stringify(value);
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="debug-summary-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ContextPanel({ copiedKey, log, onCopy }: DebugReadableContentProps) {
  const readable = log.debug_readable;

  if (!readable.context_pack && readable.context_materials.length === 0) {
    return <p className="debug-readable-empty">本次请求没有记录上下文素材。</p>;
  }

  return (
    <div className="debug-context-panel">
      {readable.context_pack ? (
        <div className="debug-summary-grid">
          <SummaryItem label="项目" value={readable.context_pack.project_id} />
          <SummaryItem label="任务" value={readable.context_pack.task} />
          <SummaryItem label="焦点" value={`${readable.context_pack.focus.length} 项`} />
          <SummaryItem label="素材" value={`${readable.context_pack.materials.length} 项`} />
          <SummaryItem label="人格" value={`${readable.context_pack.agents.length} 项`} />
          <SummaryItem label="约束" value={`${readable.context_pack.constraints.length} 项`} />
        </div>
      ) : null}
      {readable.context_materials.length > 0 ? (
        <div className="debug-context-materials">
          {readable.context_materials.map((material, index) => (
            <DebugJsonViewer
              copiedKey={copiedKey}
              copyKey={`${log.id}-context-${index}`}
              key={`${log.id}-context-${index}`}
              onCopy={onCopy}
              title={`素材 #${index + 1}`}
              value={material}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function MessageList({
  copiedKey,
  messages,
  onCopy,
}: {
  copiedKey: string | null;
  messages: DebugReadableMessage[];
  onCopy: (key: string, value: string) => void;
}) {
  if (messages.length === 0) {
    return <p className="debug-readable-empty">没有记录该角色消息。</p>;
  }

  return (
    <div className="debug-message-list">
      {messages.map((message, index) => {
        const copyKey = `${message.role}-${index}`;
        return (
          <article className="debug-message-block" key={copyKey}>
            <DebugBlockHeading
              copied={copiedKey === copyKey}
              onCopy={() => onCopy(copyKey, message.content)}
              title={`${message.role} #${index + 1}`}
            />
            <pre>{message.content}</pre>
          </article>
        );
      })}
    </div>
  );
}

function ParsedPanel({ copiedKey, log, onCopy }: DebugReadableContentProps) {
  const readable = log.debug_readable;

  return (
    <div className="debug-parsed-panel">
      {readable.raw_content ? (
        <DebugTextViewer
          copiedKey={copiedKey}
          copyKey={`${log.id}-raw-content`}
          onCopy={onCopy}
          title="原始文本"
          value={readable.raw_content}
        />
      ) : (
        <p className="debug-readable-empty">没有记录原始文本内容。</p>
      )}
      {readable.parsed_payload ? (
        <DebugJsonViewer
          copiedKey={copiedKey}
          copyKey={`${log.id}-parsed`}
          onCopy={onCopy}
          title="解析 JSON"
          value={readable.parsed_payload}
        />
      ) : null}
      {readable.schema_error ? <p className="debug-error">Schema 校验失败：{readable.schema_error}</p> : null}
    </div>
  );
}
