export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  reasoning?: string;
};

export type ChatRequest = {
  chapter_id?: string;
  session_id?: string;
  messages: ChatMessage[];
};

export type ChatSessionSummary = {
  id: string;
  project_id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type ChatSessionWithMessages = ChatSessionSummary & {
  messages: ChatMessage[];
};

export type CreateChatSessionInput = {
  title?: string;
};

export type UpdateChatSessionInput = {
  title: string;
};
