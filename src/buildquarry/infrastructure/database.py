"""SQLite storage for editable plans."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class SavedPlan:
    plan_id: int
    title: str
    markdown: str
    updated_at: str


class PlanDatabase:
    def __init__(self, path: Path | None = None) -> None:
        database_path = path or self._default_path()
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                markdown TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    @staticmethod
    def _default_path() -> Path:
        return Path.home() / ".buildquarry" / "plans.sqlite3"

    def save(self, title: str, markdown: str, plan_id: int | None = None) -> int:
        now = datetime.now(timezone.utc).isoformat()
        if plan_id is None:
            cursor = self.connection.execute(
                "INSERT INTO plans (title, markdown, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (title, markdown, now, now),
            )
            saved_id = int(cursor.lastrowid)
        else:
            self.connection.execute(
                "UPDATE plans SET title = ?, markdown = ?, updated_at = ? WHERE id = ?",
                (title, markdown, now, plan_id),
            )
            saved_id = plan_id
        self.connection.commit()
        return saved_id

    def list_plans(self) -> list[SavedPlan]:
        rows = self.connection.execute(
            "SELECT id, title, markdown, updated_at FROM plans ORDER BY updated_at DESC"
        ).fetchall()
        return [
            SavedPlan(
                plan_id=int(row["id"]),
                title=row["title"],
                markdown=row["markdown"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def get(self, plan_id: int) -> SavedPlan | None:
        row = self.connection.execute(
            "SELECT id, title, markdown, updated_at FROM plans WHERE id = ?", (plan_id,)
        ).fetchone()
        if row is None:
            return None
        return SavedPlan(int(row["id"]), row["title"], row["markdown"], row["updated_at"])

    def delete(self, plan_id: int) -> None:
        self.connection.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
