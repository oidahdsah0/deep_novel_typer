import type { DialogConfirm, DialogPrompt } from "@/components/dialog";
import type {
  ChapterNode,
  EmbeddingTag,
  GenerationPreset,
  GenerationPresetKind,
} from "@/lib/api/index";
import { defaultGenerationPresetNames } from "./presetUtils";
import { summarizeChapterDelete } from "./treeUtils";

export function confirmChapterNodeDelete(confirm: DialogConfirm, node: ChapterNode) {
  const impact = summarizeChapterDelete(node);
  const message =
    node.type === "folder"
      ? `删除章节目录「${node.title}」？\n\n将删除 ${impact.folders} 个目录、${impact.chapters} 个章节，正文文件会移入本地 trash。`
      : `删除章节「${node.title}」？\n\n正文文件会移入本地 trash。`;
  return confirm(message, { confirmLabel: "删除", tone: "danger" });
}

export function confirmEmbeddingTagDelete(confirm: DialogConfirm, tag: EmbeddingTag) {
  return confirm(`删除语义标签「${tag.name}」？`, {
    confirmLabel: "删除",
    tone: "danger",
  });
}

export function confirmGenerationPresetDelete(confirm: DialogConfirm, preset: GenerationPreset) {
  return confirm(`删除预设「${preset.name}」？`, {
    confirmLabel: "删除",
    tone: "danger",
  });
}

export async function promptCreateGenerationPreset(
  prompt: DialogPrompt,
  kind: GenerationPresetKind,
) {
  const defaultName = defaultGenerationPresetNames[kind];
  return (
    await prompt("预设名称", defaultName, {
      title: "新建预设",
      confirmLabel: "新建",
    })
  )?.trim();
}

export async function promptRenameGenerationPreset(
  prompt: DialogPrompt,
  preset: GenerationPreset,
) {
  return (
    await prompt("新的预设名称", preset.name, {
      title: "重命名预设",
      confirmLabel: "保存",
    })
  )?.trim();
}
