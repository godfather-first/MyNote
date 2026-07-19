"""SQLite persistence for MyNote.

The database is stored locally as tasks.db in the application directory.
On Android, the caller should pass the app's user_data_dir so the db file
is stored in a writable location (not inside the APK).
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from date_utils import deadline_datetime
from models import DeletedTask, Task


DEFAULT_REMINDER_THRESHOLD_MINUTES = 15
RECYCLE_BIN_RETENTION_DAYS = 10


class TaskDatabase:
    """Small SQLite wrapper for task CRUD operations."""

    def __init__(self, db_dir: str | None = None) -> None:
        if db_dir is None:
            db_dir = str(Path(__file__).resolve().parent)
        self.db_path = str(Path(db_dir) / "tasks.db")
        os.makedirs(db_dir, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_table()
        self._migrate_schema()
        self._ensure_default_settings()
        self.purge_expired_deleted_tasks()

    def _create_table(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                status INTEGER DEFAULT 0,
                create_time TEXT NOT NULL,
                update_time TEXT NOT NULL,
                due_date TEXT DEFAULT '',
                priority INTEGER DEFAULT 0,
                category TEXT DEFAULT '默认',
                reminder_sent INTEGER DEFAULT 0
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS deleted_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_task_id INTEGER,
                title TEXT NOT NULL,
                content TEXT DEFAULT '',
                status INTEGER DEFAULT 0,
                create_time TEXT NOT NULL,
                update_time TEXT NOT NULL,
                due_date TEXT DEFAULT '',
                priority INTEGER DEFAULT 0,
                category TEXT DEFAULT '默认',
                reminder_sent INTEGER DEFAULT 0,
                deleted_time TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def _migrate_schema(self) -> None:
        self._ensure_columns(
            "tasks",
            {
                "due_date": "TEXT DEFAULT ''",
                "priority": "INTEGER DEFAULT 0",
                "category": "TEXT DEFAULT '默认'",
                "reminder_sent": "INTEGER DEFAULT 0",
            },
        )
        self._ensure_columns(
            "deleted_tasks",
            {
                "original_task_id": "INTEGER",
                "due_date": "TEXT DEFAULT ''",
                "priority": "INTEGER DEFAULT 0",
                "category": "TEXT DEFAULT '默认'",
                "reminder_sent": "INTEGER DEFAULT 0",
                "deleted_time": "TEXT DEFAULT ''",
            },
        )

    def _ensure_columns(self, table_name: str, definitions: dict[str, str]) -> None:
        columns = {
            row["name"]
            for row in self.connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        for column_name, definition in definitions.items():
            if column_name in columns:
                continue
            self.connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
            )
        self.connection.commit()

    def _ensure_default_settings(self) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO app_settings (key, value)
            VALUES ('reminder_threshold_minutes', ?)
            """,
            (str(DEFAULT_REMINDER_THRESHOLD_MINUTES),),
        )
        self.connection.commit()

    def add_task(
        self,
        title: str,
        content: str = "",
        due_date: str = "",
        priority: int = 0,
        category: str = "默认",
    ) -> int:
        now = self._now()
        cursor = self.connection.execute(
            """
            INSERT INTO tasks (
                title, content, status, create_time, update_time,
                due_date, priority, category, reminder_sent
            )
            VALUES (?, ?, 0, ?, ?, ?, ?, ?, 0)
            """,
            (title, content, now, now, due_date, priority, category),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def get_tasks(self) -> list[Task]:
        rows = self.connection.execute(
            """
            SELECT id, title, content, status, create_time, update_time,
                   due_date, priority, category, reminder_sent
            FROM tasks
            ORDER BY status ASC, priority DESC, id DESC
            """
        ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def get_task(self, task_id: int) -> Task | None:
        row = self.connection.execute(
            """
            SELECT id, title, content, status, create_time, update_time,
                   due_date, priority, category, reminder_sent
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
        priority: int = 0,
        category: str = "默认",
    ) -> None:
        current = self.get_task(task_id)
        reminder_sent = current.reminder_sent if current else 0
        if current and current.due_date != due_date:
            reminder_sent = 0
        self.connection.execute(
            """
            UPDATE tasks
            SET title = ?, content = ?, due_date = ?, status = ?,
                priority = ?, category = ?, reminder_sent = ?, update_time = ?
            WHERE id = ?
            """,
            (
                title,
                content,
                due_date,
                status,
                priority,
                category,
                reminder_sent,
                self._now(),
                task_id,
            ),
        )
        self.connection.commit()

    def set_status(self, task_id: int, status: int) -> None:
        reminder_sent = 0 if status == 0 else 1
        self.connection.execute(
            "UPDATE tasks SET status = ?, reminder_sent = ?, update_time = ? WHERE id = ?",
            (status, reminder_sent, self._now(), task_id),
        )
        self.connection.commit()

    def delete_task(self, task_id: int) -> None:
        task = self.get_task(task_id)
        if task is None:
            return
        self.connection.execute(
            """
            INSERT INTO deleted_tasks (
                original_task_id, title, content, status, create_time, update_time,
                due_date, priority, category, reminder_sent, deleted_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.id,
                task.title,
                task.content,
                task.status,
                task.create_time,
                task.update_time,
                task.due_date,
                task.priority,
                task.category,
                task.reminder_sent,
                self._now(),
            ),
        )
        self.connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.connection.commit()

    def get_deleted_tasks(self) -> list[DeletedTask]:
        self.purge_expired_deleted_tasks()
        rows = self.connection.execute(
            """
            SELECT id, original_task_id, title, content, status, create_time, update_time,
                   due_date, priority, category, reminder_sent, deleted_time
            FROM deleted_tasks
            ORDER BY deleted_time DESC, id DESC
            """
        ).fetchall()
        return [self._row_to_deleted_task(row) for row in rows]

    def restore_deleted_task(self, deleted_task_id: int) -> int | None:
        row = self.connection.execute(
            """
            SELECT id, original_task_id, title, content, status, create_time, update_time,
                   due_date, priority, category, reminder_sent, deleted_time
            FROM deleted_tasks
            WHERE id = ?
            """,
            (deleted_task_id,),
        ).fetchone()
        if row is None:
            return None

        deleted_task = self._row_to_deleted_task(row)
        cursor = self.connection.execute(
            """
            INSERT INTO tasks (
                title, content, status, create_time, update_time,
                due_date, priority, category, reminder_sent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                deleted_task.title,
                deleted_task.content,
                deleted_task.status,
                deleted_task.create_time,
                self._now(),
                deleted_task.due_date,
                deleted_task.priority,
                deleted_task.category,
                deleted_task.reminder_sent,
            ),
        )
        self.connection.execute("DELETE FROM deleted_tasks WHERE id = ?", (deleted_task_id,))
        self.connection.commit()
        return int(cursor.lastrowid)

    def purge_expired_deleted_tasks(
        self,
        retention_days: int = RECYCLE_BIN_RETENTION_DAYS,
        now: datetime | None = None,
    ) -> int:
        cutoff = (now or datetime.now()) - timedelta(days=retention_days)
        cursor = self.connection.execute(
            "DELETE FROM deleted_tasks WHERE deleted_time < ?",
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),),
        )
        self.connection.commit()
        return int(cursor.rowcount)

    def get_setting(self, key: str, default: str = "") -> str:
        row = self.connection.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            (key,),
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        cursor = self.connection.execute(
            "UPDATE app_settings SET value = ? WHERE key = ?",
            (value, key),
        )
        if cursor.rowcount == 0:
            self.connection.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        self.connection.commit()

    def get_reminder_threshold_minutes(self) -> int:
        raw = self.get_setting(
            "reminder_threshold_minutes",
            str(DEFAULT_REMINDER_THRESHOLD_MINUTES),
        )
        try:
            threshold = int(raw)
        except ValueError:
            threshold = DEFAULT_REMINDER_THRESHOLD_MINUTES
        return max(1, min(threshold, 24 * 60))

    def set_reminder_threshold_minutes(self, minutes: int) -> None:
        self.set_setting("reminder_threshold_minutes", str(max(1, min(minutes, 24 * 60))))

    def get_due_reminder_tasks(
        self,
        now: datetime | None = None,
        threshold_minutes: int | None = None,
    ) -> list[Task]:
        current_time = now or datetime.now()
        threshold = threshold_minutes or self.get_reminder_threshold_minutes()
        rows = self.connection.execute(
            """
            SELECT id, title, content, status, create_time, update_time,
                   due_date, priority, category, reminder_sent
            FROM tasks
            WHERE status = 0
              AND reminder_sent = 0
              AND due_date != ''
            ORDER BY priority DESC, id DESC
            """
        ).fetchall()

        due_tasks = []
        for row in rows:
            task = self._row_to_task(row)
            try:
                seconds_left = (deadline_datetime(task.due_date) - current_time).total_seconds()
            except ValueError:
                continue
            if 0 <= seconds_left <= threshold * 60:
                due_tasks.append(task)
        return due_tasks

    def mark_reminder_sent(self, task_id: int) -> None:
        self.connection.execute(
            "UPDATE tasks SET reminder_sent = 1, update_time = ? WHERE id = ?",
            (self._now(), task_id),
        )
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
            priority=int(row["priority"] or 0),
            category=row["category"] or "默认",
            reminder_sent=int(row["reminder_sent"] or 0),
        )

    @staticmethod
    def _row_to_deleted_task(row: sqlite3.Row) -> DeletedTask:
        return DeletedTask(
            id=row["id"],
            original_task_id=row["original_task_id"],
            title=row["title"],
            content=row["content"] or "",
            status=int(row["status"]),
            create_time=row["create_time"],
            update_time=row["update_time"],
            due_date=row["due_date"] or "",
            priority=int(row["priority"] or 0),
            category=row["category"] or "默认",
            reminder_sent=int(row["reminder_sent"] or 0),
            deleted_time=row["deleted_time"],
        )
