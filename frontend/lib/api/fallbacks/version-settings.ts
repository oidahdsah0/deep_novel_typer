import type { VersionSettings } from "../types/index";

export const fallbackVersionSettings: VersionSettings = {
  auto_enabled: true,
  auto_interval_minutes: 10,
  auto_min_chars_changed: 300,
  auto_min_change_ratio: 0.15,
  updated_at: null,
};
