"use client";

import { Check, Plus, X } from "lucide-react";
import type { ApiConfig } from "@/lib/api/index";
import type { PerspectiveDraft } from "../../types";
import { PerspectiveApiSelector } from "./PerspectiveApiSelector";

export function PerspectiveEditor({
  defaultConfigLabel,
  draft,
  llmConfigs,
  mode,
  onCancel,
  onChange,
  onSubmit,
}: {
  defaultConfigLabel: string;
  draft: PerspectiveDraft;
  llmConfigs: ApiConfig[];
  mode: "create" | "edit";
  onCancel?: () => void;
  onChange: (draft: PerspectiveDraft) => void;
  onSubmit: () => void;
}) {
  const isValid = Boolean(draft.name.trim() && draft.instructions.trim());
  const isEdit = mode === "edit";

  return (
    <div className={isEdit ? "perspective-edit-form" : "perspective-form"}>
      <input
        aria-label={isEdit ? "编辑视角名称" : "视角名称"}
        onChange={(event) => onChange({ ...draft, name: event.target.value })}
        placeholder="视角名称"
        value={draft.name}
      />
      <input
        aria-label={isEdit ? "编辑视角描述" : "视角描述"}
        onChange={(event) => onChange({ ...draft, description: event.target.value })}
        placeholder="描述"
        value={draft.description}
      />
      <PerspectiveApiSelector
        ariaLabel={isEdit ? "编辑视角 API 配置" : "新视角 API 配置"}
        defaultConfigLabel={defaultConfigLabel}
        llmConfigs={llmConfigs}
        onChange={(api_config_id) => onChange({ ...draft, api_config_id })}
        value={draft.api_config_id}
      />
      <textarea
        aria-label={isEdit ? "编辑视角提示词" : "视角提示词"}
        onChange={(event) => onChange({ ...draft, instructions: event.target.value })}
        placeholder="提示词"
        value={draft.instructions}
      />
      {isEdit ? (
        <div className="perspective-edit-actions">
          <button className="secondary-button compact-action" onClick={onCancel} type="button">
            <X size={15} />
            取消
          </button>
          <button
            className="primary-button compact-action"
            disabled={!isValid}
            onClick={onSubmit}
            type="button"
          >
            <Check size={15} />
            保存
          </button>
        </div>
      ) : (
        <button className="secondary-button" onClick={onSubmit} type="button">
          <Plus size={16} />
          添加视角
        </button>
      )}
    </div>
  );
}
