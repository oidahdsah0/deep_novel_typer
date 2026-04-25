import assert from "node:assert/strict";
import test from "node:test";

import { shouldApplySuggestionResponse } from "../features/workspace/suggestionRequestGuards";

test("auto suggestion responses apply only to the latest current paragraph", () => {
  assert.equal(
    shouldApplySuggestionResponse({
      currentParagraph: "新段落",
      latestAutoParagraph: "新段落",
      requestedParagraph: "旧段落",
      trigger: "auto",
    }),
    false,
  );

  assert.equal(
    shouldApplySuggestionResponse({
      currentParagraph: "新段落",
      latestAutoParagraph: "新段落",
      requestedParagraph: "新段落",
      trigger: "auto",
    }),
    true,
  );
});

test("manual suggestion responses are always allowed to apply", () => {
  assert.equal(
    shouldApplySuggestionResponse({
      currentParagraph: "新段落",
      latestAutoParagraph: "新段落",
      requestedParagraph: "旧段落",
      trigger: "manual",
    }),
    true,
  );
});
