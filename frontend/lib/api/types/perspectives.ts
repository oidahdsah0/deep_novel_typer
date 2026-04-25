export type Perspective = {
  id: string;
  name: string;
  description: string;
  instructions: string;
  api_config_id: string | null;
  is_enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type PerspectiveInput = {
  name: string;
  description?: string;
  instructions: string;
  api_config_id?: string | null;
};

export type SuggestionCard = {
  id: string;
  perspective_id: string;
  perspective_name: string;
  title: string;
  body: string;
  detail?: string | null;
  severity: "calm" | "focus" | "risk";
  source?: "llm" | "local";
  model?: string | null;
};
