# Frontend Agent Notes

## Scope

This directory contains the MVP frontend for a single-board Kanban experience. It uses local React state for board interactions and is statically exported for backend serving.

## Stack

- Next.js (App Router) + React + TypeScript
- Tailwind CSS v4 (via `@import "tailwindcss"`)
- Drag and drop via `@dnd-kit/core` + `@dnd-kit/sortable`
- Testing:
  - Unit/component: Vitest + Testing Library + jsdom
  - E2E: Playwright

## Current runtime behavior

- Route `/` renders `AppShell`, which gates access behind login.
- Login credentials are fixed to `user` / `password`.
- Authenticated users see `KanbanBoard` and can log out to return to sign-in.
- Board starts from in-memory `initialData` in `src/lib/kanban.ts`.
- User can:
  - Rename column titles inline
  - Add cards to a column
  - Remove cards
  - Drag cards within and across columns
- No API calls or persistence are currently present.

## Code map

- `src/app/page.tsx`: home page entrypoint
- `src/components/AppShell.tsx`: login gate, auth state, and logout behavior
- `src/components/KanbanBoard.tsx`: board-level state and DnD orchestration
- `src/components/KanbanColumn.tsx`: droppable column with rename input and card list
- `src/components/KanbanCard.tsx`: sortable card item with remove action
- `src/components/NewCardForm.tsx`: add-card form UI/logic
- `src/components/KanbanCardPreview.tsx`: drag overlay card preview
- `src/lib/kanban.ts`: board/card types, seeded data, move logic, ID generation

## Styling and design tokens

Global styles are in `src/app/globals.css` and include tokens matching project colors:
- Accent Yellow `#ecad0a`
- Blue Primary `#209dd7`
- Purple Secondary `#753991`
- Dark Navy `#032147`
- Gray Text `#888888`

## Test baseline

- Unit/component tests:
  - `src/components/AppShell.test.tsx` validates auth gate transitions
  - `src/lib/kanban.test.ts` validates card movement logic
  - `src/components/KanbanBoard.test.tsx` validates render, rename, add/remove flows
- E2E tests:
  - `tests/kanban.spec.ts` validates login, logout, board load, add-card, and drag between columns

## Commands

- Dev: `npm run dev`
- Unit: `npm run test:unit`
- E2E: `npm run test:e2e`
- Full test pass: `npm run test:all`
