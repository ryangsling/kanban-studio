import type { BoardData } from "@/lib/kanban";

const readError = async (response: Response): Promise<string> => {
  const body = await response.text();
  return body || `Request failed with status ${response.status}.`;
};

export type User = {
  id: number;
  username: string;
};

export type BoardListItem = {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
};

export const register = async (username: string, password: string): Promise<User> => {
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Registration failed");
  }
  return (await response.json()) as User;
};

export const login = async (username: string, password: string): Promise<User> => {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Login failed");
  }
  return (await response.json()) as User;
};

export const logout = async (): Promise<void> => {
  await fetch("/api/auth/logout", { method: "POST" });
};

export const getCurrentUser = async (): Promise<User> => {
  const response = await fetch("/api/auth/me");
  if (!response.ok) {
    throw new Error("Not authenticated");
  }
  return (await response.json()) as User;
};

export const getBoards = async (): Promise<BoardListItem[]> => {
  const response = await fetch("/api/boards");
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as BoardListItem[];
};

export const createBoard = async (name: string): Promise<BoardListItem> => {
  const response = await fetch(`/api/boards?name=${encodeURIComponent(name)}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as BoardListItem;
};

export const renameBoard = async (boardId: number, name: string): Promise<BoardListItem> => {
  const response = await fetch(`/api/boards/${boardId}?name=${encodeURIComponent(name)}`, {
    method: "PATCH",
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as BoardListItem;
};

export const fetchBoard = async (username: string): Promise<BoardData> => {
  const response = await fetch(`/api/board?username=${encodeURIComponent(username)}`);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as BoardData;
};

export const getBoard = async (boardId: number): Promise<BoardData> => {
  const response = await fetch(`/api/board/${boardId}`);
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

export const saveBoardById = async (
  boardId: number,
  board: BoardData
): Promise<BoardData> => {
  const response = await fetch(`/api/board/${boardId}`, {
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
