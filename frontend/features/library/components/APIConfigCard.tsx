import { Activity } from "lucide-react";

import type {
  ApiConfig,
  ApiConfigHealthCheckResult,
  ApiConfigTemplate,
} from "@/lib/api/index";
import { kindLabel, providerLabel } from "@/features/library/utils";
import { ApiHealthSummary } from "@/features/library/components/ApiHealthPanel";

export function APIConfigCard({
  config,
  healthResult,
  isChecking,
  isSelected,
  onHealthCheck,
  onSelect,
  templates,
}: {
  config: ApiConfig;
  healthResult?: ApiConfigHealthCheckResult;
  isChecking: boolean;
  isSelected: boolean;
  onHealthCheck: () => void;
  onSelect: () => void;
  templates: ApiConfigTemplate[];
}) {
  return (
    <article
      className={
        isSelected
          ? "project-card project-card-with-actions active"
          : "project-card project-card-with-actions"
      }
    >
      <button className="project-card-main" onClick={onSelect} type="button">
        <span>
          {config.is_default
            ? `默认 ${kindLabel(config.kind)}`
            : `${kindLabel(config.kind)} · ${providerLabel(config.provider, templates)}`}
        </span>
        <h3>{config.name}</h3>
        <p>{config.base_url}</p>
        <small>
          {config.model} · {config.api_key_configured ? "Key 已设置" : "Key 未设置"}
        </small>
        {config.kind === "llm" ? (
          <small>
            上下文 {config.context_window_tokens.toLocaleString("zh-CN")} · 输出{" "}
            {config.max_tokens.toLocaleString("zh-CN")}
          </small>
        ) : null}
        {healthResult ? <ApiHealthSummary result={healthResult} /> : null}
      </button>
      <div className="project-card-actions">
        <button
          aria-label={`测试 ${config.name}`}
          className="project-card-icon"
          disabled={isChecking}
          onClick={onHealthCheck}
          type="button"
        >
          <Activity size={15} />
        </button>
      </div>
    </article>
  );
}
