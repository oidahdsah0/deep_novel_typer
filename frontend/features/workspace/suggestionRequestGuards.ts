export type SuggestionResponseTrigger = "auto" | "batch" | "manual";

export function normalizeSuggestionParagraph(value: string) {
  return value.trim();
}

export function shouldApplySuggestionResponse({
  currentParagraph,
  latestAutoParagraph,
  requestedParagraph,
  trigger,
}: {
  currentParagraph: string;
  latestAutoParagraph?: string;
  requestedParagraph: string;
  trigger: SuggestionResponseTrigger;
}) {
  if (trigger !== "auto") {
    return true;
  }

  const normalizedRequested = normalizeSuggestionParagraph(requestedParagraph);
  if (!normalizedRequested) {
    return false;
  }

  return (
    normalizedRequested === normalizeSuggestionParagraph(currentParagraph) &&
    normalizedRequested === normalizeSuggestionParagraph(latestAutoParagraph ?? requestedParagraph)
  );
}
