import type {
  ChapterNode,
  DocumentNode,
  DraftGenerationAction,
  GeneratedChapterBlueprint,
  GeneratedDraft,
  PromptProfile,
} from "@/lib/api/index";

export type SaveState = "idle" | "saving" | "saved" | "error" | "conflict";
export type PresetSaveState = "idle" | "saving" | "saved" | "error";
export type PendingDraftGenerationAction = DraftGenerationAction | "quick_next_paragraph";
export type GenerationDialogState = {
  action: DraftGenerationAction;
  anchor: DraftInsertionContext;
  error: string | null;
  result: GeneratedDraft | null;
} | null;
export type ChapterBlueprintDialogState = {
  anchor: DraftInsertionContext;
  error: string | null;
  result: GeneratedChapterBlueprint | null;
} | null;
export type DraftInsertionContext = {
  cursorIndex: number;
  previousParagraph: string;
  nextParagraph: string;
};
export type PendingDraftGenerationState =
  | {
      action: PendingDraftGenerationAction;
      chapterId: string;
      cursorIndex: number;
      status: "generating";
    }
  | {
      action: PendingDraftGenerationAction;
      baseContent: string;
      chapterId: string;
      end: number;
      model: string | null;
      nextContent: string;
      source: GeneratedDraft["source"];
      start: number;
      status: "ready";
      text: string;
    }
  | {
      action: PendingDraftGenerationAction;
      chapterId: string;
      error: string;
      status: "error";
    };
export type PolishDialogState = {
  error: string | null;
  result: GeneratedDraft | null;
} | null;
export type DocumentGenerationAction = "polish_selection" | "continue_document";
export type DocumentGenerationDialogState = {
  action: DocumentGenerationAction;
  error: string | null;
  result: GeneratedDraft | null;
} | null;
export type ChapterSelection = {
  start: number;
  end: number;
  text: string;
};
export type FloatingMenuPosition = {
  top: number;
  left: number;
  visible: boolean;
};
export type WritingCaretPosition = FloatingMenuPosition & {
  height: number;
};
export type WritingEditorKeyEvent = {
  altKey: boolean;
  ctrlKey: boolean;
  key: string;
  metaKey: boolean;
  nativeEvent: {
    isComposing: boolean;
  };
  preventDefault: () => void;
  shiftKey: boolean;
};
export type WritingEditorHandle = {
  readonly clientHeight: number;
  readonly clientWidth: number;
  readonly scrollLeft: number;
  scrollTop: number;
  readonly selectionEnd: number;
  readonly selectionStart: number;
  readonly value: string;
  coordsAtIndex: (index: number) => {
    fontSize: number;
    height: number;
    left: number;
    lineHeight: number;
    top: number;
  } | null;
  focus: () => void;
  isFocused: () => boolean;
  scrollIndexIntoView: (index: number) => void;
  setSelectionRange: (start: number, end: number) => void;
  setSelectionRangeWithoutScroll: (start: number, end: number) => void;
};
export type PromptMaterialOption = {
  id: string;
  title: string;
  meta: string;
};
export type PromptProfileDraft = PromptProfile & {
  apiConfigId: string;
  configText: string;
  includeChapterSynopsis: boolean;
  recentChapterCount: number;
  recentChapterEnabled: boolean;
  temperature: string;
};
export type HelpTooltip = {
  left: number;
  placement: "top" | "bottom";
  text: string;
  top: number;
};
export type PerspectiveDraft = {
  name: string;
  description: string;
  instructions: string;
  api_config_id: string | null;
};
export type ActiveResource =
  | { type: "chapter"; id: string; title: string }
  | { type: "document"; id: string; title: string };
export type ChapterDraftState =
  | { mode: "create"; type: "folder" | "chapter"; parentId: string | null; title: string }
  | { mode: "rename"; node: ChapterNode; title: string };
export type DocumentDraftState =
  | { mode: "create"; type: "folder" | "markdown"; parentId: string | null; title: string }
  | { mode: "rename"; node: DocumentNode; title: string };
export type MarkdownViewMode = "edit" | "split" | "preview";
