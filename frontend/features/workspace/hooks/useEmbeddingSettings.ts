"use client";

import { useEffect, useMemo, useState } from "react";
import type {
  ApiConfig,
  EmbeddingDistanceAlgorithm,
  EmbeddingProjectSettings,
  EmbeddingSegmentationMode,
} from "@/lib/api/index";
import { getEmbeddingSettings, updateEmbeddingSettings } from "@/lib/api/index";

export type EmbeddingAppliedSettings = {
  algorithm: EmbeddingDistanceAlgorithm;
  segmentSize: number;
  segmentationMode: EmbeddingSegmentationMode;
  selectedApiConfigId: string;
};

type UseEmbeddingSettingsOptions = {
  embeddingConfigs: ApiConfig[];
  isOpen: boolean;
  projectId: string;
};

const fallbackSettings: EmbeddingAppliedSettings = {
  algorithm: "cosine",
  segmentSize: 1,
  segmentationMode: "word",
  selectedApiConfigId: "",
};

export function useEmbeddingSettings({
  embeddingConfigs,
  isOpen,
  projectId,
}: UseEmbeddingSettingsOptions) {
  const [savedSettings, setSavedSettings] = useState<EmbeddingAppliedSettings>(fallbackSettings);
  const [draftSettings, setDraftSettings] = useState<EmbeddingAppliedSettings>(fallbackSettings);
  const [isLoadingSettings, setIsLoadingSettings] = useState(false);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [settingsError, setSettingsError] = useState<string | null>(null);

  const defaultApiConfigId = useMemo(
    () => (embeddingConfigs.find((config) => config.is_default) ?? embeddingConfigs[0])?.id ?? "",
    [embeddingConfigs],
  );

  useEffect(() => {
    let cancelled = false;
    setIsLoadingSettings(true);
    setSettingsError(null);

    void getEmbeddingSettings(projectId)
      .then((settings) => {
        if (cancelled) return;
        const resolved = resolveSettings(settings, embeddingConfigs, defaultApiConfigId);
        setSavedSettings(resolved);
        setDraftSettings(resolved);
      })
      .catch((error: unknown) => {
        if (!cancelled) setSettingsError(messageFromError(error));
      })
      .finally(() => {
        if (!cancelled) setIsLoadingSettings(false);
      });

    return () => {
      cancelled = true;
    };
  }, [defaultApiConfigId, embeddingConfigs, projectId]);

  useEffect(() => {
    if (!isOpen) setDraftSettings(savedSettings);
  }, [isOpen, savedSettings]);

  async function saveSettings() {
    setIsSavingSettings(true);
    setSettingsError(null);
    try {
      const response = await updateEmbeddingSettings(projectId, {
        api_config_id: draftSettings.selectedApiConfigId || null,
        algorithm: draftSettings.algorithm,
        segmentation_mode: draftSettings.segmentationMode,
        segment_size: draftSettings.segmentSize,
      });
      const resolved = resolveSettings(response, embeddingConfigs, defaultApiConfigId);
      setSavedSettings(resolved);
      setDraftSettings(resolved);
      return resolved;
    } catch (error) {
      setSettingsError(messageFromError(error));
      return null;
    } finally {
      setIsSavingSettings(false);
    }
  }

  return {
    draftSettings,
    hasUnsavedSettings: !sameSettings(savedSettings, draftSettings),
    isLoadingSettings,
    isSavingSettings,
    savedSettings,
    saveSettings,
    setDraftSettings,
    settingsError,
  };
}

function resolveSettings(
  settings: EmbeddingProjectSettings,
  embeddingConfigs: ApiConfig[],
  defaultApiConfigId: string,
): EmbeddingAppliedSettings {
  const configId = embeddingConfigs.some((config) => config.id === settings.api_config_id)
    ? settings.api_config_id
    : defaultApiConfigId;
  return {
    algorithm: settings.algorithm,
    segmentSize: clampSegmentSize(settings.segment_size),
    segmentationMode: settings.segmentation_mode,
    selectedApiConfigId: configId ?? "",
  };
}

function sameSettings(left: EmbeddingAppliedSettings, right: EmbeddingAppliedSettings) {
  return (
    left.algorithm === right.algorithm &&
    left.segmentSize === right.segmentSize &&
    left.segmentationMode === right.segmentationMode &&
    left.selectedApiConfigId === right.selectedApiConfigId
  );
}

function clampSegmentSize(value: number) {
  return Math.min(12, Math.max(1, Math.trunc(value)));
}

function messageFromError(error: unknown) {
  return error instanceof Error ? error.message : "Embedding 设置保存失败";
}
