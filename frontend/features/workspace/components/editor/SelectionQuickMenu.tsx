"use client";

import { Sparkles } from "lucide-react";

export function SelectionQuickMenu({
  left,
  onPolish,
  top,
  visible,
}: {
  left: number;
  onPolish: () => void;
  top: number;
  visible: boolean;
}) {
  return (
    <div
      aria-label="选区操作"
      className={visible ? "selection-fab-menu visible" : "selection-fab-menu"}
      style={{ left, top }}
    >
      <button
        className="selection-fab-action"
        onClick={onPolish}
        onMouseDown={(event) => event.preventDefault()}
        type="button"
      >
        <Sparkles size={15} />
        润色选中
      </button>
    </div>
  );
}
