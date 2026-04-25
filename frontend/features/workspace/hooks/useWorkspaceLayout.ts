"use client";

import type { CSSProperties, PointerEvent as ReactPointerEvent } from "react";
import { useEffect, useLayoutEffect, useState } from "react";
import { clamp } from "../utils";
import type { WorkspaceLayoutApi } from "./workspaceInteractionApiTypes";

export type { WorkspaceLayoutApi } from "./workspaceInteractionApiTypes";

const railWidthStorageKey = "deep-novel-typer:project-rail-width";
const insightRailWidthStorageKey = "deep-novel-typer:insight-rail-width";
const projectRailVisibleStorageKey = "deep-novel-typer:project-rail-visible";
const insightRailVisibleStorageKey = "deep-novel-typer:insight-rail-visible";
const minProjectRailWidth = 260;
const maxProjectRailWidth = 520;
const minInsightRailWidth = 280;
const maxInsightRailWidth = 560;

type ResizeDragState = {
  rail: "project" | "insight";
  startX: number;
  startWidth: number;
};

export function useWorkspaceLayout() {
  const [projectRailWidth, setProjectRailWidth] = useState(320);
  const [insightRailWidth, setInsightRailWidth] = useState(360);
  const [isProjectRailVisible, setIsProjectRailVisible] = useState(true);
  const [isInsightRailVisible, setIsInsightRailVisible] = useState(true);
  const [resizeDrag, setResizeDrag] = useState<ResizeDragState | null>(null);
  const isRailResizing = resizeDrag !== null;

  useLayoutEffect(() => {
    const saved = window.localStorage.getItem(railWidthStorageKey);
    if (saved) {
      const parsed = Number.parseInt(saved, 10);
      if (Number.isFinite(parsed)) {
        setProjectRailWidth(clamp(parsed, minProjectRailWidth, maxProjectRailWidth));
      }
    }
    const savedInsightWidth = window.localStorage.getItem(insightRailWidthStorageKey);
    if (savedInsightWidth) {
      const parsed = Number.parseInt(savedInsightWidth, 10);
      if (Number.isFinite(parsed)) {
        setInsightRailWidth(clamp(parsed, minInsightRailWidth, maxInsightRailWidth));
      }
    }
    setIsProjectRailVisible(window.localStorage.getItem(projectRailVisibleStorageKey) !== "0");
    setIsInsightRailVisible(window.localStorage.getItem(insightRailVisibleStorageKey) !== "0");
  }, []);

  useEffect(() => {
    window.localStorage.setItem(railWidthStorageKey, String(projectRailWidth));
  }, [projectRailWidth]);

  useEffect(() => {
    window.localStorage.setItem(insightRailWidthStorageKey, String(insightRailWidth));
  }, [insightRailWidth]);

  useEffect(() => {
    window.localStorage.setItem(projectRailVisibleStorageKey, isProjectRailVisible ? "1" : "0");
  }, [isProjectRailVisible]);

  useEffect(() => {
    window.localStorage.setItem(insightRailVisibleStorageKey, isInsightRailVisible ? "1" : "0");
  }, [isInsightRailVisible]);

  useEffect(() => {
    if (!resizeDrag) return;
    const { rail, startWidth, startX } = resizeDrag;
    function handlePointerMove(moveEvent: PointerEvent) {
      if (rail === "project") {
        setProjectRailWidth(
          clamp(
            startWidth + moveEvent.clientX - startX,
            minProjectRailWidth,
            maxProjectRailWidth,
          ),
        );
        return;
      }
      setInsightRailWidth(
        clamp(
          startWidth + startX - moveEvent.clientX,
          minInsightRailWidth,
          maxInsightRailWidth,
        ),
      );
    }

    function handlePointerUp() {
      setResizeDrag(null);
    }

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerUp);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerUp);
    };
  }, [resizeDrag]);

  function handleRailResizePointerDown(event: ReactPointerEvent<HTMLButtonElement>) {
    event.preventDefault();
    setResizeDrag({
      rail: "project",
      startX: event.clientX,
      startWidth: projectRailWidth,
    });
  }

  function handleInsightResizePointerDown(event: ReactPointerEvent<HTMLButtonElement>) {
    event.preventDefault();
    setResizeDrag({
      rail: "insight",
      startX: event.clientX,
      startWidth: insightRailWidth,
    });
  }

  const workspaceStyle = {
    "--project-rail-width": `${projectRailWidth}px`,
    "--insight-rail-width": `${insightRailWidth}px`,
  } as CSSProperties;

  const workspaceClassName = [
    "workspace-shell",
    isRailResizing ? "rail-resizing" : "",
    isProjectRailVisible ? "" : "left-rail-hidden",
    isInsightRailVisible ? "" : "right-rail-hidden",
  ]
    .filter(Boolean)
    .join(" ");

  return {
    handleInsightResizePointerDown,
    handleRailResizePointerDown,
    isInsightRailVisible,
    isProjectRailVisible,
    setIsInsightRailVisible,
    setIsProjectRailVisible,
    workspaceClassName,
    workspaceStyle,
  } satisfies WorkspaceLayoutApi;
}
