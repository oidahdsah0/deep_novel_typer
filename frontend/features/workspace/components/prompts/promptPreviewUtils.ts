import type { PromptPreviewResponse } from "@/lib/api/index";

export type PromptPreviewPanel =
  | "summary"
  | "context"
  | "system"
  | "user"
  | "materials"
  | "params"
  | "warnings";

export const promptPreviewPanels: Array<{ id: PromptPreviewPanel; label: string }> = [
  { id: "summary", label: "摘要" },
  { id: "context", label: "Context" },
  { id: "system", label: "System" },
  { id: "user", label: "User" },
  { id: "materials", label: "素材" },
  { id: "params", label: "参数" },
  { id: "warnings", label: "警告" },
];

export function formatNumber(value: number) {
  return new Intl.NumberFormat("zh-CN").format(value);
}

export function formatNullableNumber(value: number | null) {
  return value === null ? "未设置" : formatNumber(value);
}

export function messagesByRole(
  item: PromptPreviewResponse["items"][number] | undefined,
  role: "system" | "user",
) {
  return (item?.messages ?? [])
    .filter((message) => message.role === role)
    .map((message) => message.content)
    .join("\n\n");
}
