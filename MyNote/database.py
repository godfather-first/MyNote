"""SQLite persistence for MyNote.

The database is stored locally as tasks.db in the application directory.
On Android, Kivy maps this directory into the app sandbox, so no server or
network access is required.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path

from models import Task


class TaskDatabase:
    """Small SQLite wrapper for task CRUD operations."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            db_path = str(Path(__file__).resolve().parent / "tasks.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_table()
        self._migrate_schema()

    def _create_table(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                status INTEGER DEFAULT 0,
                create_time TEXT NOT NULL,
                update_time TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def _migrate_schema(self) -> None:
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(tasks)").fetchall()
        }
        if "due_date" not in columns:
            self.connection.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT DEFAULT ''")
            self.connection.commit()

    def add_task(self, title: str, content: str = "", due_date: str = "") -> int:
        now = self._now()
        cursor = self.connection.execute(
            """
            INSERT INTO tasks (title, content, status, create_time, update_time, due_date)
            VALUES (?, ?, 0, ?, ?, ?)
            """,
            (title, content, now, now, due_date),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def get_tasks(self) -> list[Task]:
        rows = self.connection.execute(
            """
            SELECT id, title, content, status, create_time, update_time, due_date
            FROM tasks
            ORDER BY id DESC
            """
        ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def get_task(self, task_id: int) -> Task | None:
        row = self.connection.execute(
            """
            SELECT id, title, content, status, create_time, update_time, due_date
            FROM tasks
            WHERE id = ?
            """,
            (task_id,),
        ).fetchone()
        return self._row_to_task(row) if row else None

    def update_task(
        self,
        task_id: int,
        title: str,
        content: str,
        due_date: str,
        status: int,
    ) -> None:
        self.connection.execute(
            """
            UPDATE tasks
            SET title = ?, content = ?, due_date = ?, status = ?, update_time = ?
            WHERE id = ?
            """,
            (title, content, due_date, status, self._now(), task_id),
        )
        self.connection.commit()

    def set_status(self, task_id: int, status: int) -> None:
        self.connection.execute(
            "UPDATE tasks SET status = ?, update_time = ? WHERE id = ?",
            (status, self._now(), task_id),
        )
        self.connection.commit()

    def delete_task(self, task_id: int) -> None:
        self.connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            content=row["content"] or "",
            status=int(row["status"]),
            create_time=row["create_time"],
            update_time=row["update_time"],
            due_date=row["due_date"] or "",
        )

