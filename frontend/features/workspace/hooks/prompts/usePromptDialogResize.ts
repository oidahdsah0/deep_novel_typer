"use client";

import { useState, type CSSProperties, type PointerEvent as ReactPointerEvent } from "react";
import { clamp } from "../../utils";

export function usePromptDialogResize() {
  const [dialogSize, setDialogSize] = useState<{ width: number; height: number } | null>(null);

  function handleResizeStart(event: ReactPointerEvent<HTMLButtonElement>) {
    event.preventDefault();
    event.stopPropagation();
    const dialog = event.currentTarget.closest(".prompt-manager-dialog");
    if (!(dialog instanceof HTMLElement)) {
      return;
    }

    const rect = dialog.getBoundingClientRect();
    const startX = event.clientX;
    const startY = event.clientY;
    const startWidth = rect.width;
    const startHeight = rect.height;

    function handlePointerMove(moveEvent: PointerEvent) {
      const maxWidth = Math.max(320, window.innerWidth - 36);
      const maxHeight = Math.max(360, window.innerHeight - 36);
      const minWidth = Math.min(720, maxWidth);
      const minHeight = Math.min(560, maxHeight);
      setDialogSize({
        height: clamp(startHeight + moveEvent.clientY - startY, minHeight, maxHeight),
        width: clamp(startWidth + moveEvent.clientX - startX, minWidth, maxWidth),
      });
    }

    function handlePointerUp() {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerUp);
    }

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerUp);
  }

  const dialogStyle = dialogSize
    ? ({
        "--prompt-dialog-height": `${dialogSize.height}px`,
        "--prompt-dialog-width": `${dialogSize.width}px`,
      } as CSSProperties)
    : undefined;

  return { dialogStyle, handleResizeStart };
}
