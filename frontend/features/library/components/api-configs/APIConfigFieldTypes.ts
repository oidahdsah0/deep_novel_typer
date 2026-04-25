import type { ApiConfigInput, ApiConfigTemplate } from "@/lib/api/index";

export type APIConfigSectionProps = {
  draft: ApiConfigInput;
  onChange: (draft: ApiConfigInput) => void;
  selectedTemplate?: ApiConfigTemplate;
};
