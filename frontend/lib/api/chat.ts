import { apiFetchEventStream } from "./client";
import { readChatEventStream } from "./chatStreamReader";
import type { ChatRequest } from "./types/index";

export async function streamChat(
  projectId: string,
  input: ChatRequest,
  onDelta: (delta: string) => void,
  onReasoningDelta: (delta: string) => void,
  onDone: (model: string) => void,
  onError: (error: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await apiFetchEventStream(
      `/api/projects/${encodeURIComponent(projectId)}/chat`,
      {
        method: "POST",
        body: JSON.stringify(input),
        signal,
      },
    );
  } catch (err) {
    if (isAbortError(err)) return;
    onError(err instanceof Error ? err.message : "网络请求失败");
    return;
  }

  if (!response.ok) {
    let message = `请求失败: ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) message = payload.detail;
    } catch {
      // keep default
    }
    onError(message);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onError("浏览器不支持流式响应");
    return;
  }

  await readChatEventStream(
    reader,
    {
      onDelta,
      onReasoningDelta,
      onDone,
      onError,
    },
    signal,
  );
}

function isAbortError(err: unknown): boolean {
  return err instanceof DOMException && err.name === "AbortError";
}
