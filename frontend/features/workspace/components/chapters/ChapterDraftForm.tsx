"use client";

import { TreeRenameInput } from "@/features/workspace/components/tree/TreeRenameInput";
import type { ChapterDraftState } from "../../types";

export function ChapterDraftForm({
  draft,
  isSaving,
  onCancel,
  onChange,
  onSubmit,
}: {
  draft: ChapterDraftState | null;
  isSaving: boolean;
  onCancel: () => void;
  onChange: (title: string) => void;
  onSubmit: () => void;
}) {
  if (!draft) {
    return null;
  }

  const label =
    draft.mode === "rename"
      ? "重命名章节"
      : draft.type === "folder"
        ? "新建章节目录"
        : "新建章节";

  return (
    <TreeRenameInput
      disabled={isSaving}
      label={label}
      onCancel={onCancel}
      onChange={onChange}
      onSubmit={onSubmit}
      title={draft.title}
    />
  );
}
