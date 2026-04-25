import type { ApiConfigHealthCheckResult } from "@/lib/api/index";
import { apiHealthMetric, formatDateTime, providerName } from "@/features/library/utils";

export function ApiHealthSummary({ result }: { result: ApiConfigHealthCheckResult }) {
  return (
    <small className={result.ok ? "api-health-summary ok" : "api-health-summary error"}>
      {result.ok ? "测试可用" : "测试失败"} · {apiHealthMetric(result)}
    </small>
  );
}

export function ApiHealthPanel({ result }: { result: ApiConfigHealthCheckResult }) {
  return (
    <section className={result.ok ? "api-health-panel ok" : "api-health-panel error"}>
      <div>
        <span>{result.ok ? "连接可用" : "测试失败"}</span>
        <strong>{apiHealthMetric(result)}</strong>
      </div>
      <p>
        {result.ok
          ? result.kind === "embedding"
            ? `Embedding 返回 ${result.embedding_dimensions ?? 0} 维向量。`
            : `非流式 JSON mode ${result.json_mode_supported ? "可用" : "未确认"}。`
          : result.error_message || "API 配置暂不可用。"}
      </p>
      <small>
        {providerName(result.provider)} · {result.model} · {formatDateTime(result.checked_at)}
      </small>
    </section>
  );
}
