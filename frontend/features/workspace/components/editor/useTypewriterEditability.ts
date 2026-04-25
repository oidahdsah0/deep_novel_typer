"use client";

import { Compartment, EditorState, type Extension } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { useLayoutEffect, useMemo, useRef } from "react";

export function useTypewriterEditability(
  viewRef: { current: EditorView | null },
  isReadOnly: boolean,
) {
  const compartment = useMemo(() => new Compartment(), []);
  const initialReadOnlyRef = useRef(isReadOnly);
  const extension = useMemo(
    () => compartment.of(editorEditabilityExtensions(initialReadOnlyRef.current)),
    [compartment],
  );

  useLayoutEffect(() => {
    const view = viewRef.current;
    if (!view) return;
    view.dispatch({
      effects: compartment.reconfigure(editorEditabilityExtensions(isReadOnly)),
    });
  }, [compartment, isReadOnly, viewRef]);

  return extension;
}

function editorEditabilityExtensions(isReadOnly: boolean): Extension[] {
  return [
    EditorState.readOnly.of(isReadOnly),
    EditorView.editable.of(!isReadOnly),
  ];
}
