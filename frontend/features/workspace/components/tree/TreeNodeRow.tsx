"use client";

import { ChevronDown, ChevronRight, FileText, Folder, GripVertical } from "lucide-react";
import type { CSSProperties, DragEvent, ReactNode } from "react";

export function TreeNodeRow({
  actions,
  canDropInside,
  depth,
  dragLabel,
  dragging,
  dropInside,
  expanded,
  folder,
  meta,
  onDragEnd,
  onDragStart,
  onDropInside,
  onOpen,
  onTargetInside,
  selected,
  title,
}: {
  actions: ReactNode;
  canDropInside: boolean;
  depth: number;
  dragLabel: string;
  dragging: boolean;
  dropInside: boolean;
  expanded: boolean;
  folder: boolean;
  meta?: string | null;
  onDragEnd: () => void;
  onDragStart: (event: DragEvent<HTMLButtonElement>) => void;
  onDropInside: (event: DragEvent<HTMLDivElement>) => void;
  onOpen: () => void;
  onTargetInside: () => void;
  selected: boolean;
  title: string;
}) {
  return (
    <div
      className={[
        selected ? "doc-node-row active" : "doc-node-row",
        dragging ? "dragging" : "",
        dropInside ? "drop-inside" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onDragOver={(event) => {
        if (!canDropInside) {
          return;
        }
        event.preventDefault();
        onTargetInside();
      }}
      onDrop={(event) => {
        if (canDropInside) {
          onDropInside(event);
        }
      }}
      style={{ "--depth": depth } as CSSProperties}
    >
      <button
        aria-label={dragLabel}
        className="tiny-tool drag-handle"
        draggable
        onClick={(event) => event.preventDefault()}
        onDragEnd={onDragEnd}
        onDragStart={onDragStart}
        type="button"
      >
        <GripVertical size={13} />
      </button>
      <button className="doc-node-main" onClick={onOpen} type="button">
        {folder ? (
          expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />
        ) : (
          <FileText size={14} />
        )}
        {folder ? <Folder size={14} /> : null}
        <span>{title}</span>
        {meta ? <small>{meta}</small> : null}
      </button>
      {actions}
    </div>
  );
}
