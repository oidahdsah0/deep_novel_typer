import { apiFetch } from "./client";
import type {
  TypewriterLayoutSettings,
  TypewriterLayoutSettingsInput,
} from "./types/index";

export async function getTypewriterLayoutSettings(): Promise<TypewriterLayoutSettings> {
  return await apiFetch<TypewriterLayoutSettings>("/api/typewriter-layout-settings");
}

export async function updateTypewriterLayoutSettings(
  input: TypewriterLayoutSettingsInput,
): Promise<TypewriterLayoutSettings> {
  return await apiFetch<TypewriterLayoutSettings>("/api/typewriter-layout-settings", {
    body: JSON.stringify(input),
    method: "PATCH",
  });
}
