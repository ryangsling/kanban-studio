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
