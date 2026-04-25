import type { PromptProfile } from "@/lib/api/index";
import {
  defaultRecentChapterCount,
  maxRecentChapterCount,
  promptProfileConfigKeys,
  recentChapterConfigKeys,
} from "./constants";
import type { PromptProfileDraft } from "./types";

export function toPromptDraft(profile: PromptProfile): PromptProfileDraft {
  const config = profile.config ?? {};
  const materialConfig = omitManagedPromptConfig(config);
  return {
    ...profile,
    chapter_ids: [...profile.chapter_ids],
    document_ids: [...profile.document_ids],
    config: { ...config },
    apiConfigId: readPromptApiConfigId(config),
    configText: JSON.stringify(materialConfig, null, 2),
    includeChapterSynopsis: readIncludeChapterSynopsis(config),
    recentChapterCount: readRecentChapterCount(config),
    recentChapterEnabled: readRecentChapterEnabled(config),
    temperature: readPromptTemperature(config),
  };
}

export function omitManagedPromptConfig(config: Record<string, unknown>) {
  const result: Record<string, unknown> = {};
  Object.entries(config).forEach(([key, value]) => {
    if (
      key !== recentChapterConfigKeys.enabled &&
      key !== recentChapterConfigKeys.count &&
      key !== promptProfileConfigKeys.apiConfigId &&
      key !== promptProfileConfigKeys.includeChapterSynopsis &&
      key !== promptProfileConfigKeys.temperature
    ) {
      result[key] = value;
    }
  });
  return result;
}

export function readPromptApiConfigId(config: Record<string, unknown>) {
  const value = config[promptProfileConfigKeys.apiConfigId];
  return typeof value === "string" ? value : "";
}

export function readPromptTemperature(config: Record<string, unknown>) {
  return formatPromptTemperature(config[promptProfileConfigKeys.temperature]);
}

export function readIncludeChapterSynopsis(config: Record<string, unknown>) {
  return config[promptProfileConfigKeys.includeChapterSynopsis] !== false;
}

export function normalizePromptTemperature(value: unknown) {
  if (typeof value !== "string" && typeof value !== "number") {
    return null;
  }
  const trimmed = String(value).trim();
  if (!trimmed) {
    return null;
  }
  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed)) {
    return null;
  }
  return Math.min(2, Math.max(0, parsed));
}

export function readRecentChapterEnabled(config: Record<string, unknown>) {
  const value = config[recentChapterConfigKeys.enabled];
  return typeof value === "boolean" ? value : true;
}

export function readRecentChapterCount(config: Record<string, unknown>) {
  return normalizeRecentChapterCount(config[recentChapterConfigKeys.count]);
}

export function normalizeRecentChapterCount(value: unknown) {
  const parsed =
    typeof value === "number"
      ? value
      : typeof value === "string"
        ? Number.parseInt(value, 10)
        : defaultRecentChapterCount;
  if (!Number.isFinite(parsed)) {
    return defaultRecentChapterCount;
  }
  return Math.min(Math.max(Math.trunc(parsed), 0), maxRecentChapterCount);
}

function formatPromptTemperature(value: unknown) {
  const normalized = normalizePromptTemperature(value);
  return normalized === null ? "" : String(normalized);
}
