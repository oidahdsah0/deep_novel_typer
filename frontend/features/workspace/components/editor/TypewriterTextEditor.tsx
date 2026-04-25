"use client";

import { history, historyKeymap, defaultKeymap } from "@codemirror/commands";
import { EditorState } from "@codemirror/state";
import { EditorView, keymap } from "@codemirror/view";
import { type CSSProperties, forwardRef, useEffect, useMemo, useRef } from "react";
import type { WritingEditorHandle, WritingEditorKeyEvent } from "@/features/workspace/types";
import {
  clamp,
  highlightFromTarget,
  setTypewriterTextHighlights,
  toWritingKeyEvent,
  type TypewriterTextHighlight,
  typewriterTextHighlightField,
  typewriterParagraphLines,
} from "./typewriterTextEditorCodeMirror";
import { useTypewriterEditability } from "./useTypewriterEditability";
import { useTypewriterEditorHandle } from "./useTypewriterEditorHandle";

export type { TypewriterTextHighlight } from "./typewriterTextEditorCodeMirror";

type TypewriterTextEditorProps = {
  firstLineIndentChars: number;
  fontSizePx: number;
  highlights?: TypewriterTextHighlight[];
  isReadOnly: boolean;
  lineHeightMultiplier: number;
  onBlur: () => void;
  onChange: (value: string) => void;
  onFocus: () => void;
  onHighlightPointerEnter?: (highlightId: string) => void;
  onHighlightPointerLeave?: () => void;
  onKeyDown: (event: WritingEditorKeyEvent) => void;
  onScroll: () => void;
  onSelectionChange: () => void;
  paragraphGapLines: number;
  value: string;
};

export const TypewriterTextEditor = forwardRef<
  WritingEditorHandle,
  TypewriterTextEditorProps
>(function TypewriterTextEditor(
  {
    firstLineIndentChars,
    fontSizePx,
    highlights = [],
    isReadOnly,
    lineHeightMultiplier,
    onBlur,
    onChange,
    onFocus,
    onHighlightPointerEnter,
    onHighlightPointerLeave,
    onKeyDown,
    onScroll,
    onSelectionChange,
    paragraphGapLines,
    value,
  },
  ref,
) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const viewRef = useRef<EditorView | null>(null);
  const onChangeRef = useRef(onChange);
  const onBlurRef = useRef(onBlur);
  const onFocusRef = useRef(onFocus);
  const onHighlightPointerEnterRef = useRef(onHighlightPointerEnter);
  const onHighlightPointerLeaveRef = useRef(onHighlightPointerLeave);
  const onKeyDownRef = useRef(onKeyDown);
  const onScrollRef = useRef(onScroll);
  const onSelectionChangeRef = useRef(onSelectionChange);
  const valueRef = useRef(value);
  const highlightsByIdRef = useRef(new Map<string, TypewriterTextHighlight>());

  onChangeRef.current = onChange;
  onBlurRef.current = onBlur;
  onFocusRef.current = onFocus;
  onHighlightPointerEnterRef.current = onHighlightPointerEnter;
  onHighlightPointerLeaveRef.current = onHighlightPointerLeave;
  onKeyDownRef.current = onKeyDown;
  onScrollRef.current = onScroll;
  onSelectionChangeRef.current = onSelectionChange;
  valueRef.current = value;
  highlightsByIdRef.current = new Map(highlights.map((highlight) => [highlight.id, highlight]));
  const editabilityExtension = useTypewriterEditability(viewRef, isReadOnly);

  const extensions = useMemo(
    () => [
      typewriterParagraphLines,
      typewriterTextHighlightField,
      EditorView.lineWrapping,
      history(),
      keymap.of([...defaultKeymap, ...historyKeymap]),
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          onChangeRef.current(update.state.doc.toString());
        }
        if (update.docChanged || update.selectionSet) {
          onSelectionChangeRef.current();
        }
      }),
      EditorView.domEventHandlers({
        blur() {
          onBlurRef.current();
          return false;
        },
        focus() {
          onFocusRef.current();
          return false;
        },
        keydown(event) {
          onKeyDownRef.current(toWritingKeyEvent(event));
          return event.defaultPrevented;
        },
        pointerdown(event, view) {
          const highlight = highlightFromTarget(event.target, highlightsByIdRef.current);
          if (!highlight) return false;
          event.preventDefault();
          const anchor = clamp(highlight.startOffset, 0, view.state.doc.length);
          const head = clamp(highlight.endOffset, 0, view.state.doc.length);
          view.focus();
          view.dispatch({
            selection: { anchor, head },
            effects: EditorView.scrollIntoView(anchor, { y: "center" }),
          });
          return true;
        },
        pointerout(event) {
          if (highlightFromTarget(event.target, highlightsByIdRef.current)) {
            onHighlightPointerLeaveRef.current?.();
          }
          return false;
        },
        pointerover(event) {
          const highlight = highlightFromTarget(event.target, highlightsByIdRef.current);
          if (highlight) {
            onHighlightPointerEnterRef.current?.(highlight.id);
          }
          return false;
        },
        scroll() {
          onScrollRef.current();
          return false;
        },
      }),
      editabilityExtension,
    ],
    [editabilityExtension],
  );

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const state = EditorState.create({
      doc: valueRef.current,
      extensions,
    });
    const view = new EditorView({
      parent: host,
      state,
    });
    viewRef.current = view;
    view.dispatch({
      effects: setTypewriterTextHighlights.of([...highlightsByIdRef.current.values()]),
    });
    return () => {
      view.destroy();
      viewRef.current = null;
    };
  }, [extensions]);

  useEffect(() => {
    const view = viewRef.current;
    if (!view) return;
    const currentValue = view.state.doc.toString();
    if (currentValue === value) return;
    view.dispatch({
      changes: { from: 0, to: view.state.doc.length, insert: value },
    });
  }, [value]);

  useEffect(() => {
    const view = viewRef.current;
    if (!view) return;
    view.dispatch({
      effects: setTypewriterTextHighlights.of(highlights),
    });
  }, [highlights]);

  useEffect(() => {
    viewRef.current?.requestMeasure();
  }, [firstLineIndentChars, fontSizePx, lineHeightMultiplier, paragraphGapLines]);

  useTypewriterEditorHandle(ref, viewRef);

  return (
    <div
      aria-label="小说正文"
      className="typewriter-editor"
      ref={hostRef}
      style={{
        "--typewriter-first-line-indent-chars": firstLineIndentChars,
        "--typewriter-font-size-px": `${fontSizePx}px`,
        "--typewriter-line-height-multiplier": lineHeightMultiplier,
        "--typewriter-line-height-px": `${lineHeightMultiplier * fontSizePx}px`,
        "--typewriter-paragraph-gap-lines": paragraphGapLines,
      } as CSSProperties}
    />
  );
});
