import type {
  ChapterSummary,
  DocumentNode,
  ProjectSearchResult,
  PromptRequestType,
} from "@/lib/api/index";
import type { SaveState, WritingEditorHandle } from "@/features/workspace/types";

export function buildProjectDebugHref(projectId: string) {
  const encodedProjectId = encodeURIComponent(projectId);
  return `/debug?project_id=${encodedProjectId}&return_project_id=${encodedProjectId}`;
}

export function extractLastParagraph(value: string) {
  const paragraphs = value
    .split(/\n+/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
  return paragraphs.at(-1) ?? "";
}

export function suggestionParagraphFromContent(value: string) {
  return extractLastParagraph(value) || value.trim();
}

export function saveStatusLabel(saveState: SaveState) {
  if (saveState === "saving") return "正在保存";
  if (saveState === "conflict") return "保存冲突";
  if (saveState === "error") return "保存失败";
  return "已保存";
}

export type MeasurableTextEditor = HTMLTextAreaElement | WritingEditorHandle;

type CaretRect = {
  fontSize: number;
  left: number;
  lineHeight: number;
  top: number;
};

const fallbackCaretRect: CaretRect = {
  fontSize: 20,
  left: 0,
  lineHeight: 24,
  top: 0,
};

export function isMeasurableTextEditor(value: unknown): value is MeasurableTextEditor {
  return value instanceof HTMLTextAreaElement || isWritingEditorHandle(value);
}

export function measureTextareaCaret(textarea: MeasurableTextEditor, index: number) {
  const rect = measureTextareaCaretRect(textarea, index);
  return {
    left: rect.left,
    top: rect.top + rect.lineHeight,
  };
}

export function measureTextareaCaretRect(textarea: MeasurableTextEditor, index: number) {
  if (isWritingEditorHandle(textarea)) {
    const rect = textarea.coordsAtIndex(index);
    if (rect) {
      return {
        left: rect.left,
        top: rect.top,
        lineHeight: rect.lineHeight,
        fontSize: rect.fontSize,
      };
    }
    return fallbackCaretRect;
  }
  if (!(textarea instanceof HTMLTextAreaElement)) return fallbackCaretRect;

  const textAreaElement = textarea as HTMLTextAreaElement;
  const styles = window.getComputedStyle(textAreaElement);
  const lineHeight = parseFloat(styles.lineHeight) || parseFloat(styles.fontSize) * 1.8 || 24;
  const fontSize = parseFloat(styles.fontSize) || 20;
  const mirror = document.createElement("div");
  [
    "box-sizing",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "letter-spacing",
    "line-height",
    "padding",
    "text-transform",
    "white-space",
    "word-break",
    "overflow-wrap",
  ].forEach((property) => {
    mirror.style.setProperty(property, styles.getPropertyValue(property));
  });
  mirror.style.position = "absolute";
  mirror.style.visibility = "hidden";
  mirror.style.left = "-9999px";
  mirror.style.top = "0";
  mirror.style.width = `${textAreaElement.clientWidth}px`;
  mirror.style.minHeight = "0";
  mirror.style.border = "0";
  mirror.style.overflow = "hidden";
  mirror.style.whiteSpace = "pre-wrap";

  mirror.textContent = textAreaElement.value.slice(0, index);
  const marker = document.createElement("span");
  marker.textContent = "\u200b";
  marker.style.display = "inline-block";
  marker.style.width = "0";
  marker.style.height = `${lineHeight}px`;
  marker.style.lineHeight = `${lineHeight}px`;
  marker.style.verticalAlign = "top";
  mirror.appendChild(marker);
  document.body.appendChild(mirror);
  const markerRect = marker.getBoundingClientRect();
  const mirrorRect = mirror.getBoundingClientRect();
  const position = {
    left: markerRect.left - mirrorRect.left,
    top: markerRect.top - mirrorRect.top,
    lineHeight,
    fontSize,
  };
  mirror.remove();
  return position;
}

export function scrollTextareaIndexIntoView(textarea: MeasurableTextEditor, index: number) {
  const caret = measureTextareaCaret(textarea, index);
  const margin = 96;
  const visibleTop = textarea.scrollTop + margin;
  const visibleBottom = textarea.scrollTop + textarea.clientHeight - margin;
  if (caret.top < visibleTop) {
    textarea.scrollTop = Math.max(0, caret.top - margin);
  } else if (caret.top > visibleBottom) {
    textarea.scrollTop = Math.max(0, caret.top - textarea.clientHeight + margin);
  }
}

export function findDocumentNode(nodes: DocumentNode[], documentId: string): DocumentNode | null {
  for (const node of nodes) {
    if (node.id === documentId) {
      return node;
    }
    const child = findDocumentNode(node.children, documentId);
    if (child) {
      return child;
    }
  }
  return null;
}

export function stringMetadata(result: ProjectSearchResult, key: string) {
  const value = result.metadata[key];
  return typeof value === "string" ? value : "";
}

export function isPromptRequestType(value: string): value is PromptRequestType {
  return [
    "perspective_suggestion",
    "polish_selection",
    "generate_next_paragraph",
    "generate_next_section",
    "polish_document_selection",
    "generate_document_continuation",
  ].includes(value);
}

export function countDraftWords(value: string) {
  const cjkCount = value.match(/[\u4e00-\u9fff]/g)?.length ?? 0;
  const latinCount =
    value.replace(/[\u4e00-\u9fff]/g, " ").match(/[A-Za-z0-9]+/g)?.length ?? 0;
  return cjkCount + latinCount;
}

export function formatCount(value: number) {
  return value.toLocaleString("zh-CN");
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function chapterDocxDownloadFilename(
  projectTitle: string,
  chapters: ChapterSummary[],
  selectedChapterIds: string[],
) {
  const selected = chapters.filter((chapter) => selectedChapterIds.includes(chapter.id));
  const suffix = selected.length === 1 ? selected[0].title : "正文";
  return `${safeDownloadName(projectTitle)}-${safeDownloadName(suffix)}.docx`;
}

export function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function safeDownloadName(value: string) {
  return value.replace(/[\\/:*?"<>|\r\n\t]+/g, "_").trim() || "novel";
}

function isWritingEditorHandle(value: unknown): value is WritingEditorHandle {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<WritingEditorHandle>;
  return (
    typeof candidate.coordsAtIndex === "function" &&
    typeof candidate.focus === "function" &&
    typeof candidate.setSelectionRange === "function" &&
    typeof candidate.setSelectionRangeWithoutScroll === "function" &&
    typeof candidate.scrollIndexIntoView === "function"
  );
}
