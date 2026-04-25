import type {
  ApiConfigInput,
  ApiConfigKind,
  ApiConfigTemplate,
  ApiProvider,
} from "@/lib/api/index";
import {
  applyTemplate,
  findTemplate,
  uniqueKinds,
  uniqueProviders,
} from "@/features/library/utils";
import { APIConfigModelSection } from "./APIConfigModelSection";
import { APIConfigProviderSection } from "./APIConfigProviderSection";
import { APIConfigRequestParamsSection } from "./APIConfigRequestParamsSection";
import { APIConfigSecretSection } from "./APIConfigSecretSection";

export function APIConfigFields({
  allowClear = false,
  draft,
  kindLocked = false,
  keyConfigured,
  onChange,
  showDefaultToggle = true,
  templates,
}: {
  allowClear?: boolean;
  draft: ApiConfigInput;
  kindLocked?: boolean;
  keyConfigured: boolean;
  onChange: (draft: ApiConfigInput) => void;
  showDefaultToggle?: boolean;
  templates: ApiConfigTemplate[];
}) {
  const selectableTemplates = kindLocked
    ? templates.filter((template) => template.kind === draft.kind)
    : templates;
  const providerOptions = uniqueProviders(selectableTemplates);
  const kindOptions = kindLocked ? [draft.kind] : uniqueKinds(templates, draft.provider);
  const selectedTemplate = findTemplate(selectableTemplates, draft.provider, draft.kind);
  const isEmbedding = draft.kind === "embedding";

  function applyKind(kind: ApiConfigKind) {
    if (kindLocked) {
      return;
    }
    onChange(applyTemplate(draft, findTemplate(templates, draft.provider, kind)));
  }

  function applyProvider(provider: ApiProvider) {
    const nextDraft = applyTemplate(draft, findTemplate(selectableTemplates, provider, draft.kind));
    onChange(kindLocked ? { ...nextDraft, kind: draft.kind } : nextDraft);
  }

  return (
    <div className="api-config-form">
      <APIConfigProviderSection
        draft={draft}
        kindLocked={kindLocked}
        kindOptions={kindOptions}
        onApplyKind={applyKind}
        onApplyProvider={applyProvider}
        onChange={onChange}
        providerOptions={providerOptions}
        selectedTemplate={selectedTemplate}
        templates={templates}
      />
      <APIConfigModelSection
        draft={draft}
        isEmbedding={isEmbedding}
        onChange={onChange}
        selectedTemplate={selectedTemplate}
      />
      <APIConfigSecretSection
        allowClear={allowClear}
        draft={draft}
        keyConfigured={keyConfigured}
        onChange={onChange}
      />
      <APIConfigRequestParamsSection
        draft={draft}
        isEmbedding={isEmbedding}
        onChange={onChange}
        showDefaultToggle={showDefaultToggle}
      />
    </div>
  );
}
