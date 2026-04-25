import type { ApiConfigKind, ApiConfigTemplate, ApiProvider } from "@/lib/api/index";
import { kindLabel, providerLabel } from "@/features/library/utils";
import type { APIConfigSectionProps } from "./APIConfigFieldTypes";

export function APIConfigProviderSection({
  draft,
  kindLocked = false,
  kindOptions,
  onApplyKind,
  onApplyProvider,
  onChange,
  providerOptions,
  selectedTemplate,
  templates,
}: APIConfigSectionProps & {
  kindLocked?: boolean;
  kindOptions: ApiConfigKind[];
  onApplyKind: (kind: ApiConfigKind) => void;
  onApplyProvider: (provider: ApiProvider) => void;
  providerOptions: ApiProvider[];
  templates: ApiConfigTemplate[];
}) {
  return (
    <section className="api-config-section">
      <h4>供应商与入口</h4>
      <div className="settings-grid">
        <label className="settings-field">
          <span>API 类型</span>
          <select
            disabled={kindLocked}
            onChange={(event) => onApplyKind(event.target.value as ApiConfigKind)}
            value={draft.kind}
          >
            {kindOptions.map((kind) => (
              <option key={kind} value={kind}>
                {kindLabel(kind)}
              </option>
            ))}
          </select>
        </label>

        <label className="settings-field">
          <span>API 供应商</span>
          <select
            onChange={(event) => onApplyProvider(event.target.value as ApiProvider)}
            value={draft.provider}
          >
            {providerOptions.map((provider) => (
              <option key={provider} value={provider}>
                {providerLabel(provider, templates)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="settings-field">
        <span>配置名称</span>
        <input
          onChange={(event) => onChange({ ...draft, name: event.target.value })}
          placeholder={selectedTemplate?.name ?? "DeepSeek 正式"}
          value={draft.name}
        />
      </label>

      <label className="settings-field">
        <span>Endpoint / base_url</span>
        <input
          onChange={(event) => onChange({ ...draft, base_url: event.target.value })}
          placeholder={selectedTemplate?.base_url ?? "https://api.deepseek.com"}
          value={draft.base_url}
        />
      </label>
    </section>
  );
}
