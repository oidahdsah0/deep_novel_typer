type ChatStreamHandlers = {
  onDelta: (delta: string) => void;
  onReasoningDelta: (delta: string) => void;
  onDone: (model: string) => void;
  onError: (error: string) => void;
};

export async function readChatEventStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const decoder = new TextDecoder();
  let buffer = "";
  let doneReceived = false;
  const cancelReader = () => {
    void reader.cancel().catch(() => undefined);
  };
  signal?.addEventListener("abort", cancelReader, { once: true });

  try {
    while (true) {
      if (signal?.aborted) return;
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith("data: ")) continue;
        const payload = trimmed.slice(6);
        if (payload === "[DONE]") {
          if (!doneReceived) {
            doneReceived = true;
            handlers.onDone("unknown");
          }
          continue;
        }
        try {
          const event = JSON.parse(payload) as {
            delta?: string;
            error?: string | { message?: string };
            reasoning_delta?: string;
          };
          if (event.error) {
            handlers.onError(errorMessage(event.error));
            return;
          }
          if (event.reasoning_delta) {
            handlers.onReasoningDelta(event.reasoning_delta);
          }
          if (event.delta) {
            handlers.onDelta(event.delta);
          }
        } catch {
          // skip malformed JSON lines
        }
      }
    }
    if (!doneReceived) {
      handlers.onError("流式响应未完成，消息可能未保存");
    }
  } catch (err) {
    if (isAbortError(err) || signal?.aborted) return;
    handlers.onError(err instanceof Error ? err.message : "流式响应中断");
  } finally {
    signal?.removeEventListener("abort", cancelReader);
    try {
      reader.releaseLock();
    } catch {
      // reader may already be released after cancellation
    }
  }
}

function isAbortError(err: unknown): boolean {
  return err instanceof DOMException && err.name === "AbortError";
}

function errorMessage(error: string | { message?: string }): string {
  if (typeof error === "string" && error.trim()) return error;
  if (typeof error === "object" && error.message?.trim()) return error.message;
  return "流式响应中断";
}
