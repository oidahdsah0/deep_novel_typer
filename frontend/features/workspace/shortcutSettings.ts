"use client";

export const tabQuickGenerationEnabledStorageKey =
  "deep-novel-typer:tab-quick-generation-enabled";

export function readTabQuickGenerationEnabled() {
  if (typeof window === "undefined") {
    return false;
  }
  return window.localStorage.getItem(tabQuickGenerationEnabledStorageKey) === "1";
}

export function writeTabQuickGenerationEnabled(enabled: boolean) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(tabQuickGenerationEnabledStorageKey, enabled ? "1" : "0");
}
