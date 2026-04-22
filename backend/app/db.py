import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from app.kanban_seed import SEED_BOARD
from app.schemas import BoardData


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class BoardStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        with self._connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS boards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_user_id INTEGER NOT NULL UNIQUE,
                    name TEXT NOT NULL DEFAULT 'My Board',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS board_columns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE (board_id, key),
                    UNIQUE (board_id, position),
                    FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    board_id INTEGER NOT NULL,
                    column_id INTEGER NOT NULL,
                    external_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    position INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE (column_id, position),
                    FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
                    FOREIGN KEY (column_id) REFERENCES board_columns(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_boards_owner_user_id ON boards(owner_user_id);
                CREATE INDEX IF NOT EXISTS idx_board_columns_board_id_position ON board_columns(board_id, position);
                CREATE INDEX IF NOT EXISTS idx_cards_board_id ON cards(board_id);
                CREATE INDEX IF NOT EXISTS idx_cards_column_id_position ON cards(column_id, position);
                """
            )
            self._seed_default_user_board(conn)

    def _seed_default_user_board(self, conn: sqlite3.Connection) -> None:
        created_at = _now_iso()
        conn.execute(
            """
            INSERT INTO users (username, password_hash, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(username) DO NOTHING
            """,
            ("user", _hash_password("password"), created_at),
        )
        user_id = self._user_id_for_username(conn, "user")
        board_row = conn.execute(
            "SELECT id FROM boards WHERE owner_user_id = ?",
            (user_id,),
        ).fetchone()
        if board_row is None:
            conn.execute(
                """
                INSERT INTO boards (owner_user_id, name, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, "My Board", created_at, created_at),
            )
            board_id = conn.execute(
                "SELECT id FROM boards WHERE owner_user_id = ?",
                (user_id,),
            ).fetchone()["id"]
        else:
            board_id = board_row["id"]

        column_count = conn.execute(
            "SELECT COUNT(*) AS total FROM board_columns WHERE board_id = ?",
            (board_id,),
        ).fetchone()["total"]
        if column_count > 0:
            return

        for position, column in enumerate(SEED_BOARD.columns):
            conn.execute(
                """
                INSERT INTO board_columns (board_id, key, title, position, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (board_id, column.id, column.title, position, created_at, created_at),
            )

        column_rows = conn.execute(
            "SELECT id, key FROM board_columns WHERE board_id = ?",
            (board_id,),
        ).fetchall()
        column_ids_by_key = {row["key"]: row["id"] for row in column_rows}

        for column_position, column in enumerate(SEED_BOARD.columns):
            column_id = column_ids_by_key[column.id]
            for card_position, card_id in enumerate(column.cardIds):
                card = SEED_BOARD.cards[card_id]
                conn.execute(
                    """
                    INSERT INTO cards (
                        board_id, column_id, external_id, title, details, position, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        board_id,
                        column_id,
                        card.id,
                        card.title,
                        card.details,
                        card_position,
                        created_at,
                        created_at,
                    ),
                )

    def _user_id_for_username(self, conn: sqlite3.Connection, username: str) -> int:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None:
            raise ValueError("Unknown user.")
        return int(row["id"])

    def _board_id_for_username(self, conn: sqlite3.Connection, username: str) -> int:
        row = conn.execute(
            """
            SELECT b.id
            FROM boards b
            JOIN users u ON u.id = b.owner_user_id
            WHERE u.username = ?
            """,
            (username,),
        ).fetchone()
        if row is None:
            raise ValueError("Board not found for user.")
        return int(row["id"])

    def get_board(self, username: str) -> BoardData:
        with self._connection() as conn:
            board_id = self._board_id_for_username(conn, username)
            columns = conn.execute(
                """
                SELECT key, title
                FROM board_columns
                WHERE board_id = ?
                ORDER BY position ASC
                """,
                (board_id,),
            ).fetchall()
            cards = conn.execute(
                """
                SELECT c.external_id, c.title, c.details, bc.key AS column_key
                FROM cards c
                JOIN board_columns bc ON bc.id = c.column_id
                WHERE c.board_id = ?
                ORDER BY bc.position ASC, c.position ASC
                """,
                (board_id,),
            ).fetchall()

        board_columns = [
            {"id": row["key"], "title": row["title"], "cardIds": []} for row in columns
        ]
        cards_by_id: dict[str, dict[str, str]] = {}
        column_lookup = {column["id"]: column for column in board_columns}

        for row in cards:
            card_id = row["external_id"]
            cards_by_id[card_id] = {
                "id": card_id,
                "title": row["title"],
                "details": row["details"],
            }
            column_lookup[row["column_key"]]["cardIds"].append(card_id)

        return BoardData(columns=board_columns, cards=cards_by_id)

    def save_board(self, username: str, board: BoardData) -> BoardData:
        column_ids = [column.id for column in board.columns]
        if len(set(column_ids)) != len(column_ids):
            raise ValueError("Duplicate column ids are not allowed.")

        seen_card_ids: list[str] = []
        for column in board.columns:
            seen_card_ids.extend(column.cardIds)

        if len(set(seen_card_ids)) != len(seen_card_ids):
            raise ValueError("A card cannot appear in multiple positions.")

        if set(seen_card_ids) != set(board.cards.keys()):
            raise ValueError("Column cardIds must match the cards map keys.")

        with self._connection() as conn:
            board_id = self._board_id_for_username(conn, username)
            column_rows = conn.execute(
                "SELECT id, key FROM board_columns WHERE board_id = ?",
                (board_id,),
            ).fetchall()
            column_id_map = {row["key"]: row["id"] for row in column_rows}
            if set(column_id_map.keys()) != set(column_ids):
                raise ValueError("Board must include the expected fixed columns.")

            now = _now_iso()
            conn.execute(
                "UPDATE boards SET updated_at = ? WHERE id = ?",
                (now, board_id),
            )

            for position, column in enumerate(board.columns):
                conn.execute(
                    """
                    UPDATE board_columns
                    SET title = ?, position = ?, updated_at = ?
                    WHERE board_id = ? AND key = ?
                    """,
                    (column.title, position, now, board_id, column.id),
                )

            conn.execute("DELETE FROM cards WHERE board_id = ?", (board_id,))

            for column in board.columns:
                column_db_id = column_id_map[column.id]
                for position, card_id in enumerate(column.cardIds):
                    card = board.cards[card_id]
                    conn.execute(
                        """
                        INSERT INTO cards (
                            board_id, column_id, external_id, title, details, position, created_at, updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            board_id,
                            column_db_id,
                            card.id,
                            card.title,
                            card.details,
                            position,
                            now,
                            now,
                        ),
                    )

        return self.get_board(username)
