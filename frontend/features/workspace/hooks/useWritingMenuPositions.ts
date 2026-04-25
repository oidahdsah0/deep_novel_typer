"use client";

import { useCallback, useRef, useState } from "react";
import type {
  ActiveResource,
  ChapterSelection,
  FloatingMenuPosition,
  WritingEditorHandle,
  WritingCaretPosition,
} from "@/features/workspace/types";
import { clamp } from "@/features/workspace/utils";
import {
  isMeasurableTextEditor,
  measureTextareaCaret,
  measureTextareaCaretRect,
} from "@/features/workspace/workspaceClientUtils";

const initialDraftMenuPosition = {
  top: 96,
  left: 48,
  visible: true,
};
const initialSelectionMenuPosition: FloatingMenuPosition = {
  top: 18,
  left: 18,
  visible: false,
};
const initialWritingCaretPosition: WritingCaretPosition = {
  top: 0,
  left: 0,
  height: 24,
  visible: false,
};
const draftQuickMenuMaxWidth = 700;

type UseWritingMenuPositionsOptions = {
  chapterSelection: ChapterSelection | null;
  resourceType: ActiveResource["type"];
};

export function useWritingMenuPositions({
  chapterSelection,
  resourceType,
}: UseWritingMenuPositionsOptions) {
  const [selectionMenuPosition, setSelectionMenuPosition] = useState(
    initialSelectionMenuPosition,
  );
  const [draftMenuPosition, setDraftMenuPosition] = useState(initialDraftMenuPosition);
  const [writingCaretPosition, setWritingCaretPosition] = useState(
    initialWritingCaretPosition,
  );
  const writingSurfaceRef = useRef<WritingEditorHandle | null>(null);
  const writingMirrorRef = useRef<HTMLDivElement | null>(null);

  const hideSelectionMenu = useCallback(() => {
    setSelectionMenuPosition((current) =>
      current.visible ? { ...current, visible: false } : current,
    );
  }, []);

  const hideWritingCaret = useCallback(() => {
    setWritingCaretPosition((current) =>
      current.visible ? { ...current, visible: false } : current,
    );
  }, []);

  const updateWritingCaretPosition = useCallback(() => {
    const textarea = writingSurfaceRef.current;
    if (
      resourceType !== "chapter" ||
      !isMeasurableTextEditor(textarea) ||
      !textarea.isFocused() ||
      textarea.selectionStart !== textarea.selectionEnd
    ) {
      hideWritingCaret();
      return;
    }

    const caret = measureTextareaCaretRect(textarea, textarea.selectionEnd);
    const height = Math.round(clamp(caret.fontSize * 1.2, 20, 28));
    const top = caret.top - textarea.scrollTop + Math.max(0, (caret.lineHeight - height) / 2);
    const left = caret.left - textarea.scrollLeft;
    const nextPosition = {
      top,
      left,
      height,
      visible:
        top + height >= 0 &&
        top <= textarea.clientHeight &&
        left >= -4 &&
        left <= textarea.clientWidth + 4,
    };
    setWritingCaretPosition((current) =>
      isSameCaretPosition(current, nextPosition) ? current : nextPosition,
    );
  }, [hideWritingCaret, resourceType]);

  const updateDraftMenuPosition = useCallback(() => {
    const textarea = writingSurfaceRef.current;
    if (resourceType !== "chapter" || !isMeasurableTextEditor(textarea)) {
      setDraftMenuPosition((current) =>
        current.visible ? { ...current, visible: false } : current,
      );
      return;
    }

    const caret = measureTextareaCaret(textarea, textarea.selectionEnd);
    const rawTop = caret.top - textarea.scrollTop + 12;
    const rawLeft = caret.left - textarea.scrollLeft - 44;
    const minTop = 12;
    const maxTop = Math.max(minTop, textarea.clientHeight - 56);
    const minLeft = 18;
    const estimatedMenuWidth = Math.min(
      draftQuickMenuMaxWidth,
      Math.max(240, textarea.clientWidth - 36),
    );
    const maxLeft = Math.max(minLeft, textarea.clientWidth - estimatedMenuWidth - 18);
    const nextPosition = {
      top: clamp(rawTop, minTop, maxTop),
      left: clamp(rawLeft, minLeft, maxLeft),
      visible: rawTop >= minTop - 24 && rawTop <= textarea.clientHeight - 12,
    };
    setDraftMenuPosition((current) =>
      isSameFloatingPosition(current, nextPosition) ? current : nextPosition,
    );
  }, [resourceType]);

  const updateSelectionMenuPosition = useCallback((selection = chapterSelection) => {
    const textarea = writingSurfaceRef.current;
    if (resourceType !== "chapter" || !isMeasurableTextEditor(textarea) || !selection) {
      hideSelectionMenu();
      return;
    }

    const caret = measureTextareaCaret(textarea, selection.end);
    const rawTop = caret.top - textarea.scrollTop + 8;
    const rawLeft = caret.left - textarea.scrollLeft;
    const buttonHalfWidth = 62;
    const minLeft = buttonHalfWidth + 12;
    const maxLeft = Math.max(minLeft, textarea.clientWidth - buttonHalfWidth - 12);
    const minTop = 12;
    const maxTop = Math.max(minTop, textarea.clientHeight - 46);
    const nextPosition = {
      top: clamp(rawTop, minTop, maxTop),
      left: clamp(rawLeft, minLeft, maxLeft),
      visible: rawTop >= minTop - 12 && rawTop <= textarea.clientHeight - 12,
    };
    setSelectionMenuPosition((current) =>
      isSameFloatingPosition(current, nextPosition) ? current : nextPosition,
    );
  }, [chapterSelection, hideSelectionMenu, resourceType]);

  return {
    draftMenuPosition,
    hideSelectionMenu,
    hideWritingCaret,
    selectionMenuPosition,
    setSelectionMenuPosition,
    updateDraftMenuPosition,
    updateSelectionMenuPosition,
    updateWritingCaretPosition,
    writingCaretPosition,
    writingMirrorRef,
    writingSurfaceRef,
  };
}

function isSameFloatingPosition(
  current: FloatingMenuPosition,
  next: FloatingMenuPosition,
) {
  return (
    Math.abs(current.top - next.top) < 0.5 &&
    Math.abs(current.left - next.left) < 0.5 &&
    current.visible === next.visible
  );
}

function isSameCaretPosition(
  current: WritingCaretPosition,
  next: WritingCaretPosition,
) {
  return (
    Math.abs(current.top - next.top) < 0.5 &&
    Math.abs(current.left - next.left) < 0.5 &&
    Math.abs(current.height - next.height) < 0.5 &&
    current.visible === next.visible
  );
}
