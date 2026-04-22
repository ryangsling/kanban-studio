# Database approach (Part 5 proposal)

This document defines the proposed SQLite model for MVP persistence. The canonical schema artifact is `docs/schema.json`.

## Design summary

1. `users` stores credentials (hashed password) and supports future multi-user.
2. `boards` maps board ownership to a user; MVP enforces one board per user via unique `owner_user_id`.
3. `board_columns` stores editable column titles and stable internal keys, with explicit order (`position`).
4. `cards` stores card content and order (`position`) within a specific column.

## Why this model

- Supports MVP requirements directly:
  - fixed columns that can be renamed
  - card edits
  - drag-and-drop reorder within/across columns
- Keeps ordering deterministic via integer `position`.
- Uses explicit foreign keys with `ON DELETE CASCADE` for clean board/user removal.
- Keeps migration path clear:
  - to support multiple boards per user later, remove/relax unique constraint on `boards.owner_user_id`.

## Operational notes for Part 6

- Enable SQLite foreign keys (`PRAGMA foreign_keys = ON`).
- Reorder operations should run in a transaction to avoid temporary uniqueness conflicts on `(column_id, position)`.
- Seed one user (`user`) and one board with five default columns on first run if DB is empty.

## Sign-off checkpoint

If approved, this schema will be implemented in Part 6 as migration/init SQL plus data-access layer models.
