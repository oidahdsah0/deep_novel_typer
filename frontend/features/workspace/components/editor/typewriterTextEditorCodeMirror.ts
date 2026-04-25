import {
  EditorState,
  RangeSetBuilder,
  StateEffect,
  StateField,
} from "@codemirror/state";
import {
  Decoration,
  type DecorationSet,
  EditorView,
  type ViewUpdate,
  ViewPlugin,
} from "@codemirror/view";
import type { WritingEditorKeyEvent } from "@/features/workspace/types";

const highlightIdAttribute = "data-typewriter-highlight-id";

export type TypewriterTextHighlight = {
  className: string;
  endOffset: number;
  id: string;
  startOffset: number;
  style?: string;
  title?: string;
};

export const setTypewriterTextHighlights =
  StateEffect.define<TypewriterTextHighlight[]>();

export const typewriterTextHighlightField = StateField.define<DecorationSet>({
  create() {
    return Decoration.none;
  },
  update(highlights, transaction) {
    let nextHighlights = highlights.map(transaction.changes);
    transaction.effects.forEach((effect) => {
      if (effect.is(setTypewriterTextHighlights)) {
        nextHighlights = buildHighlightDecorations(transaction.state, effect.value);
      }
    });
    return nextHighlights;
  },
  provide: (field) => EditorView.decorations.from(field),
});

export const typewriterParagraphLines = ViewPlugin.fromClass(
  class {
    decorations: DecorationSet;

    constructor(view: EditorView) {
      this.decorations = buildParagraphDecorations(view);
    }

    update(update: ViewUpdate) {
      if (update.docChanged || update.viewportChanged) {
        this.decorations = buildParagraphDecorations(update.view);
      }
    }
  },
  {
    decorations: (plugin) => plugin.decorations,
  },
);

export function toWritingKeyEvent(
  event: KeyboardEvent,
): WritingEditorKeyEvent {
  return {
    altKey: event.altKey,
    ctrlKey: event.ctrlKey,
    key: event.key,
    metaKey: event.metaKey,
    nativeEvent: {
      isComposing: event.isComposing,
    },
    preventDefault: () => event.preventDefault(),
    shiftKey: event.shiftKey,
  };
}

export function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

export function highlightFromTarget(
  target: EventTarget | null,
  highlightsById: Map<string, TypewriterTextHighlight>,
) {
  if (!(target instanceof Element)) return null;
  const element = target.closest<HTMLElement>(`[${highlightIdAttribute}]`);
  const highlightId = element?.dataset.typewriterHighlightId;
  return highlightId ? highlightsById.get(highlightId) ?? null : null;
}

function buildParagraphDecorations(view: EditorView) {
  const builder = new RangeSetBuilder<Decoration>();
  for (const range of view.visibleRanges) {
    let line = view.state.doc.lineAt(range.from);
    while (line.from <= range.to) {
      if (line.text.trim()) {
        builder.add(
          line.from,
          line.from,
          Decoration.line({ class: "typewriter-paragraph-line" }),
        );
      }
      if (line.to >= range.to || line.number >= view.state.doc.lines) break;
      line = view.state.doc.line(line.number + 1);
    }
  }
  return builder.finish();
}

function buildHighlightDecorations(
  state: EditorState,
  highlights: TypewriterTextHighlight[],
) {
  const builder = new RangeSetBuilder<Decoration>();
  highlights
    .map((highlight) => ({
      ...highlight,
      endOffset: clamp(highlight.endOffset, 0, state.doc.length),
      startOffset: clamp(highlight.startOffset, 0, state.doc.length),
    }))
    .filter((highlight) => highlight.endOffset > highlight.startOffset)
    .sort((left, right) => left.startOffset - right.startOffset)
    .forEach((highlight) => {
      builder.add(
        highlight.startOffset,
        highlight.endOffset,
        Decoration.mark({
          attributes: highlightAttributes(highlight),
          class: highlight.className,
        }),
      );
    });
  return builder.finish();
}

function highlightAttributes(highlight: TypewriterTextHighlight) {
  return {
    [highlightIdAttribute]: highlight.id,
    ...(highlight.style ? { style: highlight.style } : {}),
    ...(highlight.title ? { title: highlight.title } : {}),
  };
}
