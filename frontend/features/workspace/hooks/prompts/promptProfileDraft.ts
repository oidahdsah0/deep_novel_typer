import type {
  PromptPreviewProfileOverride,
  PromptProfile,
  PromptRequestType,
} from "@/lib/api/index";
import { promptProfileConfigKeys, recentChapterConfigKeys } from "../../constants";
import { normalizePromptTemperature, normalizeRecentChapterCount } from "../../promptProfileConfig";
import type { PromptProfileDraft } from "../../types";

export function profileForRequestType(
  promptProfiles: PromptProfile[],
  requestType: PromptRequestType,
) {
  return promptProfiles.find((profile) => profile.request_type === requestType);
}

export function buildPromptProfileOverride(
  draft: PromptProfileDraft,
): PromptPreviewProfileOverride | null {
  let config: Record<string, unknown>;
  try {
    const parsedConfig = JSON.parse(draft.configText || "{}") as unknown;
    config =
      parsedConfig && typeof parsedConfig === "object" && !Array.isArray(parsedConfig)
        ? (parsedConfig as Record<string, unknown>)
        : {};
  } catch {
    return null;
  }

  const nextConfig: Record<string, unknown> = {
    ...config,
    [promptProfileConfigKeys.includeChapterSynopsis]: draft.includeChapterSynopsis,
    [recentChapterConfigKeys.enabled]: draft.recentChapterEnabled,
    [recentChapterConfigKeys.count]: normalizeRecentChapterCount(draft.recentChapterCount),
  };
  if (draft.apiConfigId) {
    nextConfig[promptProfileConfigKeys.apiConfigId] = draft.apiConfigId;
  }
  const temperature = normalizePromptTemperature(draft.temperature);
  if (temperature !== null) {
    nextConfig[promptProfileConfigKeys.temperature] = temperature;
  }

  return {
    chapter_ids: draft.chapter_ids,
    config: nextConfig,
    document_ids: draft.document_ids,
    name: draft.name,
    output_contract: draft.output_contract,
    system_template: draft.system_template,
    user_template: draft.user_template,
  };
}
