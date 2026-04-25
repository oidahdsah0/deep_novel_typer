"use client";

import type { CSSProperties, DragEvent } from "react";
import type { TreeDropIndicatorState } from "./treeTypes";

export function TreeDropZone({
  active,
  beforeNodeId,
  depth,
  id,
  label,
  onDrop,
  onTargetChange,
  parentId,
  visible,
}: {
  active: boolean;
  beforeNodeId: string | null;
  depth: number;
  id: string;
  label: string;
  onDrop: (event: DragEvent<HTMLDivElement>) => void;
  onTargetChange: (indicator: TreeDropIndicatorState | null) => void;
  parentId: string | null;
  visible: boolean;
}) {
  return (
    <div
      aria-hidden
      className={[
        "tree-drop-zone",
        visible ? "visible" : "",
        active ? "active" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onDragLeave={() => onTargetChange(null)}
      onDragOver={(event) => {
        if (!visible) {
          return;
        }
        event.preventDefault();
        onTargetChange({ beforeNodeId, id, parentId });
      }}
      onDrop={onDrop}
      style={{ "--depth": depth } as CSSProperties}
      title={label}
    />
  );
}
