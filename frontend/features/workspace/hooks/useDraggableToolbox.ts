"use client";

import type { CSSProperties, PointerEvent } from "react";
import { useLayoutEffect, useRef, useState } from "react";

type ToolboxPosition = {
  x: number;
  y: number;
};

type DragState = {
  height: number;
  originX: number;
  originY: number;
  pointerId: number;
  startX: number;
  startY: number;
  width: number;
};

const TOOLBOX_MARGIN = 12;

export function useDraggableToolbox(isOpen: boolean) {
  const drawerRef = useRef<HTMLElement | null>(null);
  const dragRef = useRef<DragState | null>(null);
  const [position, setPosition] = useState<ToolboxPosition | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  useLayoutEffect(() => {
    if (!isOpen) return;
    const drawer = drawerRef.current;
    if (!drawer) return;

    const syncPosition = () => {
      const rect = drawer.getBoundingClientRect();
      setPosition((current) => {
        const initial = current ?? { x: window.innerWidth - rect.width - 18, y: 18 };
        return clampToolboxPosition(initial, rect.width, rect.height);
      });
    };

    syncPosition();
    window.addEventListener("resize", syncPosition);
    return () => window.removeEventListener("resize", syncPosition);
  }, [isOpen]);

  const drawerStyle: CSSProperties | undefined = position
    ? { left: position.x, right: "auto", top: position.y }
    : undefined;

  function beginDrag(event: PointerEvent<HTMLElement>) {
    if (event.button !== 0 || isInteractiveDragTarget(event.target)) return;
    const drawer = drawerRef.current;
    if (!drawer) return;
    const rect = drawer.getBoundingClientRect();
    const origin = position ?? { x: rect.left, y: rect.top };
    dragRef.current = {
      height: rect.height,
      originX: origin.x,
      originY: origin.y,
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      width: rect.width,
    };
    setPosition(origin);
    setIsDragging(true);
    event.currentTarget.setPointerCapture(event.pointerId);
    event.preventDefault();
  }

  function moveDrag(event: PointerEvent<HTMLElement>) {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    setPosition(
      clampToolboxPosition(
        {
          x: drag.originX + event.clientX - drag.startX,
          y: drag.originY + event.clientY - drag.startY,
        },
        drag.width,
        drag.height,
      ),
    );
  }

  function finishDrag(event: PointerEvent<HTMLElement>) {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    dragRef.current = null;
    setIsDragging(false);
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  return {
    dragHandlers: {
      onPointerCancel: finishDrag,
      onPointerDown: beginDrag,
      onPointerMove: moveDrag,
      onPointerUp: finishDrag,
    },
    drawerRef,
    drawerStyle,
    isDragging,
  };
}

function clampToolboxPosition(
  position: ToolboxPosition,
  width: number,
  height: number,
): ToolboxPosition {
  return {
    x: clamp(position.x, TOOLBOX_MARGIN, window.innerWidth - width - TOOLBOX_MARGIN),
    y: clamp(position.y, TOOLBOX_MARGIN, window.innerHeight - height - TOOLBOX_MARGIN),
  };
}

function clamp(value: number, min: number, max: number) {
  if (max < min) return min;
  return Math.min(max, Math.max(min, value));
}

function isInteractiveDragTarget(target: EventTarget) {
  return target instanceof Element && Boolean(target.closest("button, a, input, select, textarea"));
}
