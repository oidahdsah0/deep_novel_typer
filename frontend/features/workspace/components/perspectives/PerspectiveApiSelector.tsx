"use client";

import type { ApiConfig } from "@/lib/api/index";

export function PerspectiveApiSelector({
  ariaLabel,
  className,
  defaultConfigLabel,
  disabled = false,
  llmConfigs,
  onChange,
  value,
}: {
  ariaLabel: string;
  className?: string;
  defaultConfigLabel: string;
  disabled?: boolean;
  llmConfigs: ApiConfig[];
  onChange: (apiConfigId: string | null) => void;
  value: string | null;
}) {
  return (
    <select
      aria-label={ariaLabel}
      className={className}
      disabled={disabled}
      onChange={(event) => onChange(event.target.value || null)}
      value={value ?? ""}
    >
      <option value="">默认 · {defaultConfigLabel}</option>
      {llmConfigs.map((config) => (
        <option key={config.id} value={config.id}>
          {config.name}
        </option>
      ))}
    </select>
  );
}
