import assert from "node:assert/strict";
import test from "node:test";

import { readChatEventStream } from "../lib/api/chatStreamReader";

type CapturedEvents = {
  deltas: string[];
  done: string[];
  errors: string[];
  reasoning: string[];
};

test("chat stream reader emits deltas and done for a completed stream", async () => {
  const events = await readEvents([
    'data: {"delta":"你"}\n\n',
    'data: {"reasoning_delta":"想"}\n\n',
    'data: {"delta":"好"}\n\n',
    "data: [DONE]\n\n",
  ]);

  assert.deepEqual(events.deltas, ["你", "好"]);
  assert.deepEqual(events.reasoning, ["想"]);
  assert.deepEqual(events.done, ["unknown"]);
  assert.deepEqual(events.errors, []);
});

test("stream close without DONE reports an error", async () => {
  const events = await readEvents(['data: {"delta":"半截回复"}\n\n']);

  assert.deepEqual(events.deltas, ["半截回复"]);
  assert.deepEqual(events.done, []);
  assert.deepEqual(events.errors, ["流式响应未完成，消息可能未保存"]);
});

test("error events report an error instead of falling through to done", async () => {
  const events = await readEvents([
    'data: {"delta":"半截回复"}\n\n',
    'data: {"error":"模型连接中断"}\n\n',
  ]);

  assert.deepEqual(events.deltas, ["半截回复"]);
  assert.deepEqual(events.done, []);
  assert.deepEqual(events.errors, ["模型连接中断"]);
});

test("chat stream reader ignores user abort without success or error callbacks", async () => {
  const controller = new AbortController();
  controller.abort();
  const events = await readEvents(['data: {"delta":"不会读取"}\n\n'], controller.signal);

  assert.deepEqual(events.deltas, []);
  assert.deepEqual(events.reasoning, []);
  assert.deepEqual(events.done, []);
  assert.deepEqual(events.errors, []);
});

async function readEvents(chunks: string[], signal?: AbortSignal): Promise<CapturedEvents> {
  const events: CapturedEvents = {
    deltas: [],
    done: [],
    errors: [],
    reasoning: [],
  };

  await readChatEventStream(
    readerFromChunks(chunks),
    {
      onDelta: (delta) => events.deltas.push(delta),
      onReasoningDelta: (delta) => events.reasoning.push(delta),
      onDone: (model) => events.done.push(model),
      onError: (error) => events.errors.push(error),
    },
    signal,
  );

  return events;
}

function readerFromChunks(chunks: string[]): ReadableStreamDefaultReader<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  }).getReader();
}
