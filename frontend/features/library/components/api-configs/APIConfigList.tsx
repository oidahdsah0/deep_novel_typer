import type {
  ApiConfig,
  ApiConfigHealthCheckResult,
  ApiConfigTemplate,
} from "@/lib/api/index";
import { APIConfigCard } from "@/features/library/components/APIConfigCard";

export function APIConfigList({
  configs,
  healthResults,
  checkingApiConfigId,
  onHealthCheck,
  onSelect,
  selectedConfigId,
  templates,
}: {
  configs: ApiConfig[];
  healthResults: Record<string, ApiConfigHealthCheckResult>;
  checkingApiConfigId: string | null;
  onHealthCheck: (config: ApiConfig) => void;
  onSelect: (configId: string) => void;
  selectedConfigId: string;
  templates: ApiConfigTemplate[];
}) {
  return (
    <div className="project-grid api-config-grid">
      {configs.map((config) => (
        <APIConfigCard
          config={config}
          healthResult={healthResults[config.id]}
          isChecking={checkingApiConfigId === config.id}
          isSelected={config.id === selectedConfigId}
          key={config.id}
          onHealthCheck={() => onHealthCheck(config)}
          onSelect={() => onSelect(config.id)}
          templates={templates}
        />
      ))}
    </div>
  );
}
