import { Activity, KeyRound, Pencil, Server, Star, Trash2 } from "lucide-react";

import type {
  ApiConfig,
  ApiConfigHealthCheckResult,
  ApiConfigInput,
  ApiConfigTemplate,
} from "@/lib/api/index";
import { kindLabel } from "@/features/library/utils";
import { ApiHealthPanel } from "@/features/library/components/ApiHealthPanel";
import { APIConfigFields } from "@/features/library/components/APIConfigFields";

export function APIConfigDetail({
  draft,
  healthResult,
  isCheckingHealth,
  isOnlyKindConfig,
  onChange,
  onDelete,
  onHealthCheck,
  onSave,
  onSetDefault,
  selectedConfig,
  templates,
}: {
  draft: ApiConfigInput | null;
  healthResult?: ApiConfigHealthCheckResult;
  isCheckingHealth: boolean;
  isOnlyKindConfig: boolean;
  onChange: (draft: ApiConfigInput) => void;
  onDelete?: () => void;
  onHealthCheck?: () => void;
  onSave: () => void;
  onSetDefault?: () => void;
  selectedConfig?: ApiConfig;
  templates: ApiConfigTemplate[];
}) {
  if (!selectedConfig || !draft) {
    return <p className="empty-note">还没有 API 配置。</p>;
  }

  return (
    <>
      <div className="detail-heading">
        <div>
          <p className="eyebrow">{selectedConfig.is_default ? "默认配置" : "API 配置"}</p>
          <h2>{selectedConfig.name}</h2>
        </div>
        <div className="detail-heading-actions">
          <button
            className="secondary-button compact-action"
            disabled={isCheckingHealth || !onHealthCheck}
            onClick={onHealthCheck}
            type="button"
          >
            <Activity size={16} />
            {isCheckingHealth ? "测试中" : "测试"}
          </button>
          <button
            className="primary-icon-button compact-action"
            disabled={!onSetDefault}
            onClick={onSetDefault}
            type="button"
          >
            <Star size={17} />
            默认
          </button>
        </div>
      </div>

      <div className="detail-meta">
        <span>
          <Server size={15} />
          写作 JSON / 聊天流式
        </span>
        <span>
          <KeyRound size={15} />
          {selectedConfig.api_key_configured ? "Key 已设置" : "Key 未设置"}
        </span>
        <span>{kindLabel(selectedConfig.kind)}</span>
        {selectedConfig.kind === "llm" ? (
          <>
            <span>上下文 {selectedConfig.context_window_tokens.toLocaleString("zh-CN")}</span>
            <span>输出 {selectedConfig.max_tokens.toLocaleString("zh-CN")}</span>
          </>
        ) : null}
      </div>

      {healthResult ? <ApiHealthPanel result={healthResult} /> : null}

      <APIConfigFields
        allowClear
        draft={draft}
        kindLocked
        keyConfigured={selectedConfig.api_key_configured}
        onChange={onChange}
        showDefaultToggle={false}
        templates={templates}
      />

      <button className="secondary-button" onClick={onSave} type="button">
        <Pencil size={16} />
        保存配置
      </button>

      <section className="danger-zone">
        <div>
          <h3>删除配置</h3>
          <p>被视角使用的配置不能删除；最后一套同类型配置也会被保留。</p>
        </div>
        <button
          className="danger-button"
          disabled={isOnlyKindConfig || !onDelete}
          onClick={onDelete}
          type="button"
        >
          <Trash2 size={16} />
          删除配置
        </button>
      </section>
    </>
  );
}
