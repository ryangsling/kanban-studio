"use client";

import { FormEvent } from "react";
import type { AIChatHistoryMessage } from "@/lib/api";

type AiSidebarProps = {
  history: AIChatHistoryMessage[];
  draft: string;
  onDraftChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  error: string;
  disabled: boolean;
};

export const AiSidebar = ({
  history,
  draft,
  onDraftChange,
  onSubmit,
  isLoading,
  error,
  disabled,
}: AiSidebarProps) => {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <aside
      className="border-t border-[var(--stroke)] bg-white lg:fixed lg:right-4 lg:top-[72px] lg:z-30 lg:h-[min(48vh,420px)] lg:w-[360px] lg:overflow-hidden lg:rounded-xl lg:border lg:shadow-[var(--shadow)]"
      data-testid="ai-sidebar"
    >
      <div className="flex h-full flex-col">
        <header className="border-b border-[var(--stroke)] px-3 py-2.5">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            AI Assistant
          </p>
          <p className="mt-1 text-sm font-semibold text-[var(--navy-dark)]">
            Create, move, and edit cards from chat.
          </p>
        </header>

        <div className="flex-1 space-y-2 overflow-y-auto px-2 py-2">
          {history.length === 0 ? (
            <p className="rounded-xl border border-dashed border-[var(--stroke)] bg-[var(--surface)] px-2.5 py-2 text-sm text-[var(--gray-text)]">
              Ask for board updates like moving cards, renaming columns, or drafting new tasks.
            </p>
          ) : (
            history.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={message.role === "user" ? "flex justify-end" : "flex justify-start"}
              >
                <div
                  className={
                    message.role === "user"
                      ? "max-w-[95%] rounded-xl bg-[var(--primary-blue)] px-2.5 py-1.5 text-sm text-white"
                      : "max-w-[95%] rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-2.5 py-1.5 text-sm text-[var(--navy-dark)]"
                  }
                >
                  {message.content}
                </div>
              </div>
            ))
          )}
        </div>

        <form className="border-t border-[var(--stroke)] px-3 py-2" onSubmit={handleSubmit}>
          <label
            htmlFor="ai-message"
            className="mb-1 block text-xs font-semibold uppercase tracking-[0.15em] text-[var(--gray-text)]"
          >
            Message
          </label>
          <textarea
            id="ai-message"
            value={draft}
            onChange={(event) => onDraftChange(event.target.value)}
            placeholder="Move card-1 to Review and summarize priorities."
            className="h-12 w-full resize-none rounded-xl border border-[var(--stroke)] bg-white px-2.5 py-1.5 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            disabled={disabled || isLoading}
          />
          {error ? (
            <p className="mt-1.5 text-sm font-medium text-[var(--secondary-purple)]">{error}</p>
          ) : null}
          <button
            type="submit"
            className="mt-2 w-full rounded-full bg-[var(--secondary-purple)] px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-white transition enabled:hover:brightness-110 disabled:opacity-60"
            disabled={disabled || isLoading || draft.trim().length === 0}
          >
            {isLoading ? "Sending..." : "Send"}
          </button>
        </form>
      </div>
    </aside>
  );
};
