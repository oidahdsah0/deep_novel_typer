"use client";

import type { Dispatch, SetStateAction } from "react";
import { useState } from "react";
import {
  getPromptProfileVersion,
  listPromptProfileVersions,
  restorePromptProfileVersion,
  type PromptProfile,
  type PromptProfileVersion,
  type PromptProfileVersionDetail,
  type PromptRequestType,
  type WorkspaceSnapshot,
} from "@/lib/api/index";
import { useConfirm, useNotice } from "@/components/dialog";
import { toPromptDraft } from "../../promptProfileConfig";
import type { PresetSaveState, PromptProfileDraft } from "../../types";
import { promptProfileVersionTypeLabel } from "../../utils";
import { profileForRequestType } from "./promptProfileDraft";

export function usePromptProfileVersions({
  projectId,
  promptProfiles,
  setActivePromptRequestType,
  setIsPromptManagerOpen,
  setPromptDraft,
  setPromptSaveState,
  setWorkspace,
}: {
  projectId: string;
  promptProfiles: PromptProfile[];
  setActivePromptRequestType: Dispatch<SetStateAction<PromptRequestType>>;
  setIsPromptManagerOpen: Dispatch<SetStateAction<boolean>>;
  setPromptDraft: Dispatch<SetStateAction<PromptProfileDraft | null>>;
  setPromptSaveState: Dispatch<SetStateAction<PresetSaveState>>;
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>;
}) {
  const [isPromptVersionDialogOpen, setIsPromptVersionDialogOpen] = useState(false);
  const [promptVersions, setPromptVersions] = useState<PromptProfileVersion[]>([]);
  const [selectedPromptVersion, setSelectedPromptVersion] =
    useState<PromptProfileVersionDetail | null>(null);
  const [isPromptVersionLoading, setIsPromptVersionLoading] = useState(false);
  const confirm = useConfirm();
  const notice = useNotice();

  async function loadPromptVersions(
    requestType: PromptRequestType,
    selectedVersionId?: string,
  ) {
    setIsPromptVersionLoading(true);
    try {
      const versions = await listPromptProfileVersions(projectId, requestType);
      setPromptVersions(versions);
      const nextSelected =
        versions.find((version) => version.id === selectedVersionId) ?? versions[0];
      setSelectedPromptVersion(
        nextSelected
          ? await getPromptProfileVersion(projectId, requestType, nextSelected.id)
          : null,
      );
    } catch (error) {
      void notice(error instanceof Error ? error.message : "请求配置历史加载失败", {
        title: "请求配置历史加载失败",
      });
    } finally {
      setIsPromptVersionLoading(false);
    }
  }

  function handleOpenPromptVersions(promptDraft: PromptProfileDraft | null) {
    if (!promptDraft) {
      return;
    }
    setIsPromptVersionDialogOpen(true);
    void loadPromptVersions(promptDraft.request_type);
  }

  function openPromptVersions(requestType: PromptRequestType, selectedVersionId?: string) {
    const profile = profileForRequestType(promptProfiles, requestType) ?? promptProfiles[0];
    if (!profile) {
      return;
    }
    setActivePromptRequestType(profile.request_type);
    setPromptDraft(toPromptDraft(profile));
    setPromptSaveState("idle");
    setIsPromptManagerOpen(true);
    setIsPromptVersionDialogOpen(true);
    void loadPromptVersions(profile.request_type, selectedVersionId);
  }

  async function handleSelectPromptVersion(version: PromptProfileVersion) {
    setIsPromptVersionLoading(true);
    try {
      const detail = await getPromptProfileVersion(projectId, version.request_type, version.id);
      setSelectedPromptVersion(detail);
    } catch (error) {
      void notice(error instanceof Error ? error.message : "请求配置历史读取失败", {
        title: "请求配置历史读取失败",
      });
    } finally {
      setIsPromptVersionLoading(false);
    }
  }

  async function handleRestorePromptProfileVersion(version: PromptProfileVersionDetail) {
    if (
      !(await confirm(
        `确定恢复“${version.label || promptProfileVersionTypeLabel(version.version_type)}”吗？当前请求配置会先自动保存为恢复前备份。`,
        {
          confirmLabel: "恢复",
          tone: "danger",
        },
      ))
    ) {
      return;
    }
    setIsPromptVersionLoading(true);
    try {
      const restored = await restorePromptProfileVersion(
        projectId,
        version.request_type,
        version.id,
      );
      setWorkspace((current) => ({
        ...current,
        prompt_profiles: {
          profiles: current.prompt_profiles.profiles.map((profile) =>
            profile.request_type === restored.profile.request_type ? restored.profile : profile,
          ),
        },
      }));
      setActivePromptRequestType(restored.profile.request_type);
      setPromptDraft(toPromptDraft(restored.profile));
      setPromptSaveState("saved");
      await loadPromptVersions(restored.profile.request_type, restored.version.id);
    } catch (error) {
      void notice(error instanceof Error ? error.message : "请求配置历史恢复失败", {
        title: "请求配置历史恢复失败",
      });
    } finally {
      setIsPromptVersionLoading(false);
    }
  }

  return {
    handleOpenPromptVersions,
    handleRestorePromptProfileVersion,
    handleSelectPromptVersion,
    isPromptVersionDialogOpen,
    isPromptVersionLoading,
    loadPromptVersions,
    openPromptVersions,
    promptVersions,
    selectedPromptVersion,
    setIsPromptVersionDialogOpen,
  };
}
