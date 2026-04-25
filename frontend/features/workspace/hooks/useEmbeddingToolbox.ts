"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ClusterResponse, EmbeddingTag } from "@/lib/api/index";
import type { EmbeddingTagInput, EmbeddingTagUpdate, HeatmapResponse } from "@/lib/api/index";
import { buildEmbeddingClusters, buildEmbeddingHeatmap, createEmbeddingTag, deleteEmbeddingTag, getEmbeddingTags, updateEmbeddingTag } from "@/lib/api/index";
import { useConfirm } from "@/components/dialog";
import { confirmEmbeddingTagDelete } from "../workspaceDialogHelpers";
import { analysisRange, messageFromError, reconcileSelectedTags, validateEmbeddingAnalysis } from "./embeddingToolboxUtils";
import type { EmbeddingRangeMode, EmbeddingToolboxOptions, EmbeddingToolboxTab } from "./embeddingToolboxTypes";
import { useEmbeddingSettings, type EmbeddingAppliedSettings } from "./useEmbeddingSettings";
import type { EmbeddingToolboxApi } from "./workspaceToolApiTypes";

export type { EmbeddingToolboxApi } from "./workspaceToolApiTypes";
export type { EmbeddingRangeMode, EmbeddingToolboxTab } from "./embeddingToolboxTypes";

export function useEmbeddingToolbox({
  activeSelection,
  apiConfigs,
  content,
  projectId,
  resource,
}: EmbeddingToolboxOptions) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<EmbeddingToolboxTab>("heatmap");
  const [tags, setTags] = useState<EmbeddingTag[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [rangeMode, setRangeMode] = useState<EmbeddingRangeMode>("full");
  const [heatmap, setHeatmap] = useState<HeatmapResponse | null>(null);
  const [clusters, setClusters] = useState<ClusterResponse | null>(null);
  const [activeHeatmapTagId, setActiveHeatmapTagId] = useState<string | null>(null);
  const [isHeatmapVisible, setIsHeatmapVisible] = useState(false);
  const [activeClusterTagId, setActiveClusterTagId] = useState<string | null>(null);
  const [isClusterMapOpen, setIsClusterMapOpen] = useState(false);
  const [isLoadingTags, setIsLoadingTags] = useState(false);
  const [isSavingTag, setIsSavingTag] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const confirm = useConfirm();

  const embeddingConfigs = useMemo(
    () => apiConfigs.filter((config) => config.kind === "embedding"),
    [apiConfigs],
  );
  const settings = useEmbeddingSettings({ embeddingConfigs, isOpen, projectId });

  const reloadTags = useCallback(async () => {
    setIsLoadingTags(true);
    setError(null);
    try {
      const nextTags = await getEmbeddingTags(projectId);
      setTags(nextTags);
      setSelectedTagIds((current) => reconcileSelectedTags(current, nextTags));
    } catch (err) {
      setError(messageFromError(err));
    } finally {
      setIsLoadingTags(false);
    }
  }, [projectId]);

  useEffect(() => {
    void reloadTags();
  }, [reloadTags]);

  useEffect(() => {
    setHeatmap(null);
    setClusters(null);
    setActiveHeatmapTagId(null);
    setIsHeatmapVisible(false);
    setActiveClusterTagId(null);
    setIsClusterMapOpen(false);
  }, [content, resource.id, resource.type]);

  async function saveNewTag(input: EmbeddingTagInput) {
    await saveTagAction(async () => {
      const tag = await createEmbeddingTag(projectId, input);
      setTags((current) => [...current, tag]);
      if (tag.is_enabled) setSelectedTagIds((current) => [...new Set([...current, tag.id])]);
      setNotice("标签已创建");
    });
  }

  async function saveTag(tagId: string, input: EmbeddingTagUpdate) {
    await saveTagAction(async () => {
      const tag = await updateEmbeddingTag(projectId, tagId, input);
      setTags((current) => current.map((item) => (item.id === tag.id ? tag : item)));
      setNotice("标签已保存");
    });
  }

  async function removeTag(tag: EmbeddingTag) {
    if (!(await confirmEmbeddingTagDelete(confirm, tag))) {
      return;
    }
    await saveTagAction(async () => {
      await deleteEmbeddingTag(projectId, tag.id);
      setTags((current) => current.filter((item) => item.id !== tag.id));
      setSelectedTagIds((current) => current.filter((id) => id !== tag.id));
      setNotice("标签已删除");
    });
  }

  async function saveTagAction(action: () => Promise<void>) {
    setIsSavingTag(true);
    setError(null);
    setNotice(null);
    try {
      await action();
    } catch (err) {
      setError(messageFromError(err));
    } finally {
      setIsSavingTag(false);
    }
  }

  function toggleSelectedTag(tagId: string) {
    setSelectedTagIds((current) =>
      current.includes(tagId) ? current.filter((id) => id !== tagId) : [...current, tagId],
    );
  }

  async function analyzeHeatmap(
    appliedSettings: EmbeddingAppliedSettings = settings.savedSettings,
    forceReembed = false,
  ) {
    const validationError = validateEmbeddingAnalysis(
      appliedSettings.selectedApiConfigId,
      selectedTagIds,
      rangeMode,
      activeSelection,
    );
    if (validationError) return setError(validationError);

    setIsAnalyzing(true);
    setError(null);
    setNotice(null);
    try {
      const response = await buildEmbeddingHeatmap(projectId, {
        resource_type: resource.type,
        resource_id: resource.id,
        api_config_id: appliedSettings.selectedApiConfigId,
        segmentation_mode: appliedSettings.segmentationMode,
        segment_size: appliedSettings.segmentSize,
        algorithm: appliedSettings.algorithm,
        tag_ids: selectedTagIds,
        range: analysisRange(rangeMode, activeSelection),
        force_reembed: forceReembed,
      });
      setHeatmap(response);
      setActiveHeatmapTagId(selectedTagIds.length === 1 ? selectedTagIds[0] : null);
      setIsHeatmapVisible(true);
      setNotice(`分析完成：${response.items.length} 个片段`);
    } catch (err) {
      setError(messageFromError(err));
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function analyzeClusters(
    appliedSettings: EmbeddingAppliedSettings = settings.savedSettings,
    forceReembed = false,
  ) {
    const validationError = validateEmbeddingAnalysis(
      appliedSettings.selectedApiConfigId,
      selectedTagIds,
      rangeMode,
      activeSelection,
    );
    if (validationError) return setError(validationError);

    setIsAnalyzing(true);
    setError(null);
    setNotice(null);
    try {
      const response = await buildEmbeddingClusters(projectId, {
        resource_type: resource.type,
        resource_id: resource.id,
        api_config_id: appliedSettings.selectedApiConfigId,
        segmentation_mode: appliedSettings.segmentationMode,
        segment_size: appliedSettings.segmentSize,
        algorithm: appliedSettings.algorithm,
        cluster_mode: "fixed_tag_centers",
        tag_ids: selectedTagIds,
        range: analysisRange(rangeMode, activeSelection),
        force_reembed: forceReembed,
      });
      setClusters(response);
      setActiveClusterTagId(null);
      setNotice(`语言簇完成：${response.points.length} 个点`);
    } catch (err) {
      setError(messageFromError(err));
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function saveSettingsAndReembed() {
    const nextSettings = await settings.saveSettings();
    if (!nextSettings) return;
    if (!heatmap && !clusters) {
      setNotice("Embedding 设置已保存；下次分析会重新生成向量");
      return;
    }
    if (heatmap) await analyzeHeatmap(nextSettings, true);
    if (clusters) await analyzeClusters(nextSettings, true);
  }

  return {
    activeClusterTagId,
    activeHeatmapTagId,
    activeTab,
    analyzeClusters,
    analyzeHeatmap,
    clusters,
    draftSettings: settings.draftSettings,
    embeddingConfigs,
    error: error ?? settings.settingsError,
    hasUnsavedSettings: settings.hasUnsavedSettings,
    heatmap,
    isAnalyzing,
    isClusterMapOpen,
    isHeatmapVisible,
    isLoadingSettings: settings.isLoadingSettings,
    isLoadingTags,
    isOpen,
    isSavingSettings: settings.isSavingSettings,
    isSavingTag,
    notice,
    rangeMode,
    reloadTags,
    removeTag,
    saveNewTag,
    saveTag,
    saveSettingsAndReembed,
    selectedTagIds,
    setActiveHeatmapTagId,
    setActiveClusterTagId,
    setActiveTab,
    setDraftSettings: settings.setDraftSettings,
    setIsClusterMapOpen,
    setIsHeatmapVisible,
    setIsOpen,
    setRangeMode,
    tags,
    toggleSelectedTag,
  } satisfies EmbeddingToolboxApi;
}
