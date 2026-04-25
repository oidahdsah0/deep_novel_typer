import type { CSSProperties, PointerEvent as ReactPointerEvent } from "react";
import { useEffect, useLayoutEffect, useState } from "react";

import { clampNumber } from "@/features/library/utils";

const librarySidebarVisibleStorageKey = "deep-novel-typer:library-sidebar-visible";
const libraryDetailVisibleStorageKey = "deep-novel-typer:library-detail-visible";
const libraryDetailWidthStorageKey = "deep-novel-typer:library-detail-width";
const minLibraryDetailWidth = 320;
const maxLibraryDetailWidth = 560;

export function useLibraryLayout() {
  const [isLibrarySidebarVisible, setIsLibrarySidebarVisible] = useState(true);
  const [isLibraryDetailVisible, setIsLibraryDetailVisible] = useState(true);
  const [libraryDetailWidth, setLibraryDetailWidth] = useState(400);
  const [isLibraryResizing, setIsLibraryResizing] = useState(false);

  useLayoutEffect(() => {
    setIsLibrarySidebarVisible(
      window.localStorage.getItem(librarySidebarVisibleStorageKey) !== "0",
    );
    setIsLibraryDetailVisible(
      window.localStorage.getItem(libraryDetailVisibleStorageKey) !== "0",
    );
    const savedDetailWidth = window.localStorage.getItem(libraryDetailWidthStorageKey);
    if (savedDetailWidth) {
      const parsed = Number.parseInt(savedDetailWidth, 10);
      if (Number.isFinite(parsed)) {
        setLibraryDetailWidth(clampNumber(parsed, minLibraryDetailWidth, maxLibraryDetailWidth));
      }
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(
      librarySidebarVisibleStorageKey,
      isLibrarySidebarVisible ? "1" : "0",
    );
  }, [isLibrarySidebarVisible]);

  useEffect(() => {
    window.localStorage.setItem(
      libraryDetailVisibleStorageKey,
      isLibraryDetailVisible ? "1" : "0",
    );
  }, [isLibraryDetailVisible]);

  useEffect(() => {
    window.localStorage.setItem(libraryDetailWidthStorageKey, String(libraryDetailWidth));
  }, [libraryDetailWidth]);

  function handleLibraryDetailResizePointerDown(
    event: ReactPointerEvent<HTMLButtonElement>,
  ) {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = libraryDetailWidth;
    setIsLibraryResizing(true);

    function handlePointerMove(moveEvent: PointerEvent) {
      const nextWidth = clampNumber(
        startWidth + startX - moveEvent.clientX,
        minLibraryDetailWidth,
        maxLibraryDetailWidth,
      );
      setLibraryDetailWidth(nextWidth);
    }

    function handlePointerUp() {
      setIsLibraryResizing(false);
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerUp);
    }

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerUp);
  }

  const libraryClassName = [
    "library-shell",
    isLibraryResizing ? "rail-resizing" : "",
    isLibrarySidebarVisible ? "" : "left-rail-hidden",
    isLibraryDetailVisible ? "" : "right-rail-hidden",
  ]
    .filter(Boolean)
    .join(" ");
  const libraryStyle = {
    "--library-detail-width": `${libraryDetailWidth}px`,
  } as CSSProperties;

  return {
    handleLibraryDetailResizePointerDown,
    isLibraryDetailVisible,
    isLibrarySidebarVisible,
    libraryClassName,
    libraryStyle,
    setIsLibraryDetailVisible,
    setIsLibrarySidebarVisible,
  };
}
