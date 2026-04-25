"use client";

import type { DocumentNode } from "@/lib/api/index";
import { TreeView } from "@/features/workspace/components/tree/TreeView";
import type { TreeMoveTarget } from "@/features/workspace/components/tree/treeTypes";

type DocumentCreateType = "folder" | "markdown";

export function DocumentTree({
  activeDocumentId,
  expandedIds,
  nodes,
  onCreateNode,
  onDeleteNode,
  onMoveNode,
  onOpenDocument,
  onRenameNode,
}: {
  activeDocumentId: string | null;
  expandedIds: Set<string>;
  nodes: DocumentNode[];
  onCreateNode: (type: DocumentCreateType, parentId?: string | null) => void;
  onDeleteNode: (document: DocumentNode) => void;
  onMoveNode: (nodeId: string, target: TreeMoveTarget) => void;
  onOpenDocument: (document: DocumentNode) => void;
  onRenameNode: (document: DocumentNode) => void;
}) {
  return (
    <TreeView<DocumentNode, DocumentCreateType>
      ariaLabel="资料树"
      beforeDropLabel={(node) => `移动到 ${node.title} 前`}
      childrenEndDropLabel={(node) => `移动到 ${node.title} 目录末尾`}
      createFolderAction={{
        ariaLabel: (title) => `在 ${title} 下新建目录`,
        type: "folder",
      }}
      createLeafAction={{
        ariaLabel: (title) => `在 ${title} 下新建文本`,
        type: "markdown",
      }}
      emptyLabel="暂无资料"
      expandedIds={expandedIds}
      isNodeActive={(node) => activeDocumentId === node.id}
      nodes={nodes}
      onCreateNode={onCreateNode}
      onDeleteNode={onDeleteNode}
      onMoveNode={onMoveNode}
      onOpenNode={onOpenDocument}
      onRenameNode={onRenameNode}
      rootEndDropLabel="移动到资料根目录末尾"
    />
  );
}
