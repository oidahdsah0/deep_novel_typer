"use client";

import type { Dispatch, SetStateAction } from "react";
import { useState } from "react";
import {
  createResourceVersion,
  getResourceVersion,
  getWorkspaceSnapshot,
  listResourceVersions,
  restoreResourceVersion,
  type ResourceVersion,
  type ResourceVersionDetail,
  type RestoreResourceVersionResponse,
  type WorkspaceSnapshot,
} from "@/lib/api/index";
import { useConfirm } from "@/components/dialog";
import type { ResourceContentSnapshot } from "../resourceControllerState";
import type { WorkspaceResourceControllerApi } from "./useWorkspaceResourceController";

type VersionDraft = { label: string; note: string };

export type VersionHistoryApi = {
  handleCreateManualVersion: () => Promise<void>;
  handleOpenVersionDialog: () => Promise<void>;
  handleRestoreVersion: (version: ResourceVersionDetail) => Promise<void>;
  handleSelectVersion: (version: ResourceVersion) => Promise<void>;
  isVersionDialogOpen: boolean;
  isVersionLoading: boolean;
  resourceVersions: ResourceVersion[];
  selectedVersion: ResourceVersionDetail | null;
  setIsVersionDialogOpen: Dispatch<SetStateAction<boolean>>;
  setVersionDraft: Dispatch<SetStateAction<VersionDraft>>;
  versionDraft: VersionDraft;
};

export function useVersionHistory({
  projectId,
  resourceController,
  workspace,
}: {
  projectId: string;
  resourceController: WorkspaceResourceControllerApi;
  workspace: WorkspaceSnapshot;
}) {
  const { openResource, openWorkspaceChapter, requestSave, resource } = resourceController;
  const [isVersionDialogOpen, setIsVersionDialogOpen] = useState(false);
  const [resourceVersions, setResourceVersions] = useState<ResourceVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<ResourceVersionDetail | null>(null);
  const [isVersionLoading, setIsVersionLoading] = useState(false);
  const [versionDraft, setVersionDraft] = useState({ label: "", note: "" });
  const confirm = useConfirm();

  async function loadResourceVersions(selectVersionId?: string) {
    setIsVersionLoading(true);
    try {
      const versions = await listResourceVersions(projectId, resource.type, resource.id);
      setResourceVersions(versions);
      const target = selectVersionId
        ? versions.find((version) => version.id === selectVersionId)
        : versions[0];
      if (target) {
        const detail = await getResourceVersion(projectId, target.id);
        setSelectedVersion(detail);
      } else {
        setSelectedVersion(null);
      }
    } finally {
      setIsVersionLoading(false);
    }
  }

  async function handleOpenVersionDialog() {
    await requestSave();
    setIsVersionDialogOpen(true);
    setVersionDraft({ label: "", note: "" });
    await loadResourceVersions();
  }

  async function handleCreateManualVersion() {
    await requestSave();
    setIsVersionLoading(true);
    try {
      const version = await createResourceVersion(projectId, {
        resource_type: resource.type,
        resource_id: resource.id,
        version_type: "manual",
        label: versionDraft.label.trim() || null,
        note: versionDraft.note.trim(),
      });
      setVersionDraft({ label: "", note: "" });
      await loadResourceVersions(version.id);
    } finally {
      setIsVersionLoading(false);
    }
  }

  async function handleSelectVersion(version: ResourceVersion) {
    setIsVersionLoading(true);
    try {
      setSelectedVersion(await getResourceVersion(projectId, version.id));
    } finally {
      setIsVersionLoading(false);
    }
  }

  async function handleRestoreVersion(version: ResourceVersionDetail) {
    if (
      !(await confirm(`恢复到「${version.label || version.created_at}」这个版本？当前内容会先自动备份。`, {
        confirmLabel: "恢复",
        tone: "danger",
      }))
    ) {
      return;
    }

    setIsVersionLoading(true);
    try {
      const restored = await restoreResourceVersion(projectId, version.id);
      const nextWorkspace = await getWorkspaceSnapshot(
        projectId,
        restored.resource_type === "chapter" ? restored.resource_id : workspace.active_chapter.id,
      );
      if (restored.resource_type === "chapter") {
        openWorkspaceChapter(nextWorkspace);
      } else {
        openResource(restoredDocumentSnapshot(restored), nextWorkspace);
      }
      await loadResourceVersions();
    } finally {
      setIsVersionLoading(false);
    }
  }

  return {
    handleCreateManualVersion,
    handleOpenVersionDialog,
    handleRestoreVersion,
    handleSelectVersion,
    isVersionDialogOpen,
    isVersionLoading,
    resourceVersions,
    selectedVersion,
    setIsVersionDialogOpen,
    setVersionDraft,
    versionDraft,
  } satisfies VersionHistoryApi;
}

function restoredDocumentSnapshot(
  restored: RestoreResourceVersionResponse,
): ResourceContentSnapshot {
  return {
    content: restored.content,
    resource: {
      type: "document",
      id: restored.resource_id,
      title: restored.title,
    },
  };
}
