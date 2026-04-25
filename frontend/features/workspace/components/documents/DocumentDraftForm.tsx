"use client";

import { TreeRenameInput } from "@/features/workspace/components/tree/TreeRenameInput";
import type { DocumentDraftState } from "../../types";

export function DocumentDraftForm({
  draft,
  isSaving,
  onCancel,
  onChange,
  onSubmit,
}: {
  draft: DocumentDraftState | null;
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
      ? "重命名资料"
      : draft.type === "folder"
        ? "新建资料目录"
        : "新建 Markdown 文本";

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
