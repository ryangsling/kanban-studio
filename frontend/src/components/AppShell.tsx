"use client";

import { FormEvent, useEffect, useState } from "react";
import { AiSidebar } from "@/components/AiSidebar";
import { KanbanBoard } from "@/components/KanbanBoard";
import type { BoardData } from "@/lib/kanban";
import {
  register,
  login,
  logout,
  getCurrentUser,
  getBoards,
  createBoard,
  renameBoard,
  getBoard,
  saveBoardById,
  sendAIChat,
  type AIChatHistoryMessage,
} from "@/lib/api";

type AuthMode = "login" | "register";

export const AppShell = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [isLoading, setIsLoading] = useState(true);
  const [boards, setBoards] = useState<{ id: number; name: string }[]>([]);
  const [currentBoardId, setCurrentBoardId] = useState<number | null>(null);
  const [board, setBoard] = useState<BoardData | null>(null);
  const [boardLoading, setBoardLoading] = useState(false);
  const [boardError, setBoardError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [chatHistory, setChatHistory] = useState<AIChatHistoryMessage[]>([]);
  const [chatDraft, setChatDraft] = useState("");
  const [chatError, setChatError] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [editingBoardId, setEditingBoardId] = useState<number | null>(null);
  const [editingBoardName, setEditingBoardName] = useState("");

  const checkAuth = async () => {
    try {
      await getCurrentUser();
      return true;
    } catch {
      return false;
    }
  };

  useEffect(() => {
    const init = async () => {
      const authenticated = await checkAuth();
      if (!authenticated) {
        setIsLoading(false);
        return;
      }
      await loadBoards();
      setIsLoading(false);
    };
    void init();
  }, []);

  const loadBoards = async () => {
    try {
      const boardList = await getBoards();
      setBoards(boardList);
      if (boardList.length > 0 && !currentBoardId) {
        setCurrentBoardId(boardList[0].id);
      }
    } catch (err) {
      console.error("Failed to load boards:", err);
    }
  };

  useEffect(() => {
    if (currentBoardId === null) {
      return;
    }

    let isCurrent = true;
    setBoardLoading(true);
    setBoardError("");

    const loadBoard = async () => {
      try {
        const boardData = await getBoard(currentBoardId);
        if (isCurrent) {
          setBoard(boardData);
        }
      } catch (error: unknown) {
        if (isCurrent) {
          setBoardError(
            error instanceof Error ? error.message : "Failed to load board."
          );
        }
      } finally {
        if (isCurrent) {
          setBoardLoading(false);
        }
      }
    };

    void loadBoard();

    return () => {
      isCurrent = false;
    };
  }, [currentBoardId]);

  const handleAuth = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    try {
      if (authMode === "register") {
        await register(username, password);
        setAuthMode("login");
        setError("Registration successful! Please log in.");
      } else {
        await login(username, password);
        await loadBoards();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // Ignore logout errors
    }
    setUsername("");
    setPassword("");
    setError("");
    setBoard(null);
    setBoards([]);
    setCurrentBoardId(null);
  };

  const handleCreateBoard = async () => {
    try {
      const newBoard = await createBoard("New Board");
      setBoards((prev) => [newBoard, ...prev]);
      setCurrentBoardId(newBoard.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create board");
    }
  };

  const handleStartRename = (boardId: number, currentName: string) => {
    setEditingBoardId(boardId);
    setEditingBoardName(currentName);
  };

  const handleRenameBoard = async () => {
    if (editingBoardId === null || !editingBoardName.trim()) return;
    try {
      const updated = await renameBoard(editingBoardId, editingBoardName);
      setBoards((prev) => prev.map((b) => (b.id === editingBoardId ? updated : b)));
      setEditingBoardId(null);
      setEditingBoardName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to rename board");
    }
  };

  const handleBoardChange = async (nextBoard: BoardData) => {
    if (currentBoardId === null) return;
    setBoard(nextBoard);
    setIsSaving(true);
    setBoardError("");
    try {
      const persistedBoard = await saveBoardById(currentBoardId, nextBoard);
      setBoard(persistedBoard);
    } catch (error: unknown) {
      setBoardError(
        error instanceof Error ? error.message : "Failed to persist board."
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleChatSubmit = async () => {
    const message = chatDraft.trim();
    if (!message || !board || chatLoading) {
      return;
    }

    const historySnapshot = chatHistory;
    const boardSnapshot = board;

    setChatDraft("");
    setChatError("");
    setChatLoading(true);
    setChatHistory((current) => [...current, { role: "user", content: message }]);

    try {
      const response = await sendAIChat(username || "user", {
        message,
        board: boardSnapshot,
        history: historySnapshot,
      });
      setChatHistory((current) => [
        ...current,
        { role: "assistant", content: response.assistantMessage },
      ]);
      if (response.boardUpdated && response.board) {
        setBoard(response.board);
      }
    } catch (error: unknown) {
      setChatError(
        error instanceof Error ? error.message : "Failed to contact AI assistant."
      );
    } finally {
      setChatLoading(false);
    }
  };

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)]">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
          Loading...
        </p>
      </main>
    );
  }

  if (!currentBoardId) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6">
        <section className="w-full max-w-md rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
            PM MVP
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
            {authMode === "register" ? "Create Account" : "Welcome Back"}
          </h1>
          <form className="mt-6 space-y-4" onSubmit={handleAuth}>
            <div>
              <label
                className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
                htmlFor="username"
              >
                Username
              </label>
              <input
                id="username"
                name="username"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                required
                minLength={3}
              />
            </div>
            <div>
              <label
                className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
                htmlFor="password"
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                required
                minLength={6}
              />
            </div>
            {error ? (
              <p className="text-sm font-medium text-[var(--secondary-purple)]">{error}</p>
            ) : null}
            <button
              type="submit"
              className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:brightness-110"
            >
              {authMode === "register" ? "Create Account" : "Sign In"}
            </button>
          </form>
          <p className="mt-4 text-center text-sm text-[var(--gray-text)]">
            {authMode === "register" ? (
              <>
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => setAuthMode("login")}
                  className="text-[var(--primary-blue)] hover:underline"
                >
                  Sign in
                </button>
              </>
            ) : (
              <>
                Don't have an account?{" "}
                <button
                  type="button"
                  onClick={() => setAuthMode("register")}
                  className="text-[var(--primary-blue)] hover:underline"
                >
                  Create one
                </button>
              </>
            )}
          </p>
        </section>
      </main>
    );
  }

  return (
    <div>
      <div className="sticky top-0 z-20 border-b border-[var(--stroke)] bg-white/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-[1500px] items-center justify-between px-6 py-3">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Board:
            </p>
            {editingBoardId === currentBoardId ? (
              <div className="flex items-center gap-1">
                <input
                  type="text"
                  value={editingBoardName}
                  onChange={(e) => setEditingBoardName(e.target.value)}
                  className="rounded border border-[var(--stroke)] px-2 py-1 text-sm"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleRenameBoard();
                    if (e.key === "Escape") setEditingBoardId(null);
                  }}
                />
                <button
                  type="button"
                  onClick={handleRenameBoard}
                  className="text-xs text-[var(--primary-blue)]"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => setEditingBoardId(null)}
                  className="text-xs text-[var(--gray-text)]"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <>
                <select
                  value={currentBoardId ?? ""}
                  onChange={(e) => setCurrentBoardId(Number(e.target.value))}
                  className="rounded border border-[var(--stroke)] px-2 py-1 text-sm"
                >
                  {boards.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => {
                    const board = boards.find((b) => b.id === currentBoardId);
                    if (board) handleStartRename(board.id, board.name);
                  }}
                  className="text-xs text-[var(--gray-text)] hover:text-[var(--primary-blue)]"
                  title="Rename board"
                >
                  ✏️
                </button>
                <button
                  type="button"
                  onClick={handleCreateBoard}
                  className="rounded-full border border-[var(--stroke)] px-3 py-1 text-xs font-semibold uppercase tracking-[0.15em] text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
                >
                  + New
                </button>
              </>
            )}
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.15em] text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
          >
            Log out
          </button>
        </div>
      </div>
      {boardLoading ? (
        <main className="mx-auto flex min-h-[70vh] max-w-[1500px] items-center justify-center px-6">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Loading board...
          </p>
        </main>
      ) : board ? (
        <>
          <KanbanBoard
            board={board}
            onBoardChange={handleBoardChange}
            isSaving={isSaving}
            saveError={boardError}
          />
          <AiSidebar
            history={chatHistory}
            draft={chatDraft}
            onDraftChange={setChatDraft}
            onSubmit={handleChatSubmit}
            isLoading={chatLoading}
            error={chatError}
            disabled={boardLoading || isSaving}
          />
        </>
      ) : (
        <main className="mx-auto flex min-h-[70vh] max-w-[1500px] items-center justify-center px-6">
          <p className="text-sm font-semibold text-[var(--secondary-purple)]">
            {boardError || "Board unavailable."}
          </p>
        </main>
      )}
    </div>
  );
};