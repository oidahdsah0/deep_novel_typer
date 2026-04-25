"use client";

import { FilePlus2, FolderPlus, Pencil, Trash2 } from "lucide-react";
import type { TreeCreateAction } from "./treeTypes";

export function TreeNodeActions<TCreateType extends string>({
  createFolderAction,
  createLeafAction,
  isFolder,
  nodeId,
  nodeTitle,
  onCreateNode,
  onDelete,
  onRename,
}: {
  createFolderAction: TreeCreateAction<TCreateType>;
  createLeafAction: TreeCreateAction<TCreateType>;
  isFolder: boolean;
  nodeId: string;
  nodeTitle: string;
  onCreateNode: (type: TCreateType, parentId?: string | null) => void;
  onDelete: () => void;
  onRename: () => void;
}) {
  return (
    <div className="doc-node-actions">
      {isFolder ? (
        <>
          <button
            aria-label={createFolderAction.ariaLabel(nodeTitle)}
            className="tiny-tool"
            onClick={() => onCreateNode(createFolderAction.type, nodeId)}
            type="button"
          >
            <FolderPlus size={13} />
          </button>
          <button
            aria-label={createLeafAction.ariaLabel(nodeTitle)}
            className="tiny-tool"
            onClick={() => onCreateNode(createLeafAction.type, nodeId)}
            type="button"
          >
            <FilePlus2 size={13} />
          </button>
        </>
      ) : null}
      <button
        aria-label={`重命名 ${nodeTitle}`}
        className="tiny-tool"
        onClick={onRename}
        type="button"
      >
        <Pencil size={13} />
      </button>
      <button
        aria-label={`删除 ${nodeTitle}`}
        className="tiny-tool danger-tool"
        onClick={onDelete}
        type="button"
      >
        <Trash2 size={13} />
      </button>
    </div>
  );
}
