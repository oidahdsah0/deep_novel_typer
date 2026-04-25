import assert from "node:assert/strict";
import test from "node:test";

import type { WritingEditorHandle } from "../features/workspace/types";
import { scrollTextareaIndexIntoView } from "../features/workspace/workspaceClientUtils";

test("scrollTextareaIndexIntoView uses margin clamping for writing editor handles", () => {
  let scrollTop = 100;
  let centered = false;
  const handle = writingEditorHandle({
    clientHeight: 500,
    coordsTop: 900,
    getScrollTop: () => scrollTop,
    onCenter: () => {
      centered = true;
    },
    setScrollTop: (value) => {
      scrollTop = value;
    },
  });

  scrollTextareaIndexIntoView(handle, 12);

  assert.equal(centered, false);
  assert.equal(scrollTop, 516);
});

test("scrollTextareaIndexIntoView keeps visible writing editor handles still", () => {
  let scrollTop = 100;
  const handle = writingEditorHandle({
    clientHeight: 500,
    coordsTop: 200,
    getScrollTop: () => scrollTop,
    onCenter: () => {
      throw new Error("scrollIndexIntoView should not be called");
    },
    setScrollTop: (value) => {
      scrollTop = value;
    },
  });

  scrollTextareaIndexIntoView(handle, 12);

  assert.equal(scrollTop, 100);
});

function writingEditorHandle({
  clientHeight,
  coordsTop,
  getScrollTop,
  onCenter,
  setScrollTop,
}: {
  clientHeight: number;
  coordsTop: number;
  getScrollTop: () => number;
  onCenter: () => void;
  setScrollTop: (value: number) => void;
}): WritingEditorHandle {
  return {
    get clientHeight() {
      return clientHeight;
    },
    clientWidth: 800,
    coordsAtIndex: () => ({
      fontSize: 20,
      height: 20,
      left: 0,
      lineHeight: 20,
      top: coordsTop,
    }),
    focus: () => undefined,
    isFocused: () => true,
    scrollIndexIntoView: onCenter,
    scrollLeft: 0,
    get scrollTop() {
      return getScrollTop();
    },
    set scrollTop(value: number) {
      setScrollTop(value);
    },
    selectionEnd: 0,
    selectionStart: 0,
    setSelectionRange: () => undefined,
    setSelectionRangeWithoutScroll: () => undefined,
    value: "正文",
  };
}
