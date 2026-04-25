import type { VersionedResourceType, VersionType } from "./common";

export type VersionSettings = {
  auto_enabled: boolean;
  auto_interval_minutes: number;
  auto_min_chars_changed: number;
  auto_min_change_ratio: number;
  updated_at: string | null;
};

export type VersionSettingsInput = Partial<
  Pick<
    VersionSettings,
    | "auto_enabled"
    | "auto_interval_minutes"
    | "auto_min_chars_changed"
    | "auto_min_change_ratio"
  >
>;

export type ResourceVersion = {
  id: string;
  project_id: string;
  resource_type: VersionedResourceType;
  resource_id: string;
  resource_title: string;
  version_type: VersionType;
  label: string | null;
  note: string;
  word_count: number;
  char_count: number;
  created_at: string;
};

export type ResourceVersionDetail = ResourceVersion & {
  content: string;
};

export type CreateResourceVersionInput = {
  resource_type: VersionedResourceType;
  resource_id: string;
  version_type?: VersionType;
  label?: string | null;
  note?: string;
};

export type RestoreResourceVersionResponse = {
  resource_type: VersionedResourceType;
  resource_id: string;
  title: string;
  content: string;
  word_count: number;
  updated_at: string;
};
