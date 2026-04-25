"use client";

import type { Dispatch, SetStateAction } from "react";
import { useState, useTransition } from "react";
import {
  createPerspective,
  deletePerspective,
  updatePerspective,
  type Perspective,
  type WorkspaceSnapshot,
} from "@/lib/api/index";
import { useConfirm } from "@/components/dialog";
import type { PerspectiveDraft } from "../types";
import type { PerspectiveActionsApi } from "./workspaceInteractionApiTypes";

export type { PerspectiveActionsApi } from "./workspaceInteractionApiTypes";

const emptyPerspectiveDraft: PerspectiveDraft = {
  name: "",
  description: "",
  instructions: "",
  api_config_id: null,
};

export function usePerspectiveActions({
  projectId,
  setWorkspace,
}: {
  projectId: string;
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>;
}) {
  const [perspectiveDraft, setPerspectiveDraft] =
    useState<PerspectiveDraft>(emptyPerspectiveDraft);
  const [editingPerspectiveId, setEditingPerspectiveId] = useState<string | null>(null);
  const [perspectiveEditDraft, setPerspectiveEditDraft] =
    useState<PerspectiveDraft>(emptyPerspectiveDraft);
  const [, startTransition] = useTransition();
  const confirm = useConfirm();

  function handleCreatePerspective() {
    if (!perspectiveDraft.name.trim() || !perspectiveDraft.instructions.trim()) {
      return;
    }

    startTransition(async () => {
      const perspective = await createPerspective(projectId, perspectiveDraft);
      setWorkspace((current) => ({
        ...current,
        perspectives: [...current.perspectives, perspective],
      }));
      setPerspectiveDraft(emptyPerspectiveDraft);
    });
  }

  function handleTogglePerspective(perspective: Perspective) {
    startTransition(async () => {
      const updated = await updatePerspective(projectId, perspective.id, {
        is_enabled: !perspective.is_enabled,
      });
      setWorkspace((current) => ({
        ...current,
        perspectives: current.perspectives.map((item) =>
          item.id === updated.id ? updated : item,
        ),
      }));
    });
  }

  function handleSelectPerspectiveConfig(perspective: Perspective, apiConfigId: string | null) {
    startTransition(async () => {
      const updated = await updatePerspective(projectId, perspective.id, {
        api_config_id: apiConfigId,
      });
      setWorkspace((current) => ({
        ...current,
        perspectives: current.perspectives.map((item) =>
          item.id === updated.id ? updated : item,
        ),
      }));
    });
  }

  function handleStartEditPerspective(perspective: Perspective) {
    setEditingPerspectiveId(perspective.id);
    setPerspectiveEditDraft({
      name: perspective.name,
      description: perspective.description,
      instructions: perspective.instructions,
      api_config_id: perspective.api_config_id,
    });
  }

  function handleCancelEditPerspective() {
    setEditingPerspectiveId(null);
    setPerspectiveEditDraft(emptyPerspectiveDraft);
  }

  function handleSavePerspective() {
    if (
      !editingPerspectiveId ||
      !perspectiveEditDraft.name.trim() ||
      !perspectiveEditDraft.instructions.trim()
    ) {
      return;
    }

    const perspectiveId = editingPerspectiveId;
    const draft = perspectiveEditDraft;
    startTransition(async () => {
      const updated = await updatePerspective(projectId, perspectiveId, {
        name: draft.name.trim(),
        description: draft.description.trim(),
        instructions: draft.instructions.trim(),
        api_config_id: draft.api_config_id,
      });
      setWorkspace((current) => ({
        ...current,
        perspectives: current.perspectives.map((item) =>
          item.id === updated.id ? updated : item,
        ),
      }));
      handleCancelEditPerspective();
    });
  }

  async function handleDeletePerspective(perspective: Perspective) {
    if (
      !(await confirm(`删除 AI 视角「${perspective.name}」？`, {
        confirmLabel: "删除",
        tone: "danger",
      }))
    ) {
      return;
    }

    startTransition(async () => {
      await deletePerspective(projectId, perspective.id);
      setWorkspace((current) => ({
        ...current,
        perspectives: current.perspectives.filter((item) => item.id !== perspective.id),
      }));
      if (editingPerspectiveId === perspective.id) {
        handleCancelEditPerspective();
      }
    });
  }

  return {
    editingPerspectiveId,
    handleCancelEditPerspective,
    handleCreatePerspective,
    handleDeletePerspective,
    handleSavePerspective,
    handleSelectPerspectiveConfig,
    handleStartEditPerspective,
    handleTogglePerspective,
    perspectiveEditDraft,
    perspectiveDraft,
    setPerspectiveEditDraft,
    setPerspectiveDraft,
  } satisfies PerspectiveActionsApi;
}
