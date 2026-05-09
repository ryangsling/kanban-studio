import hashlib
import secrets
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


def _generate_session_token() -> str:
    return secrets.token_hex(32)


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
                    owner_user_id INTEGER NOT NULL,
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
                    external_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    position INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE (board_id, external_id),
                    UNIQUE (column_id, position),
                    FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
                    FOREIGN KEY (column_id) REFERENCES board_columns(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_boards_owner_user_id ON boards(owner_user_id);
                CREATE INDEX IF NOT EXISTS idx_board_columns_board_id_position ON board_columns(board_id, position);
                CREATE INDEX IF NOT EXISTS idx_cards_board_id ON cards(board_id);
                CREATE INDEX IF NOT EXISTS idx_cards_column_id_position ON cards(column_id, position);

                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
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

        self._seed_board_columns_and_cards(conn, board_id)

    def _seed_board_columns_and_cards(self, conn: sqlite3.Connection, board_id: int) -> None:
        column_count = conn.execute(
            "SELECT COUNT(*) AS total FROM board_columns WHERE board_id = ?",
            (board_id,),
        ).fetchone()["total"]
        if column_count > 0:
            return

        created_at = _now_iso()
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

    def create_board_for_user(self, user_id: int, name: str) -> dict:
        created_at = _now_iso()
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO boards (owner_user_id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (user_id, name, created_at, created_at),
            )
            board_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            self._seed_board_columns_and_cards(conn, board_id)
        return {"id": board_id, "name": name, "created_at": created_at, "updated_at": created_at}

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

            # Avoid transient UNIQUE(board_id, position) conflicts while reordering.
            safe_offset = len(board.columns) + 1
            for position, column in enumerate(board.columns):
                conn.execute(
                    """
                    UPDATE board_columns
                    SET position = ?, updated_at = ?
                    WHERE board_id = ? AND key = ?
                    """,
                    (position + safe_offset, now, board_id, column.id),
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

    def create_user(self, username: str, password: str) -> dict:
        created_at = _now_iso()
        password_hash = _hash_password(password)
        with self._connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                    (username, password_hash, created_at),
                )
            except sqlite3.IntegrityError as e:
                if "UNIQUE" in str(e):
                    raise ValueError("Username already exists.") from e
                raise
            user_id = self._user_id_for_username(conn, username)
            conn.execute(
                "INSERT INTO boards (owner_user_id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (user_id, "My Board", created_at, created_at),
            )
            board_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            self._seed_board_columns_and_cards(conn, board_id)
        return {"id": user_id, "username": username}

    def authenticate_user(self, username: str, password: str) -> dict:
        password_hash = _hash_password(password)
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, username FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash),
            ).fetchone()
            if row is None:
                raise ValueError("Invalid username or password.")
            return {"id": row["id"], "username": row["username"]}

    def create_session(self, user_id: int) -> str:
        token = _generate_session_token()
        from datetime import timedelta
        expires_at = datetime.now(tz=UTC) + timedelta(days=1)
        expires_at_str = expires_at.isoformat()
        created_at = _now_iso()
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO sessions (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)",
                (user_id, token, expires_at_str, created_at),
            )
        return token

    def get_user_from_session(self, token: str) -> dict | None:
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT u.id, u.username
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token = ? AND s.expires_at > ?
                """,
                (token, _now_iso()),
            ).fetchone()
            if row is None:
                return None
            return {"id": row["id"], "username": row["username"]}

    def delete_session(self, token: str) -> None:
        with self._connection() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))

    def get_board_by_id(self, board_id: int, user_id: int) -> BoardData:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id FROM boards WHERE id = ? AND owner_user_id = ?",
                (board_id, user_id),
            ).fetchone()
            if row is None:
                raise ValueError("Board not found.")
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

    def save_board_by_id(self, board_id: int, user_id: int, board: BoardData) -> BoardData:
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
            row = conn.execute(
                "SELECT id FROM boards WHERE id = ? AND owner_user_id = ?",
                (board_id, user_id),
            ).fetchone()
            if row is None:
                raise ValueError("Board not found.")
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

            safe_offset = len(board.columns) + 1
            for position, column in enumerate(board.columns):
                conn.execute(
                    """
                    UPDATE board_columns
                    SET position = ?, updated_at = ?
                    WHERE board_id = ? AND key = ?
                    """,
                    (position + safe_offset, now, board_id, column.id),
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

        return self.get_board_by_id(board_id, user_id)
