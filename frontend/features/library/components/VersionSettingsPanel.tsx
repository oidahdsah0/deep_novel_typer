import { Save } from "lucide-react";

import type { VersionSettings } from "@/lib/api/index";

export function VersionSettingsOverview({ settings }: { settings: VersionSettings }) {
  const ratio = Math.round(settings.auto_min_change_ratio * 100);
  return (
    <div className="settings-overview">
      <article className="settings-card">
        <span>自动版本</span>
        <strong>{settings.auto_enabled ? "已启用" : "已关闭"}</strong>
        <p>自动保存不会逐次入历史，只在达到间隔和变化阈值后生成可回溯版本。</p>
      </article>
      <article className="settings-card">
        <span>时间间隔</span>
        <strong>{settings.auto_interval_minutes} 分钟</strong>
        <p>同一章节或资料距离上次版本至少经过该时间，才会考虑生成自动版本。</p>
      </article>
      <article className="settings-card">
        <span>变化阈值</span>
        <strong>
          {settings.auto_min_chars_changed} 字 / {ratio}%
        </strong>
        <p>字数变化或文本变化比例达到任一条件，才会写入新的自动版本。</p>
      </article>
    </div>
  );
}

export function VersionSettingsDetail({
  onChange,
  onSave,
  settings,
}: {
  onChange: (settings: VersionSettings) => void;
  onSave: () => void;
  settings: VersionSettings;
}) {
  return (
    <>
      <div className="detail-heading">
        <div>
          <p className="eyebrow">Save Policy</p>
          <h2>保存机制</h2>
        </div>
      </div>

      <div className="api-config-form">
        <label className="settings-check">
          <input
            checked={settings.auto_enabled}
            onChange={(event) => onChange({ ...settings, auto_enabled: event.target.checked })}
            type="checkbox"
          />
          <span>启用自动历史版本</span>
        </label>

        <label className="settings-field">
          <span>自动版本最小间隔（分钟）</span>
          <input
            min={1}
            max={240}
            onChange={(event) =>
              onChange({
                ...settings,
                auto_interval_minutes: Number(event.target.value),
              })
            }
            type="number"
            value={settings.auto_interval_minutes}
          />
        </label>

        <label className="settings-field">
          <span>最小变化字数</span>
          <input
            min={1}
            max={10000}
            onChange={(event) =>
              onChange({
                ...settings,
                auto_min_chars_changed: Number(event.target.value),
              })
            }
            type="number"
            value={settings.auto_min_chars_changed}
          />
        </label>

        <label className="settings-field">
          <span>最小变化比例（%）</span>
          <input
            min={0}
            max={100}
            onChange={(event) =>
              onChange({
                ...settings,
                auto_min_change_ratio: Number(event.target.value) / 100,
              })
            }
            type="number"
            value={Math.round(settings.auto_min_change_ratio * 100)}
          />
        </label>
      </div>

      <button className="secondary-button" onClick={onSave} type="button">
        <Save size={16} />
        保存机制设置
      </button>
    </>
  );
}
