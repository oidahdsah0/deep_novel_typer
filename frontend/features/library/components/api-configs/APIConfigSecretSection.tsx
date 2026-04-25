import type { APIConfigSectionProps } from "./APIConfigFieldTypes";

export function APIConfigSecretSection({
  allowClear,
  draft,
  keyConfigured,
  onChange,
}: APIConfigSectionProps & {
  allowClear: boolean;
  keyConfigured: boolean;
}) {
  return (
    <section className="api-config-section">
      <h4>密钥</h4>
      <label className="settings-check">
        <input
          checked={draft.api_key_required}
          onChange={(event) => onChange({ ...draft, api_key_required: event.target.checked })}
          type="checkbox"
        />
        <span>需要 API Key</span>
      </label>

      <label className="settings-field">
        <span>API Key</span>
        <input
          autoComplete="off"
          onChange={(event) =>
            onChange({ ...draft, api_key: event.target.value, clear_api_key: false })
          }
          placeholder={
            keyConfigured
              ? "已保存，留空不变"
              : draft.api_key_required
                ? "未设置"
                : "本地服务通常留空"
          }
          type="password"
          value={draft.api_key ?? ""}
        />
      </label>

      {allowClear ? (
        <label className="settings-check muted">
          <input
            checked={Boolean(draft.clear_api_key)}
            disabled={!keyConfigured && !draft.api_key}
            onChange={(event) =>
              onChange({
                ...draft,
                api_key: event.target.checked ? null : draft.api_key,
                clear_api_key: event.target.checked,
              })
            }
            type="checkbox"
          />
          <span>清除已保存的 API Key</span>
        </label>
      ) : null}
    </section>
  );
}
