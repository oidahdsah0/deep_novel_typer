export function generationErrorMessage(error: unknown) {
  const message = error instanceof Error ? error.message : "生成失败";
  if (
    message.includes("schema validation failed") ||
    message.includes("valid JSON object") ||
    message.includes("non-empty text") ||
    message.includes("non-empty points")
  ) {
    return `模型返回格式不符合要求：${message}`;
  }
  return message;
}
