"use client";

import type { ChapterNode } from "@/lib/api/index";
import { TreeView } from "@/features/workspace/components/tree/TreeView";
import type { TreeMoveTarget } from "@/features/workspace/components/tree/treeTypes";

type ChapterCreateType = "folder" | "chapter";

export function ChapterTree({
  activeChapterId,
  expandedIds,
  nodes,
  onCreateNode,
  onDeleteNode,
  onMoveNode,
  onOpenNode,
  onRenameNode,
}: {
  activeChapterId: string | null;
  expandedIds: Set<string>;
  nodes: ChapterNode[];
  onCreateNode: (type: ChapterCreateType, parentId?: string | null) => void;
  onDeleteNode: (node: ChapterNode) => void;
  onMoveNode: (nodeId: string, target: TreeMoveTarget) => void;
  onOpenNode: (node: ChapterNode) => void;
  onRenameNode: (node: ChapterNode) => void;
}) {
  return (
    <TreeView<ChapterNode, ChapterCreateType>
      ariaLabel="章节树"
      beforeDropLabel={(node) => `移动到 ${node.title} 前`}
      childrenEndDropLabel={(node) => `移动到 ${node.title} 目录末尾`}
      createFolderAction={{
        ariaLabel: (title) => `在 ${title} 下新建章节目录`,
        type: "folder",
      }}
      createLeafAction={{
        ariaLabel: (title) => `在 ${title} 下新建章节`,
        type: "chapter",
      }}
      emptyLabel="暂无章节"
      expandedIds={expandedIds}
      getNodeMeta={(node) => (node.type === "chapter" ? `${node.word_count} 字` : null)}
      isNodeActive={(node) => node.type === "chapter" && activeChapterId === node.chapter_id}
      nodes={nodes}
      onCreateNode={onCreateNode}
      onDeleteNode={onDeleteNode}
      onMoveNode={onMoveNode}
      onOpenNode={onOpenNode}
      onRenameNode={onRenameNode}
      rootEndDropLabel="移动到章节根目录末尾"
    />
  );
}
