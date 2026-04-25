import type {
  DocumentNode,
  PromptProfileVersion,
  ResourceVersion,
} from "@/lib/api/index";
import type { DraftInsertionContext, PromptMaterialOption } from "./types";

export function formatMaterialSource(source: string) {
  return source
    .split("+")
    .map((item) => {
      if (item === "recent") {
        return "最近章节";
      }
      if (item === "fixed") {
        return "固定选取";
      }
      return item || "素材";
    })
    .join(" + ");
}

export function appendGeneratedText(current: string, generated: string) {
  const trimmedCurrent = current.trimEnd();
  const trimmedGenerated = generated.trim();
  if (!trimmedGenerated) {
    return current;
  }
  return trimmedCurrent ? `${trimmedCurrent}\n\n${trimmedGenerated}\n` : `${trimmedGenerated}\n`;
}

export function appendGeneratedTextWithRange(current: string, generated: string) {
  const trimmedCurrent = current.trimEnd();
  const trimmedGenerated = generated.trim();
  if (!trimmedGenerated) {
    return null;
  }

  const prefix = trimmedCurrent ? `${trimmedCurrent}\n\n` : "";
  const nextContent = `${prefix}${trimmedGenerated}\n`;
  return {
    end: prefix.length + trimmedGenerated.length,
    nextContent,
    start: prefix.length,
  };
}

export function insertGeneratedTextWithRange(
  current: string,
  generated: string,
  cursorIndex: number,
) {
  const trimmedGenerated = generated.trim();
  if (!trimmedGenerated) {
    return null;
  }

  const safeIndex = clamp(Math.trunc(cursorIndex), 0, current.length);
  const prefix = current.slice(0, safeIndex).trimEnd();
  const suffix = current.slice(safeIndex).trimStart();
  const beforeGenerated = prefix ? `${prefix}\n\n` : "";
  const afterGenerated = suffix ? `\n\n${suffix}` : "\n";
  const nextContent = `${beforeGenerated}${trimmedGenerated}${afterGenerated}`;
  return {
    end: beforeGenerated.length + trimmedGenerated.length,
    nextContent,
    start: beforeGenerated.length,
  };
}

export function renderChapterBlueprintPoints(points: string[]) {
  return points
    .map((point) => {
      const normalized = point.trim().split(/\s+/).join(" ");
      return normalized ? `「 ${normalized} 」` : "";
    })
    .filter(Boolean)
    .join("\n");
}

export function draftInsertionContextAt(
  content: string,
  cursorIndex: number,
): DraftInsertionContext {
  const safeIndex = clamp(Math.trunc(cursorIndex), 0, content.length);
  const ranges = nonEmptyParagraphRanges(content);
  const containingIndex = ranges.findIndex(
    (range) => range.start <= safeIndex && safeIndex <= range.end,
  );

  if (containingIndex >= 0) {
    const containing = ranges[containingIndex];
    const previousParagraph =
      safeIndex > containing.start
        ? content.slice(containing.start, safeIndex).trim()
        : ranges[containingIndex - 1]?.text ?? "";
    const nextParagraph =
      safeIndex < containing.end
        ? content.slice(safeIndex, containing.end).trim()
        : ranges[containingIndex + 1]?.text ?? "";
    return {
      cursorIndex: safeIndex,
      previousParagraph,
      nextParagraph,
    };
  }

  const previousParagraph =
    [...ranges].reverse().find((range) => range.end <= safeIndex)?.text ?? "";
  const nextParagraph = ranges.find((range) => range.start >= safeIndex)?.text ?? "";
  return {
    cursorIndex: safeIndex,
    previousParagraph,
    nextParagraph,
  };
}

export function flattenDocumentOptions(nodes: DocumentNode[], path: string[] = []): PromptMaterialOption[] {
  return nodes.flatMap((node) => {
    const nextPath = [...path, node.title];
    const children = flattenDocumentOptions(node.children, nextPath);
    if (node.type !== "markdown") {
      return children;
    }
    return [
      {
        id: node.id,
        title: node.title,
        meta: nextPath.join(" / "),
      },
      ...children,
    ];
  });
}

export function toggleId(ids: string[], id: string) {
  return ids.includes(id) ? ids.filter((item) => item !== id) : [...ids, id];
}

export function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function nonEmptyParagraphRanges(value: string) {
  const ranges: Array<{ start: number; end: number; text: string }> = [];
  const paragraphPattern = /[^\n]+/g;
  for (const match of value.matchAll(paragraphPattern)) {
    const raw = match[0];
    const rawStart = match.index ?? 0;
    const leadingWhitespace = raw.match(/^\s*/)?.[0].length ?? 0;
    const trailingWhitespace = raw.match(/\s*$/)?.[0].length ?? 0;
    const start = rawStart + leadingWhitespace;
    const end = rawStart + raw.length - trailingWhitespace;
    if (start < end) {
      ranges.push({ start, end, text: value.slice(start, end) });
    }
  }
  return ranges;
}

export function versionTypeLabel(type: ResourceVersion["version_type"]) {
  const labels: Record<ResourceVersion["version_type"], string> = {
    manual: "手动版本",
    auto: "自动版本",
    initial: "初始版本",
    pre_action: "操作前备份",
    pre_restore: "恢复前备份",
  };
  return labels[type];
}

export function promptProfileVersionTypeLabel(type: PromptProfileVersion["version_type"]) {
  const labels: Record<PromptProfileVersion["version_type"], string> = {
    manual: "手动保存",
    initial: "初始配置",
    pre_restore: "恢复前备份",
  };
  return labels[type];
}

export function formatDate(value: string) {
  return new Date(value).toLocaleDateString("zh-CN");
}

export function formatDateTime(value: string) {
  return new Date(value).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
