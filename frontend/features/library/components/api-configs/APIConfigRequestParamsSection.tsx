import type { ApiConfig } from "@/lib/api/index";
import {
  API_CONFIG_MAX_TOKENS,
  API_CONFIG_MIN_TOKENS,
} from "@/features/library/utils";
import type { APIConfigSectionProps } from "./APIConfigFieldTypes";

export function APIConfigRequestParamsSection({
  draft,
  isEmbedding,
  onChange,
  showDefaultToggle,
}: APIConfigSectionProps & {
  isEmbedding: boolean;
  showDefaultToggle: boolean;
}) {
  return (
    <section className="api-config-section">
      <h4>请求参数</h4>
      {!isEmbedding ? (
        <>
          <label className="settings-check">
            <input
              checked={draft.thinking_enabled}
              onChange={(event) => onChange({ ...draft, thinking_enabled: event.target.checked })}
              type="checkbox"
            />
            <span>Thinking</span>
          </label>

          <div className="settings-grid">
            <label className="settings-field">
              <span>推理强度</span>
              <select
                disabled={!draft.thinking_enabled}
                onChange={(event) =>
                  onChange({
                    ...draft,
                    reasoning_effort: event.target.value as ApiConfig["reasoning_effort"],
                  })
                }
                value={draft.reasoning_effort}
              >
                <option value="high">high</option>
                <option value="max">max</option>
              </select>
            </label>

            <label className="settings-field">
              <span>最大输出 tokens</span>
              <input
                max={API_CONFIG_MAX_TOKENS}
                min={API_CONFIG_MIN_TOKENS}
                onChange={(event) => onChange({ ...draft, max_tokens: Number(event.target.value) })}
                step={256}
                type="number"
                value={draft.max_tokens}
              />
            </label>
          </div>

          <label className="settings-field">
            <span>Temperature</span>
            <input
              disabled={draft.thinking_enabled}
              max={2}
              min={0}
              onChange={(event) =>
                onChange({
                  ...draft,
                  temperature: event.target.value === "" ? null : Number(event.target.value),
                })
              }
              placeholder="默认"
              step={0.1}
              type="number"
              value={draft.temperature ?? ""}
            />
          </label>

          <div className="settings-grid">
            <label className="settings-field">
              <span>Top P</span>
              <input
                max={1}
                min={0}
                onChange={(event) =>
                  onChange({
                    ...draft,
                    top_p: event.target.value === "" ? null : Number(event.target.value),
                  })
                }
                placeholder="默认"
                step={0.05}
                type="number"
                value={draft.top_p ?? ""}
              />
            </label>

            <label className="settings-field">
              <span>Top K</span>
              <input
                max={1000}
                min={1}
                onChange={(event) =>
                  onChange({
                    ...draft,
                    top_k: event.target.value === "" ? null : Number(event.target.value),
                  })
                }
                placeholder="默认"
                step={1}
                type="number"
                value={draft.top_k ?? ""}
              />
            </label>
          </div>
        </>
      ) : (
        <p className="empty-note">Embedding 配置当前只发送模型、Endpoint、Key 和 Dimensions。</p>
      )}

      {showDefaultToggle ? (
        <label className="settings-check">
          <input
            checked={draft.is_default}
            onChange={(event) => onChange({ ...draft, is_default: event.target.checked })}
            type="checkbox"
          />
          <span>设为默认配置</span>
        </label>
      ) : null}
    </section>
  );
}
