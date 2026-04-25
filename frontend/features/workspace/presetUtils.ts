import type { Dispatch, SetStateAction } from "react";
import type {
  GenerationPreset,
  GenerationPresetKind,
  WorkspaceSnapshot,
} from "@/lib/api/index";
import { presetListKeys } from "./constants";

export const defaultGenerationPresetNames: Record<GenerationPresetKind, string> = {
  writing_mode: "新的写作方式",
  quick_generation_mode: "新的快速生成方式",
  chapter_blueprint_mode: "新的章节铺设方式",
  author_persona: "新的作者人格",
  polish_mode: "新的润色方式",
  document_polish_mode: "新的资料润色方式",
  document_generation_mode: "新的资料生成方式",
  editor_persona: "新的资料编辑人格",
};

export function presetSaveKey(kind: GenerationPresetKind, presetId: string) {
  return `${kind}:${presetId}`;
}

export function updateGenerationPresetInWorkspace(
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>,
  preset: GenerationPreset,
) {
  const listKey = presetListKeys[preset.kind];
  setWorkspace((current) => {
    const currentList = current.generation_presets[listKey];
    const nextList = currentList.some((item) => item.id === preset.id)
      ? currentList.map((item) => (item.id === preset.id ? preset : item))
      : [...currentList, preset];
    return {
      ...current,
      generation_presets: {
        ...current.generation_presets,
        [listKey]: nextList,
      },
    };
  });
}

export function patchGenerationPresetInWorkspace(
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>,
  kind: GenerationPresetKind,
  presetId: string,
  patch: Partial<Pick<GenerationPreset, "name" | "content">>,
) {
  const listKey = presetListKeys[kind];
  setWorkspace((current) => ({
    ...current,
    generation_presets: {
      ...current.generation_presets,
      [listKey]: current.generation_presets[listKey].map((preset) =>
        preset.id === presetId ? { ...preset, ...patch } : preset,
      ),
    },
  }));
}

export function removeGenerationPresetFromWorkspace(
  setWorkspace: Dispatch<SetStateAction<WorkspaceSnapshot>>,
  kind: GenerationPresetKind,
  presetId: string,
) {
  const listKey = presetListKeys[kind];
  setWorkspace((current) => ({
    ...current,
    generation_presets: {
      ...current.generation_presets,
      [listKey]: current.generation_presets[listKey].filter((preset) => preset.id !== presetId),
    },
  }));
}
