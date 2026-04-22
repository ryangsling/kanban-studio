import type { BoardData } from "@/lib/kanban";

const readError = async (response: Response): Promise<string> => {
  const body = await response.text();
  return body || `Request failed with status ${response.status}.`;
};

export const fetchBoard = async (username: string): Promise<BoardData> => {
  const response = await fetch(`/api/board?username=${encodeURIComponent(username)}`);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as BoardData;
};

export const saveBoard = async (
  username: string,
  board: BoardData
): Promise<BoardData> => {
  const response = await fetch(`/api/board?username=${encodeURIComponent(username)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(board),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as BoardData;
};

export type ChatRole = "user" | "assistant";

export type AIChatHistoryMessage = {
  role: ChatRole;
  content: string;
};

export type AIChatRequest = {
  message: string;
  board: BoardData;
  history: AIChatHistoryMessage[];
};

export type AIChatResponse = {
  model: string;
  assistantMessage: string;
  boardUpdated: boolean;
  board: BoardData | null;
};

export const sendAIChat = async (
  username: string,
  payload: AIChatRequest
): Promise<AIChatResponse> => {
  const response = await fetch(`/api/ai/chat?username=${encodeURIComponent(username)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as AIChatResponse;
};
