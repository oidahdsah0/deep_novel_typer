"use client";

import type { ApiConfig } from "@/lib/api/index";
import type { PromptProfileDraft } from "../../types";

export function PromptConfigToolbar({
  apiConfigs,
  draft,
  onChangeDraft,
}: {
  apiConfigs: ApiConfig[];
  draft: PromptProfileDraft;
  onChangeDraft: (patch: Partial<PromptProfileDraft>) => void;
}) {
  const llmConfigs = apiConfigs.filter((config) => config.kind === "llm");
  const selectedApiConfig = llmConfigs.find((config) => config.id === draft.apiConfigId);
  const inheritedConfig =
    selectedApiConfig ?? llmConfigs.find((config) => config.is_default) ?? llmConfigs[0];
  const inheritedTemperature =
    inheritedConfig?.temperature === null || inheritedConfig?.temperature === undefined
      ? "未设置"
      : String(inheritedConfig.temperature);

  return (
    <>
      <label className="settings-field">
        <span>配置名称</span>
        <input onChange={(event) => onChangeDraft({ name: event.target.value })} value={draft.name} />
      </label>

      <div className="prompt-request-config-row">
        <label className="settings-field">
          <span>请求模型</span>
          <select
            onChange={(event) => onChangeDraft({ apiConfigId: event.target.value })}
            value={draft.apiConfigId}
          >
            <option value="">默认 LLM 配置</option>
            {llmConfigs.map((config) => (
              <option key={config.id} value={config.id}>
                {apiConfigLabel(config)}
              </option>
            ))}
            {draft.apiConfigId && !selectedApiConfig ? (
              <option value={draft.apiConfigId}>已删除配置：{draft.apiConfigId}</option>
            ) : null}
          </select>
        </label>

        <label className="settings-field">
          <span>Temperature</span>
          <input
            max={2}
            min={0}
            onChange={(event) => onChangeDraft({ temperature: event.target.value })}
            placeholder={`继承：${inheritedTemperature}`}
            step={0.1}
            type="number"
            value={draft.temperature}
          />
        </label>
      </div>

      <label className="settings-check prompt-context-toggle">
        <input
          checked={draft.includeChapterSynopsis}
          onChange={(event) =>
            onChangeDraft({ includeChapterSynopsis: event.target.checked })
          }
          type="checkbox"
        />
        <span>包含本章梗概</span>
      </label>
    </>
  );
}

function apiConfigLabel(config: ApiConfig) {
  const defaultMark = config.is_default ? "默认 · " : "";
  const keyState = config.api_key_required && !config.api_key_configured ? " · 未配置 key" : "";
  return `${defaultMark}${config.name} · ${config.model}${keyState}`;
}
