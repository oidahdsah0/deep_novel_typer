"use client";

import type { Dispatch, SetStateAction } from "react";
import { useEffect, useRef, useState, useTransition } from "react";
import {
  createGenerationPreset,
  deleteGenerationPreset,
  updateGenerationPreset,
  type GenerationPreset,
  type GenerationPresetKind,
  type GenerationPresetUpdate,
  type WorkspaceSnapshot,
} from "@/lib/api/index";
import { presetListKeys } from "../constants";
import {
  patchGenerationPresetInWorkspace,
  presetSaveKey,
  removeGenerationPresetFromWorkspace,
  updateGenerationPresetInWorkspace,
} from "../presetUtils";
import type { PresetSaveState } from "../types";
import {
  confirmGenerationPresetDelete,
  promptCreateGenerationPreset,
  promptRenameGenerationPreset,
} from "../workspaceDialogHelpers";
import { useConfirm, usePrompt } from "@/components/dialog";
import { useGenerationPresetSelection } from "./useGenerationPresetSelection";
import type { GenerationPresetsApi } from "./workspaceToolApiTypes";

export type { GenerationPresetsApi } from "./workspaceToolApiTypes";

export function useGenerationPresets({
  generationPresets,
  projectId,
  setWorkspace,
}: {
  generationPresets: WorkspaceSnapshot["generation_presets"];
  projectId: string;
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>;
}) {
  const writingPresets = generationPresets.writing_modes;
  const quickGenerationPresets = generationPresets.quick_generation_modes;
  const chapterBlueprintPresets = generationPresets.chapter_blueprint_modes;
  const authorPresets = generationPresets.author_personas;
  const polishPresets = generationPresets.polish_modes;
  const documentPolishPresets = generationPresets.document_polish_modes;
  const documentGenerationPresets = generationPresets.document_generation_modes;
  const editorPresets = generationPresets.editor_personas;

  const { selectGenerationPreset, ...presetSelection } = useGenerationPresetSelection({
    authorPresets,
    chapterBlueprintPresets,
    documentGenerationPresets,
    documentPolishPresets,
    editorPresets,
    polishPresets,
    quickGenerationPresets,
    writingPresets,
  });
  const [presetSaveState, setPresetSaveState] = useState<PresetSaveState>("idle");
  const presetSaveTimers = useRef<Record<string, number>>({});
  const presetSaveVersions = useRef<Record<string, number>>({});
  const pendingPresetPatches = useRef<Record<string, GenerationPresetUpdate>>({});
  const presetSaveStatusTimer = useRef<number | null>(null);
  const [, startTransition] = useTransition();
  const confirm = useConfirm();
  const prompt = usePrompt();

  useEffect(() => {
    const saveTimers = presetSaveTimers.current;
    return () => {
      Object.values(saveTimers).forEach((timer) => window.clearTimeout(timer));
      if (presetSaveStatusTimer.current) {
        window.clearTimeout(presetSaveStatusTimer.current);
      }
    };
  }, []);

  function settlePresetSaveState(state: Exclude<PresetSaveState, "idle" | "saving">) {
    setPresetSaveState(state);
    if (presetSaveStatusTimer.current) {
      window.clearTimeout(presetSaveStatusTimer.current);
    }
    presetSaveStatusTimer.current = window.setTimeout(() => {
      setPresetSaveState("idle");
    }, 1800);
  }

  async function flushPresetSave(
    kind: GenerationPresetKind,
    presetId: string,
    expectedVersion?: number,
  ) {
    const key = presetSaveKey(kind, presetId);
    const patch = pendingPresetPatches.current[key];
    if (!patch || !Object.keys(patch).length) {
      return;
    }

    if (presetSaveTimers.current[key]) {
      window.clearTimeout(presetSaveTimers.current[key]);
      delete presetSaveTimers.current[key];
    }
    delete pendingPresetPatches.current[key];
    setPresetSaveState("saving");
    try {
      const updated = await updateGenerationPreset(projectId, kind, presetId, patch);
      if (
        typeof expectedVersion === "undefined" ||
        presetSaveVersions.current[key] === expectedVersion
      ) {
        updateGenerationPresetInWorkspace(setWorkspace, updated);
      }
      settlePresetSaveState("saved");
    } catch {
      pendingPresetPatches.current[key] = {
        ...patch,
        ...pendingPresetPatches.current[key],
      };
      settlePresetSaveState("error");
    }
  }

  function schedulePresetSave(
    kind: GenerationPresetKind,
    presetId: string,
    patch: GenerationPresetUpdate,
  ) {
    const key = presetSaveKey(kind, presetId);
    pendingPresetPatches.current[key] = {
      ...pendingPresetPatches.current[key],
      ...patch,
    };
    presetSaveVersions.current[key] = (presetSaveVersions.current[key] ?? 0) + 1;
    const version = presetSaveVersions.current[key];
    if (presetSaveTimers.current[key]) {
      window.clearTimeout(presetSaveTimers.current[key]);
    }
    setPresetSaveState("saving");
    presetSaveTimers.current[key] = window.setTimeout(() => {
      void flushPresetSave(kind, presetId, version);
    }, 650);
  }

  function handlePresetContentChange(
    kind: GenerationPresetKind,
    preset: GenerationPreset,
    contentValue: string,
  ) {
    patchGenerationPresetInWorkspace(setWorkspace, kind, preset.id, {
      content: contentValue,
    });
    schedulePresetSave(kind, preset.id, { content: contentValue });
  }

  async function handleCreateGenerationPreset(kind: GenerationPresetKind) {
    const name = await promptCreateGenerationPreset(prompt, kind);
    if (!name) {
      return;
    }

    startTransition(async () => {
      setPresetSaveState("saving");
      try {
        const preset = await createGenerationPreset(projectId, { kind, name, content: "" });
        updateGenerationPresetInWorkspace(setWorkspace, preset);
        selectGenerationPreset(kind, preset.id);
        settlePresetSaveState("saved");
      } catch {
        settlePresetSaveState("error");
      }
    });
  }

  async function handleRenameGenerationPreset(preset: GenerationPreset) {
    const name = await promptRenameGenerationPreset(prompt, preset);
    if (!name || name === preset.name) {
      return;
    }

    patchGenerationPresetInWorkspace(setWorkspace, preset.kind, preset.id, { name });
    startTransition(async () => {
      setPresetSaveState("saving");
      try {
        const updated = await updateGenerationPreset(projectId, preset.kind, preset.id, {
          name,
        });
        updateGenerationPresetInWorkspace(setWorkspace, updated);
        settlePresetSaveState("saved");
      } catch {
        patchGenerationPresetInWorkspace(setWorkspace, preset.kind, preset.id, {
          name: preset.name,
        });
        settlePresetSaveState("error");
      }
    });
  }

  async function handleDeleteGenerationPreset(preset: GenerationPreset) {
    if (!(await confirmGenerationPresetDelete(confirm, preset))) {
      return;
    }

    const list = generationPresets[presetListKeys[preset.kind]];
    const nextPreset = list.find((item) => item.id !== preset.id);
    startTransition(async () => {
      const key = presetSaveKey(preset.kind, preset.id);
      if (presetSaveTimers.current[key]) {
        window.clearTimeout(presetSaveTimers.current[key]);
        delete presetSaveTimers.current[key];
      }
      delete pendingPresetPatches.current[key];
      setPresetSaveState("saving");
      try {
        await deleteGenerationPreset(projectId, preset.kind, preset.id);
        removeGenerationPresetFromWorkspace(setWorkspace, preset.kind, preset.id);
        selectGenerationPreset(preset.kind, nextPreset?.id ?? "");
        settlePresetSaveState("saved");
      } catch {
        settlePresetSaveState("error");
      }
    });
  }

  return {
    authorPresets,
    chapterBlueprintPresets,
    documentGenerationPresets,
    documentPolishPresets,
    editorPresets,
    flushPresetSave,
    handleCreateGenerationPreset,
    handleDeleteGenerationPreset,
    handlePresetContentChange,
    handleRenameGenerationPreset,
    pendingPresetPatches,
    polishPresets,
    presetSaveKey,
    presetSaveState,
    quickGenerationPresets,
    ...presetSelection,
    writingPresets,
  } satisfies GenerationPresetsApi;
}
