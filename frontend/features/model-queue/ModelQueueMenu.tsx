"use client";

import { Activity, Bot, ChevronDown, Cpu, ListChecks } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  getModelQueueSnapshot,
  type ModelQueueItem,
  type ModelQueueSnapshot,
} from "@/lib/api/index";

const emptySnapshot: ModelQueueSnapshot = {
  worker_count: 0,
  queued_count: 0,
  running_count: 0,
  items: [],
};

const labelMap: Record<string, string> = {
  api_config_health_embedding: "Embedding 健康检查",
  api_config_health_llm: "LLM 健康检查",
  generate_chapter_blueprint: "章节基础铺设",
  generate_document_continuation: "资料续写",
  generate_next_paragraph: "生成下一段落",
  generate_next_section: "生成下一部分",
  quick_generate_next_paragraph: "快速生成下一段",
  perspective_suggestion: "视角建议",
  polish_document_selection: "资料润色",
  polish_selection: "正文润色",
};

const priorityLabels: Record<ModelQueueItem["priority"], string> = {
  auto: "自动",
  batch: "批量",
  manual: "手动",
};

const statusLabels: Record<ModelQueueItem["status"], string> = {
  queued: "等待",
  running: "运行中",
};

type ModelQueueMenuProps = {
  variant?: "default" | "square";
};

export function ModelQueueMenu({ variant = "default" }: ModelQueueMenuProps) {
  const [snapshot, setSnapshot] = useState<ModelQueueSnapshot>(emptySnapshot);
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const totalCount = snapshot.queued_count + snapshot.running_count;
  const isSquare = variant === "square";

  useEffect(() => {
    let cancelled = false;

    async function refresh() {
      const nextSnapshot = await getModelQueueSnapshot();
      if (!cancelled) {
        setSnapshot(nextSnapshot);
      }
    }

    void refresh();
    const timer = window.setInterval(() => void refresh(), 1800);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, []);

  return (
    <div className="model-queue-menu" ref={menuRef}>
      <button
        aria-expanded={isOpen}
        aria-label="模型请求队列"
        className={[
          "model-queue-trigger",
          totalCount > 0 ? "active" : "",
          isSquare ? "square icon-button icon-tooltip" : "",
        ].filter(Boolean).join(" ")}
        data-tooltip={isSquare ? "模型请求队列" : undefined}
        onClick={() => setIsOpen((current) => !current)}
        title={isSquare ? undefined : "模型请求队列"}
        type="button"
      >
        <Activity size={16} />
        {totalCount > 0 ? <span className="model-queue-count">{totalCount}</span> : null}
        <ChevronDown className="model-queue-chevron" size={13} />
      </button>

      {isOpen ? (
        <div className="model-queue-popover" role="menu" aria-label="模型请求队列">
          <header>
            <div>
              <p className="eyebrow">Model Queue</p>
              <h3>{totalCount > 0 ? `${totalCount} 个请求` : "队列空闲"}</h3>
            </div>
            <span>{snapshot.worker_count || "-"} worker</span>
          </header>

          <div className="model-queue-summary">
            <span>运行 {snapshot.running_count}</span>
            <span>等待 {snapshot.queued_count}</span>
          </div>

          {snapshot.items.length > 0 ? (
            <div className="model-queue-list">
              {snapshot.items.map((item) => (
                <ModelQueueRow item={item} key={item.id} />
              ))}
            </div>
          ) : (
            <div className="model-queue-empty">
              <ListChecks size={18} />
              <span>暂无模型请求</span>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}

function ModelQueueRow({ item }: { item: ModelQueueItem }) {
  const Icon = item.kind === "embedding" ? Cpu : Bot;
  const anchorTime = item.status === "running" ? item.started_at : item.queued_at;

  return (
    <div className={`model-queue-row ${item.status}`}>
      <div className="model-queue-row-icon">
        <Icon size={15} />
      </div>
      <div className="model-queue-row-main">
        <strong>{labelMap[item.label] ?? item.label}</strong>
        <span>
          {item.kind === "embedding" ? "Embedding" : "LLM"} · {item.model || "未知模型"}
        </span>
      </div>
      <div className="model-queue-row-meta">
        <span>{statusLabels[item.status]}</span>
        <small>
          {priorityLabels[item.priority]} · {formatElapsed(anchorTime)}
        </small>
      </div>
    </div>
  );
}

function formatElapsed(value: string | null) {
  if (!value) {
    return "刚刚";
  }
  const elapsedSeconds = Math.max(0, Math.round((Date.now() - Date.parse(value)) / 1000));
  if (elapsedSeconds < 60) {
    return `${elapsedSeconds}s`;
  }
  const minutes = Math.floor(elapsedSeconds / 60);
  const seconds = elapsedSeconds % 60;
  return `${minutes}m ${seconds}s`;
}
