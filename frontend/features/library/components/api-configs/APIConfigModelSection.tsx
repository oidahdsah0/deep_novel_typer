import {
  API_CONFIG_MAX_CONTEXT_WINDOW_TOKENS,
  API_CONFIG_MIN_CONTEXT_WINDOW_TOKENS,
} from "@/features/library/utils";
import type { APIConfigSectionProps } from "./APIConfigFieldTypes";

export function APIConfigModelSection({
  draft,
  isEmbedding,
  onChange,
  selectedTemplate,
}: APIConfigSectionProps & {
  isEmbedding: boolean;
}) {
  return (
    <section className="api-config-section">
      <h4>模型</h4>
      <div className="settings-grid">
        <label className="settings-field">
          <span>{isEmbedding ? "Embedding 模型" : "模型"}</span>
          <input
            onChange={(event) => onChange({ ...draft, model: event.target.value })}
            placeholder={selectedTemplate?.model ?? "deepseek-v4-pro"}
            value={draft.model}
          />
        </label>

        {isEmbedding ? (
          <label className="settings-field">
            <span>Dimensions</span>
            <input
              min={1}
              onChange={(event) =>
                onChange({
                  ...draft,
                  dimensions: event.target.value === "" ? null : Number(event.target.value),
                })
              }
              placeholder="默认"
              type="number"
              value={draft.dimensions ?? ""}
            />
          </label>
        ) : (
          <label className="settings-field">
            <span>上下文窗口 tokens</span>
            <input
              max={API_CONFIG_MAX_CONTEXT_WINDOW_TOKENS}
              min={API_CONFIG_MIN_CONTEXT_WINDOW_TOKENS}
              onChange={(event) =>
                onChange({ ...draft, context_window_tokens: Number(event.target.value) })
              }
              step={1024}
              type="number"
              value={draft.context_window_tokens}
            />
          </label>
        )}
      </div>
      {!isEmbedding ? (
        <p className="api-config-field-note">
          上下文窗口用于本地预算检查；最大输出 tokens 才会发送给模型 API。
        </p>
      ) : null}
    </section>
  );
}
