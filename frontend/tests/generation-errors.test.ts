import assert from "node:assert/strict";
import test from "node:test";

import { generationErrorMessage } from "../features/workspace/generationErrors";

test("generation error message highlights schema validation failures", () => {
  assert.equal(
    generationErrorMessage(new Error("response must contain non-empty points")),
    "模型返回格式不符合要求：response must contain non-empty points",
  );
});

test("generation error message keeps regular errors unchanged", () => {
  assert.equal(generationErrorMessage(new Error("network failed")), "network failed");
});
