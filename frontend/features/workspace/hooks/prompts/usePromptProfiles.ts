"use client";

import type { Dispatch, SetStateAction } from "react";
import { useState } from "react";
import {
  updatePromptProfile,
  type PromptProfile,
  type PromptRequestType,
  type WorkspaceSnapshot,
} from "@/lib/api/index";
import { promptProfileConfigKeys } from "../../constants";
import { normalizePromptTemperature, toPromptDraft } from "../../promptProfileConfig";
import type { PresetSaveState, PromptProfileDraft } from "../../types";
import { toggleId } from "../../utils";
import type { PromptProfilesApi } from "../workspaceInteractionApiTypes";
import { buildPromptProfileOverride, profileForRequestType } from "./promptProfileDraft";
import { usePromptProfileVersions } from "./usePromptProfileVersions";

export type { PromptProfilesApi } from "../workspaceInteractionApiTypes";

export function usePromptProfiles({
  projectId,
  promptProfiles,
  setWorkspace,
}: {
  projectId: string;
  promptProfiles: PromptProfile[];
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>;
}) {
  const [isPromptManagerOpen, setIsPromptManagerOpen] = useState(false);
  const [activePromptRequestType, setActivePromptRequestType] =
    useState<PromptRequestType>("perspective_suggestion");
  const [promptDraft, setPromptDraft] = useState<PromptProfileDraft | null>(null);
  const [promptSaveState, setPromptSaveState] = useState<PresetSaveState>("idle");
  const [quickGenerationProfileSaveState, setQuickGenerationProfileSaveState] =
    useState<PresetSaveState>("idle");
  const versions = usePromptProfileVersions({
    projectId,
    promptProfiles,
    setActivePromptRequestType,
    setIsPromptManagerOpen,
    setPromptDraft,
    setPromptSaveState,
    setWorkspace,
  });

  function openPromptManager(requestType: PromptRequestType = activePromptRequestType) {
    const profile = profileForRequestType(promptProfiles, requestType) ?? promptProfiles[0];
    if (!profile) {
      return;
    }
    setActivePromptRequestType(profile.request_type);
    setPromptDraft(toPromptDraft(profile));
    setPromptSaveState("idle");
    setIsPromptManagerOpen(true);
  }

  function handleSelectPromptRequestType(requestType: PromptRequestType) {
    const profile = profileForRequestType(promptProfiles, requestType);
    setActivePromptRequestType(requestType);
    if (profile) {
      setPromptDraft(toPromptDraft(profile));
    }
    setPromptSaveState("idle");
  }

  function patchPromptDraft(patch: Partial<PromptProfileDraft>) {
    setPromptDraft((current) => (current ? { ...current, ...patch } : current));
  }

  function togglePromptChapter(chapterId: string) {
    setPromptDraft((current) =>
      current ? { ...current, chapter_ids: toggleId(current.chapter_ids, chapterId) } : current,
    );
  }

  function togglePromptDocument(documentId: string) {
    setPromptDraft((current) =>
      current ? { ...current, document_ids: toggleId(current.document_ids, documentId) } : current,
    );
  }

  async function handleSavePromptProfile() {
    if (!promptDraft) {
      return;
    }
    const profilePayload = buildPromptProfileOverride(promptDraft);
    if (!profilePayload) {
      setPromptSaveState("error");
      return;
    }

    setPromptSaveState("saving");
    try {
      const updated = await updatePromptProfile(projectId, promptDraft.request_type, {
        chapter_ids: profilePayload.chapter_ids,
        config: profilePayload.config,
        document_ids: profilePayload.document_ids,
        name: profilePayload.name,
        output_contract: profilePayload.output_contract,
        system_template: profilePayload.system_template,
        user_template: profilePayload.user_template,
      });
      setWorkspace((current) => ({
        ...current,
        prompt_profiles: {
          profiles: current.prompt_profiles.profiles.map((profile) =>
            profile.request_type === updated.request_type ? updated : profile,
          ),
        },
      }));
      setPromptDraft(toPromptDraft(updated));
      setPromptSaveState("saved");
      if (versions.isPromptVersionDialogOpen) {
        void versions.loadPromptVersions(updated.request_type);
      }
    } catch {
      setPromptSaveState("error");
    }
  }

  async function saveQuickGenerationProfile({
    apiConfigId,
    includeChapterSynopsis,
    systemTemplate,
    temperature,
    userTemplate,
  }: {
    apiConfigId?: string;
    includeChapterSynopsis?: boolean;
    systemTemplate?: string;
    temperature?: string;
    userTemplate?: string;
  }) {
    const profile = profileForRequestType(promptProfiles, "quick_generate_next_paragraph");
    if (!profile) {
      setQuickGenerationProfileSaveState("error");
      return;
    }

    const config = { ...profile.config };
    if (apiConfigId !== undefined) {
      if (apiConfigId) {
        config[promptProfileConfigKeys.apiConfigId] = apiConfigId;
      } else {
        delete config[promptProfileConfigKeys.apiConfigId];
      }
    }
    if (temperature !== undefined) {
      const normalizedTemperature = normalizePromptTemperature(temperature);
      if (normalizedTemperature === null) {
        delete config[promptProfileConfigKeys.temperature];
      } else {
        config[promptProfileConfigKeys.temperature] = normalizedTemperature;
      }
    }
    if (includeChapterSynopsis !== undefined) {
      config[promptProfileConfigKeys.includeChapterSynopsis] = includeChapterSynopsis;
    }

    setQuickGenerationProfileSaveState("saving");
    try {
      const updated = await updatePromptProfile(projectId, "quick_generate_next_paragraph", {
        config,
        system_template: systemTemplate,
        user_template: userTemplate,
      });
      setWorkspace((current) => ({
        ...current,
        prompt_profiles: {
          profiles: current.prompt_profiles.profiles.map((item) =>
            item.request_type === updated.request_type ? updated : item,
          ),
        },
      }));
      setPromptDraft((current) =>
        current?.request_type === updated.request_type ? toPromptDraft(updated) : current,
      );
      setQuickGenerationProfileSaveState("saved");
      if (versions.isPromptVersionDialogOpen) {
        void versions.loadPromptVersions(updated.request_type);
      }
    } catch {
      setQuickGenerationProfileSaveState("error");
    }
  }

  return {
    activePromptRequestType,
    buildPromptProfileOverride,
    handleOpenPromptVersions: () => versions.handleOpenPromptVersions(promptDraft),
    handleRestorePromptProfileVersion: versions.handleRestorePromptProfileVersion,
    handleSavePromptProfile,
    handleSelectPromptRequestType,
    handleSelectPromptVersion: versions.handleSelectPromptVersion,
    isPromptManagerOpen,
    isPromptVersionDialogOpen: versions.isPromptVersionDialogOpen,
    isPromptVersionLoading: versions.isPromptVersionLoading,
    openPromptManager,
    openPromptVersions: versions.openPromptVersions,
    patchPromptDraft,
    promptDraft,
    quickGenerationProfileSaveState,
    promptSaveState,
    promptVersions: versions.promptVersions,
    selectedPromptVersion: versions.selectedPromptVersion,
    setIsPromptManagerOpen,
    setIsPromptVersionDialogOpen: versions.setIsPromptVersionDialogOpen,
    setPromptSaveState,
    saveQuickGenerationProfile,
    togglePromptChapter,
    togglePromptDocument,
  } satisfies PromptProfilesApi;
}
