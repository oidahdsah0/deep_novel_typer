"use client";

import { EditorView } from "@codemirror/view";
import { type ForwardedRef, useImperativeHandle } from "react";
import type { WritingEditorHandle } from "@/features/workspace/types";
import { clamp } from "./typewriterTextEditorCodeMirror";

export function useTypewriterEditorHandle(
  ref: ForwardedRef<WritingEditorHandle>,
  viewRef: { current: EditorView | null },
) {
  useImperativeHandle(ref, () => ({
    get clientHeight() {
      return viewRef.current?.scrollDOM.clientHeight ?? 0;
    },
    get clientWidth() {
      return viewRef.current?.scrollDOM.clientWidth ?? 0;
    },
    get scrollLeft() {
      return viewRef.current?.scrollDOM.scrollLeft ?? 0;
    },
    get scrollTop() {
      return viewRef.current?.scrollDOM.scrollTop ?? 0;
    },
    set scrollTop(value) {
      const view = viewRef.current;
      if (view) view.scrollDOM.scrollTop = value;
    },
    get selectionEnd() {
      return viewRef.current?.state.selection.main.to ?? 0;
    },
    get selectionStart() {
      return viewRef.current?.state.selection.main.from ?? 0;
    },
    get value() {
      return viewRef.current?.state.doc.toString() ?? "";
    },
    coordsAtIndex(index) {
      const view = viewRef.current;
      if (!view) return null;
      const safeIndex = clamp(index, 0, view.state.doc.length);
      const coords = view.coordsAtPos(safeIndex);
      if (!coords) return null;
      const scrollerRect = view.scrollDOM.getBoundingClientRect();
      const styles = window.getComputedStyle(view.contentDOM);
      const fontSize = parseFloat(styles.fontSize) || 20;
      const lineHeight = parseFloat(styles.lineHeight) || fontSize * 1.8;
      return {
        fontSize,
        height: coords.bottom - coords.top,
        left: coords.left - scrollerRect.left + view.scrollDOM.scrollLeft,
        lineHeight,
        top: coords.top - scrollerRect.top + view.scrollDOM.scrollTop,
      };
    },
    focus() {
      viewRef.current?.focus();
    },
    isFocused() {
      return viewRef.current?.hasFocus ?? false;
    },
    scrollIndexIntoView(index) {
      const view = viewRef.current;
      if (!view) return;
      const target = clamp(index, 0, view.state.doc.length);
      view.dispatch({
        effects: EditorView.scrollIntoView(target, {
          y: "center",
        }),
      });
    },
    setSelectionRange(start, end) {
      const view = viewRef.current;
      if (!view) return;
      const anchor = clamp(start, 0, view.state.doc.length);
      const head = clamp(end, 0, view.state.doc.length);
      view.dispatch({
        selection: { anchor, head },
        effects: EditorView.scrollIntoView(anchor, { y: "center" }),
      });
    },
    setSelectionRangeWithoutScroll(start, end) {
      const view = viewRef.current;
      if (!view) return;
      const anchor = clamp(start, 0, view.state.doc.length);
      const head = clamp(end, 0, view.state.doc.length);
      view.dispatch({
        selection: { anchor, head },
      });
    },
  }), [viewRef]);
}
