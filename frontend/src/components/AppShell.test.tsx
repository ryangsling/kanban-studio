import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { initialData } from "@/lib/kanban";
import { AppShell } from "@/components/AppShell";

const okResponse = (body: unknown) =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

const signIn = async (username: string, password: string) => {
  await userEvent.type(screen.getByLabelText(/username/i), username);
  await userEvent.type(screen.getByLabelText(/password/i), password);
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
};

const cloneBoard = () => JSON.parse(JSON.stringify(initialData));

describe("AppShell auth gate", () => {
  beforeEach(() => {
    window.localStorage.clear();
    let boardState = cloneBoard();
    global.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (typeof input === "string" && input.startsWith("/api/board")) {
        if (init?.method === "PUT") {
          boardState = JSON.parse(init.body as string);
          return okResponse(boardState);
        }
        return okResponse(boardState);
      }
      if (typeof input === "string" && input.startsWith("/api/ai/chat")) {
        return okResponse({
          model: "openai/gpt-oss-120b:free",
          assistantMessage: "No board update needed.",
          boardUpdated: false,
          board: null,
        });
      }
      return new Response("not found", { status: 404 });
    }) as typeof fetch;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows login before board", () => {
    render(<AppShell />);

    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: /kanban studio/i })
    ).not.toBeInTheDocument();
  });

  it("rejects invalid credentials", async () => {
    render(<AppShell />);
    await signIn("wrong", "nope");

    expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: /kanban studio/i })
    ).not.toBeInTheDocument();
  });

  it("allows valid login and logout", async () => {
    render(<AppShell />);
    await signIn("user", "password");

    expect(
      await screen.findByRole("heading", { name: /kanban studio/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
  });

  it("shows ai response and applies returned board update", async () => {
    global.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (typeof input === "string" && input.startsWith("/api/board")) {
        return okResponse(initialData);
      }
      if (typeof input === "string" && input.startsWith("/api/ai/chat")) {
        const boardWithRename = cloneBoard();
        boardWithRename.columns[0].title = "Roadmap";
        return okResponse({
          model: "openai/gpt-oss-120b:free",
          assistantMessage: "Updated backlog to Roadmap.",
          boardUpdated: true,
          board: boardWithRename,
        });
      }
      return new Response("not found", { status: 404 });
    }) as typeof fetch;

    render(<AppShell />);
    await signIn("user", "password");

    await userEvent.type(
      await screen.findByLabelText(/message/i),
      "Rename Backlog to Roadmap"
    );
    await userEvent.click(screen.getByRole("button", { name: /^send$/i }));

    expect(await screen.findByText("Updated backlog to Roadmap.")).toBeInTheDocument();
    expect(await screen.findByText("Roadmap")).toBeInTheDocument();
  });
});
