"use client";

import { useEffect, useState } from "react";
import { Keyboard, RotateCcw } from "lucide-react";
import type {
  ApiConfig,
  GenerationPreset,
  GenerationPresetKind,
  PromptProfile,
} from "@/lib/api/index";
import { presetSaveLabels } from "../../constants";
import {
  readIncludeChapterSynopsis,
  readPromptTemperature,
} from "../../promptProfileConfig";
import type { PresetSaveState } from "../../types";
import { PresetEditor } from "../generation/PresetEditor";

export function QuickGenerationSettingsPanel({
  authorPreset,
  authorPresets,
  llmConfigs,
  onAddPreset,
  onChangeAuthorPreset,
  onChangePresetContent,
  onDeletePreset,
  onRenamePreset,
  onSaveProfile,
  presetSaveState,
  profileSaveState,
  promptProfiles,
  selectedAuthorPresetId,
}: {
  authorPreset: GenerationPreset | undefined;
  authorPresets: GenerationPreset[];
  llmConfigs: ApiConfig[];
  onAddPreset: (kind: GenerationPresetKind) => void;
  onChangeAuthorPreset: (presetId: string) => void;
  onChangePresetContent: (
    kind: GenerationPresetKind,
    preset: GenerationPreset,
    contentValue: string,
  ) => void;
  onDeletePreset: (preset: GenerationPreset) => void;
  onRenamePreset: (preset: GenerationPreset) => void;
  onSaveProfile: (patch: {
    apiConfigId?: string;
    includeChapterSynopsis?: boolean;
    systemTemplate?: string;
    temperature?: string;
    userTemplate?: string;
  }) => Promise<void>;
  presetSaveState: PresetSaveState;
  profileSaveState: PresetSaveState;
  promptProfiles: PromptProfile[];
  selectedAuthorPresetId: string;
}) {
  const profile = quickGenerationProfile(promptProfiles);
  const profileConfigId = requestProfileApiConfig(profile);
  const selectedConfig =
    llmConfigs.find((config) => config.id === profileConfigId) ??
    llmConfigs.find((config) => config.is_default) ??
    llmConfigs[0];
  const inheritedTemperature =
    selectedConfig?.temperature === null || selectedConfig?.temperature === undefined
      ? "未设置"
      : String(selectedConfig.temperature);
  const profileTemperature = requestProfileTemperature(profile);
  const includeChapterSynopsis = profile ? readIncludeChapterSynopsis(profile.config) : true;
  const [systemTemplateDraft, setSystemTemplateDraft] = useState(
    profile?.system_template ?? "",
  );
  const [userTemplateDraft, setUserTemplateDraft] = useState(profile?.user_template ?? "");
  const [temperatureDraft, setTemperatureDraft] = useState(profileTemperature);

  useEffect(() => {
    setSystemTemplateDraft(profile?.system_template ?? "");
  }, [profile?.system_template]);

  useEffect(() => {
    setUserTemplateDraft(profile?.user_template ?? "");
  }, [profile?.user_template]);

  useEffect(() => {
    setTemperatureDraft(profileTemperature);
  }, [profileTemperature]);

  return (
    <section className="quick-generation-rail-panel" aria-label="Tab 快速生成设置">
      <div className="quick-generation-rail-heading">
        <div>
          <span className="quick-generation-rail-title">
            <Keyboard size={15} />
            Tab 快速生成
          </span>
          <small>{selectedConfig ? selectedConfig.model : "未设置模型"}</small>
        </div>
        <button
          aria-label="清空 Tab 快速生成温度覆盖"
          className="tiny-action"
          onClick={() => void onSaveProfile({ temperature: "" })}
          title="清空温度覆盖"
          type="button"
        >
          <RotateCcw size={14} />
        </button>
      </div>

      <label className="rail-settings-field">
        <span>模型</span>
        <select
          disabled={!profile}
          onChange={(event) => void onSaveProfile({ apiConfigId: event.target.value })}
          value={profileConfigId}
        >
          <option value="">默认 LLM 配置</option>
          {llmConfigs.map((config) => (
            <option key={config.id} value={config.id}>
              {apiConfigLabel(config)}
            </option>
          ))}
        </select>
      </label>

      <label className="rail-settings-field">
        <span>Temperature</span>
        <input
          disabled={!profile}
          max={2}
          min={0}
          onBlur={() => {
            if (profile && temperatureDraft !== profileTemperature) {
              void onSaveProfile({ temperature: temperatureDraft });
            }
          }}
          onChange={(event) => setTemperatureDraft(event.target.value)}
          placeholder={`继承：${inheritedTemperature}`}
          step={0.1}
          type="number"
          value={temperatureDraft}
        />
      </label>

      <label className="rail-settings-check">
        <input
          checked={includeChapterSynopsis}
          disabled={!profile}
          onChange={(event) =>
            void onSaveProfile({ includeChapterSynopsis: event.target.checked })
          }
          type="checkbox"
        />
        <span>包含本章梗概</span>
      </label>

      <div className="quick-generation-author-editor">
        <PresetEditor
          kind="author_persona"
          label="执笔作者人格"
          onAddPreset={onAddPreset}
          onChangePreset={onChangeAuthorPreset}
          onChangePresetContent={onChangePresetContent}
          onDeletePreset={onDeletePreset}
          onRenamePreset={onRenamePreset}
          placeholder="填写作者人格或人格设定 Skill。"
          preset={authorPreset}
          presets={authorPresets}
          selectedPresetId={selectedAuthorPresetId}
        />
        {presetSaveState !== "idle" ? (
          <div className={`preset-save-hint ${presetSaveState}`}>
            {presetSaveLabels[presetSaveState]}
          </div>
        ) : null}
      </div>

      <label className="rail-settings-field">
        <span>System 提示词</span>
        <textarea
          disabled={!profile}
          maxLength={60000}
          onBlur={() => {
            if (profile && systemTemplateDraft !== profile.system_template) {
              void onSaveProfile({ systemTemplate: systemTemplateDraft });
            }
          }}
          onChange={(event) => setSystemTemplateDraft(event.target.value)}
          placeholder="读取 quick_generate_next_paragraph 的 SQL 系统提示词"
          rows={4}
          value={systemTemplateDraft}
        />
      </label>

      <label className="rail-settings-field">
        <span>User 提示词</span>
        <textarea
          disabled={!profile}
          maxLength={60000}
          onBlur={() => {
            if (profile && userTemplateDraft !== profile.user_template) {
              void onSaveProfile({ userTemplate: userTemplateDraft });
            }
          }}
          onChange={(event) => setUserTemplateDraft(event.target.value)}
          placeholder="读取 quick_generate_next_paragraph 的 SQL User 提示词；占位符会保持原样保存"
          rows={5}
          value={userTemplateDraft}
        />
      </label>

      {profileSaveState !== "idle" ? (
        <div className={`preset-save-hint ${profileSaveState}`}>
          {presetSaveLabels[profileSaveState]}
        </div>
      ) : null}
    </section>
  );
}

function quickGenerationProfile(promptProfiles: PromptProfile[]) {
  return promptProfiles.find(
    (item) => item.request_type === "quick_generate_next_paragraph",
  );
}

function requestProfileApiConfig(profile: PromptProfile | undefined) {
  const value = profile?.config.api_config_id;
  return typeof value === "string" ? value : "";
}

function requestProfileTemperature(profile: PromptProfile | undefined) {
  return profile ? readPromptTemperature(profile.config) : "";
}

function apiConfigLabel(config: ApiConfig) {
  const defaultMark = config.is_default ? "默认 · " : "";
  const keyState = config.api_key_required && !config.api_key_configured ? " · 未配置 key" : "";
  return `${defaultMark}${config.name} · ${config.model}${keyState}`;
}
