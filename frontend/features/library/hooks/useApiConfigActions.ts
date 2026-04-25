import type { Dispatch, SetStateAction, TransitionStartFunction } from "react";

import {
  checkApiConfigHealth,
  createApiConfig,
  deleteApiConfig,
  setDefaultApiConfig,
  updateApiConfig,
  type ApiConfig,
  type ApiConfigHealthCheckResult,
  type ApiConfigInput,
  type ApiConfigTemplate,
  type LibrarySnapshot,
} from "@/lib/api/index";
import {
  normalizeApiConfigInput,
  sortApiConfigs,
  templateToApiConfigInput,
} from "@/features/library/utils";
import { useConfirm, useNotice } from "@/components/dialog";

export function useApiConfigActions({
  apiDraft,
  library,
  selectedConfig,
  selectedConfigDraft,
  setApiDraft,
  setApiEditDraft,
  setApiHealthResults,
  setCheckingApiConfigId,
  setLibrary,
  setSelectedConfigId,
  onApiConfigCreated,
  startTransition,
  templates,
}: {
  apiDraft: ApiConfigInput;
  library: LibrarySnapshot;
  selectedConfig?: ApiConfig;
  selectedConfigDraft: ApiConfigInput | null;
  setApiDraft: Dispatch<SetStateAction<ApiConfigInput>>;
  setApiEditDraft: Dispatch<SetStateAction<ApiConfigInput | null>>;
  setApiHealthResults: Dispatch<SetStateAction<Record<string, ApiConfigHealthCheckResult>>>;
  setCheckingApiConfigId: Dispatch<SetStateAction<string | null>>;
  setLibrary: Dispatch<SetStateAction<LibrarySnapshot>>;
  setSelectedConfigId: Dispatch<SetStateAction<string>>;
  onApiConfigCreated?: () => void;
  startTransition: TransitionStartFunction;
  templates: ApiConfigTemplate[];
}) {
  const confirm = useConfirm();
  const notice = useNotice();

  function refreshApiConfig(config: ApiConfig) {
    setApiHealthResults((current) => {
      const next = { ...current };
      delete next[config.id];
      return next;
    });
    setLibrary((current) => ({
      ...current,
      api_configs: current.api_configs
        .map((item) =>
          item.id === config.id
            ? config
            : config.is_default && item.kind === config.kind
              ? { ...item, is_default: false }
              : item,
        )
        .sort(sortApiConfigs),
    }));
  }

  function handleCreateApiConfig() {
    const payload = normalizeApiConfigInput(apiDraft);
    if (!payload.name || !payload.base_url || !payload.model) {
      return;
    }

    startTransition(async () => {
      const config = await createApiConfig(payload);
      setLibrary((current) => ({
        ...current,
        api_configs: [
          config,
          ...current.api_configs.map((item) =>
            config.is_default && item.kind === config.kind
              ? { ...item, is_default: false }
              : item,
          ),
        ].sort(sortApiConfigs),
      }));
      setSelectedConfigId(config.id);
      setApiDraft(templateToApiConfigInput(templates[0]));
      onApiConfigCreated?.();
    });
  }

  function handleUpdateApiConfig() {
    if (!selectedConfig || !selectedConfigDraft) {
      return;
    }

    const payload = normalizeApiConfigInput(selectedConfigDraft);
    if (!payload.name || !payload.base_url || !payload.model) {
      return;
    }

    startTransition(async () => {
      const updated = await updateApiConfig(selectedConfig.id, payload);
      refreshApiConfig(updated);
      setApiEditDraft(null);
    });
  }

  function handleSetDefaultApiConfig(config: ApiConfig) {
    startTransition(async () => {
      const updated = await setDefaultApiConfig(config.id);
      refreshApiConfig(updated);
    });
  }

  async function handleCheckApiConfig(config: ApiConfig) {
    setCheckingApiConfigId(config.id);
    try {
      const result = await checkApiConfigHealth(config.id);
      setApiHealthResults((current) => ({ ...current, [config.id]: result }));
    } catch (error) {
      void notice(error instanceof Error ? error.message : "API 配置测试失败", {
        title: "API 配置测试失败",
      });
    } finally {
      setCheckingApiConfigId(null);
    }
  }

  async function handleDeleteApiConfig(config: ApiConfig) {
    if (
      !(await confirm(`删除 API 配置「${config.name}」？`, {
        confirmLabel: "删除",
        tone: "danger",
      }))
    ) {
      return;
    }

    startTransition(async () => {
      await deleteApiConfig(config.id);
      const nextConfig = library.api_configs.find((item) => item.id !== config.id);
      setLibrary((current) => ({
        ...current,
        api_configs: current.api_configs.filter((item) => item.id !== config.id),
      }));
      setApiHealthResults((current) => {
        const next = { ...current };
        delete next[config.id];
        return next;
      });
      setSelectedConfigId(nextConfig?.id ?? "");
      setApiEditDraft(null);
    });
  }

  return {
    handleCheckApiConfig,
    handleCreateApiConfig,
    handleDeleteApiConfig,
    handleSetDefaultApiConfig,
    handleUpdateApiConfig,
  };
}
