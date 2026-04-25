"use client";

import type { CSSProperties, DragEvent, ReactNode } from "react";
import { useState } from "react";
import { TreeDropZone } from "./TreeDropIndicator";
import { TreeNodeActions } from "./TreeNodeActions";
import { TreeNodeRow } from "./TreeNodeRow";
import type {
  TreeCreateAction,
  TreeDropIndicatorState,
  TreeMoveTarget,
  WorkspaceTreeNode,
} from "./treeTypes";

type TreeViewProps<TNode extends WorkspaceTreeNode<TNode>, TCreateType extends string> = {
  ariaLabel: string;
  beforeDropLabel: (node: TNode) => string;
  childrenEndDropLabel: (node: TNode) => string;
  createFolderAction: TreeCreateAction<TCreateType>;
  createLeafAction: TreeCreateAction<TCreateType>;
  emptyLabel: string;
  expandedIds: Set<string>;
  getNodeMeta?: (node: TNode) => string | null;
  isNodeActive: (node: TNode) => boolean;
  nodes: TNode[];
  onCreateNode: (type: TCreateType, parentId?: string | null) => void;
  onDeleteNode: (node: TNode) => void;
  onMoveNode: (nodeId: string, target: TreeMoveTarget) => void;
  onOpenNode: (node: TNode) => void;
  onRenameNode: (node: TNode) => void;
  rootEndDropLabel: string;
};

export function TreeView<TNode extends WorkspaceTreeNode<TNode>, TCreateType extends string>({
  ariaLabel,
  beforeDropLabel,
  childrenEndDropLabel,
  createFolderAction,
  createLeafAction,
  emptyLabel,
  expandedIds,
  getNodeMeta,
  isNodeActive,
  nodes,
  onCreateNode,
  onDeleteNode,
  onMoveNode,
  onOpenNode,
  onRenameNode,
  rootEndDropLabel,
}: TreeViewProps<TNode, TCreateType>) {
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [dropIndicator, setDropIndicator] = useState<TreeDropIndicatorState | null>(null);

  if (!nodes.length) {
    return <p className="empty-note">{emptyLabel}</p>;
  }

  function handleDrop(event: DragEvent<HTMLDivElement>, target: TreeMoveTarget) {
    event.preventDefault();
    if (!draggingNodeId) {
      return;
    }
    setDropIndicator(null);
    if (draggingNodeId === target.beforeNodeId || draggingNodeId === target.parentId) {
      return;
    }
    onMoveNode(draggingNodeId, target);
  }

  function renderNode(node: TNode, depth = 0): ReactNode {
    const isFolder = node.type === "folder";
    const isExpanded = expandedIds.has(node.id);
    const beforeId = `before:${node.id}`;
    const insideId = `inside:${node.id}`;
    const canDropInside = Boolean(isFolder && draggingNodeId && draggingNodeId !== node.id);

    return (
      <div className="doc-node" key={node.id}>
        <TreeDropZone
          active={dropIndicator?.id === beforeId}
          beforeNodeId={node.id}
          depth={depth}
          id={beforeId}
          label={beforeDropLabel(node)}
          onDrop={(event) =>
            handleDrop(event, { beforeNodeId: node.id, parentId: node.parent_id })
          }
          onTargetChange={setDropIndicator}
          parentId={node.parent_id}
          visible={Boolean(draggingNodeId && draggingNodeId !== node.id)}
        />
        <TreeNodeRow
          actions={
            <TreeNodeActions
              createFolderAction={createFolderAction}
              createLeafAction={createLeafAction}
              isFolder={isFolder}
              nodeId={node.id}
              nodeTitle={node.title}
              onCreateNode={onCreateNode}
              onDelete={() => onDeleteNode(node)}
              onRename={() => onRenameNode(node)}
            />
          }
          canDropInside={canDropInside}
          depth={depth}
          dragLabel={`拖动 ${node.title}`}
          dragging={draggingNodeId === node.id}
          dropInside={dropIndicator?.id === insideId}
          expanded={isExpanded}
          folder={isFolder}
          meta={getNodeMeta?.(node) ?? null}
          onDragEnd={() => {
            setDraggingNodeId(null);
            setDropIndicator(null);
          }}
          onDragStart={(event) => {
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", node.id);
            setDraggingNodeId(node.id);
          }}
          onDropInside={(event) =>
            handleDrop(event, { beforeNodeId: null, parentId: node.id })
          }
          onOpen={() => onOpenNode(node)}
          onTargetInside={() =>
            setDropIndicator({ beforeNodeId: null, id: insideId, parentId: node.id })
          }
          selected={isNodeActive(node)}
          title={node.title}
        />
        {isFolder && isExpanded && node.children.length ? (
          <div className="doc-node-children">
            {node.children.map((child) => renderNode(child, depth + 1))}
            <TreeDropZone
              active={dropIndicator?.id === `children-end:${node.id}`}
              beforeNodeId={null}
              depth={depth + 1}
              id={`children-end:${node.id}`}
              label={childrenEndDropLabel(node)}
              onDrop={(event) =>
                handleDrop(event, { beforeNodeId: null, parentId: node.id })
              }
              onTargetChange={setDropIndicator}
              parentId={node.id}
              visible={Boolean(draggingNodeId)}
            />
          </div>
        ) : null}
        {isFolder && isExpanded && !node.children.length ? (
          <p className="doc-empty-child" style={{ "--depth": depth + 1 } as CSSProperties}>
            空目录
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="doc-tree" aria-label={ariaLabel}>
      {nodes.map((node) => renderNode(node))}
      <TreeDropZone
        active={dropIndicator?.id === "root:end"}
        beforeNodeId={null}
        depth={0}
        id="root:end"
        label={rootEndDropLabel}
        onDrop={(event) => handleDrop(event, { beforeNodeId: null, parentId: null })}
        onTargetChange={setDropIndicator}
        parentId={null}
        visible={Boolean(draggingNodeId)}
      />
    </div>
  );
}
