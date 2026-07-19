"""SQLite persistence for the local task app."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from date_utils import deadline_datetime
from models import DEFAULT_CATEGORY, STATUS_ACTIVE, STATUS_DONE, DeletedTask, Task
from priority import clamp_priority


DEFAULT_REMINDER_THRESHOLD_MINUTES = 15
RECYCLE_BIN_RETENTION_DAYS = 10


class TaskDatabase:
    """Small SQLite wrapper with explicit Android-safe storage paths."""

    def __init__(self, db_dir: str | None = None) -> None:
        if db_dir is None:
            db_dir = str(Path(__file__).resolve().parent)
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = str(Path(db_dir) / "tasks.db")
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()
        self._migrate()
        self._ensure_default_settings()
        self.purge_expired_deleted_tasks()

    def _create_tables(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                status INTEGER NOT NULL DEFAULT 0,
                create_time TEXT NOT NULL,
                update_time TEXT NOT NULL,
                due_date TEXT NOT NULL DEFAULT '',
                priority INTEGER NOT NULL DEFAULT 0,
                category TEXT NOT NULL DEFAULT '默认',
                reminder_sent INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS deleted_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_task_id INTEGER,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                status INTEGER NOT NULL DEFAULT 0,
                create_time TEXT NOT NULL,
                update_time TEXT NOT NULL,
                due_date TEXT NOT NULL DEFAULT '',
                priority INTEGER NOT NULL DEFAULT 0,
                category TEXT NOT NULL DEFAULT '默认',
                reminder_sent INTEGER NOT NULL DEFAULT 0,
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

    def _migrate(self) -> None:
        self._ensure_columns(
            "tasks",
            {
                "content": "TEXT NOT NULL DEFAULT ''",
                "status": "INTEGER NOT NULL DEFAULT 0",
                "due_date": "TEXT NOT NULL DEFAULT ''",
                "priority": "INTEGER NOT NULL DEFAULT 0",
                "category": "TEXT NOT NULL DEFAULT '默认'",
                "reminder_sent": "INTEGER NOT NULL DEFAULT 0",
            },
        )
        self._ensure_columns(
            "deleted_tasks",
            {
                "original_task_id": "INTEGER",
                "content": "TEXT NOT NULL DEFAULT ''",
                "status": "INTEGER NOT NULL DEFAULT 0",
                "due_date": "TEXT NOT NULL DEFAULT ''",
                "priority": "INTEGER NOT NULL DEFAULT 0",
                "category": "TEXT NOT NULL DEFAULT '默认'",
                "reminder_sent": "INTEGER NOT NULL DEFAULT 0",
                "deleted_time": "TEXT NOT NULL DEFAULT ''",
            },
        )
        self.connection.execute(
            """
            UPDATE deleted_tasks
            SET deleted_time = COALESCE(NULLIF(update_time, ''), ?)
            WHERE deleted_time = ''
            """,
            (self._now(),),
        )
        self.connection.commit()

    def _ensure_columns(self, table: str, definitions: dict[str, str]) -> None:
        columns = {row["name"] for row in self.connection.execute(f"PRAGMA table_info({table})")}
        for column, definition in definitions.items():
            if column not in columns:
                self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        self.connection.commit()

    def _ensure_default_settings(self) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
            ("reminder_threshold_minutes", str(DEFAULT_REMINDER_THRESHOLD_MINUTES)),
        )
        self.connection.commit()

    def add_task(
        self,
        title: str,
        content: str = "",
        due_date: str = "",
        priority: int = 0,
        category: str = DEFAULT_CATEGORY,
    ) -> int:
        now = self._now()
        cursor = self.connection.execute(
            """
            INSERT INTO tasks (
                title, content, status, create_time, update_time,
                due_date, priority, category, reminder_sent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                title.strip(),
                content or "",
                STATUS_ACTIVE,
                now,
                now,
                due_date or "",
                clamp_priority(priority),
                (category or DEFAULT_CATEGORY).strip() or DEFAULT_CATEGORY,
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def get_tasks(self) -> list[Task]:
        rows = self.connection.execute(
            """
            SELECT id, title, content, status, create_time, update_time,
                   due_date, priority, category, reminder_sent
            FROM tasks
            ORDER BY status ASC, priority DESC, due_date ASC, id DESC
            """
        ).fetchall()
        return [self._task_from_row(row) for row in rows]

    def get_task(self, task_id: int | None) -> Task | None:
        row = self.connection.execute(
            """
            SELECT id, title, content, status, create_time, update_time,
                   due_date, priority, category, reminder_sent
            FROM tasks
            WHERE id = ?
            """,
            (task_id,),
        ).fetchone()
        return self._task_from_row(row) if row else None

    def update_task(
        self,
        task_id: int,
        title: str,
        content: str,
        due_date: str,
        status: int,
        priority: int,
        category: str,
    ) -> bool:
        old = self.get_task(task_id)
        if old is None:
            return False
        reminder_sent = old.reminder_sent if old.due_date == due_date and status == STATUS_ACTIVE else 0
        if status == STATUS_DONE:
            reminder_sent = 1
        cursor = self.connection.execute(
            """
            UPDATE tasks
            SET title = ?, content = ?, due_date = ?, status = ?,
                priority = ?, category = ?, reminder_sent = ?, update_time = ?
            WHERE id = ?
            """,
            (
                title.strip(),
                content or "",
                due_date or "",
                STATUS_DONE if status == STATUS_DONE else STATUS_ACTIVE,
                clamp_priority(priority),
                (category or DEFAULT_CATEGORY).strip() or DEFAULT_CATEGORY,
                reminder_sent,
                self._now(),
                task_id,
            ),
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def set_status(self, task_id: int, status: int) -> bool:
        status = STATUS_DONE if status == STATUS_DONE else STATUS_ACTIVE
        reminder_sent = 1 if status == STATUS_DONE else 0
        cursor = self.connection.execute(
            "UPDATE tasks SET status = ?, reminder_sent = ?, update_time = ? WHERE id = ?",
            (status, reminder_sent, self._now(), task_id),
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if task is None:
            return False
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
        return True

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
        return [self._deleted_from_row(row) for row in rows]

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
        task = self._deleted_from_row(row)
        cursor = self.connection.execute(
            """
            INSERT INTO tasks (
                title, content, status, create_time, update_time,
                due_date, priority, category, reminder_sent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.title,
                task.content,
                task.status,
                task.create_time,
                self._now(),
                task.due_date,
                task.priority,
                task.category,
                task.reminder_sent,
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
        row = self.connection.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        cursor = self.connection.execute("UPDATE app_settings SET value = ? WHERE key = ?", (value, key))
        if cursor.rowcount == 0:
            self.connection.execute("INSERT INTO app_settings (key, value) VALUES (?, ?)", (key, value))
        self.connection.commit()

    def get_reminder_threshold_minutes(self) -> int:
        raw = self.get_setting("reminder_threshold_minutes", str(DEFAULT_REMINDER_THRESHOLD_MINUTES))
        try:
            value = int(raw)
        except ValueError:
            value = DEFAULT_REMINDER_THRESHOLD_MINUTES
        return max(1, min(value, 24 * 60))

    def set_reminder_threshold_minutes(self, minutes: int) -> None:
        self.set_setting("reminder_threshold_minutes", str(max(1, min(int(minutes), 24 * 60))))

    def get_due_reminder_tasks(
        self,
        now: datetime | None = None,
        threshold_minutes: int | None = None,
    ) -> list[Task]:
        current = now or datetime.now()
        threshold = threshold_minutes or self.get_reminder_threshold_minutes()
        tasks = []
        for task in self.get_tasks():
            if task.is_done or task.reminder_sent or not task.due_date:
                continue
            try:
                seconds_left = (deadline_datetime(task.due_date) - current).total_seconds()
            except ValueError:
                continue
            if 0 <= seconds_left <= threshold * 60:
                tasks.append(task)
        return tasks

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
    def _task_from_row(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            content=row["content"] or "",
            status=int(row["status"] or STATUS_ACTIVE),
            create_time=row["create_time"],
            update_time=row["update_time"],
            due_date=row["due_date"] or "",
            priority=clamp_priority(row["priority"]),
            category=row["category"] or DEFAULT_CATEGORY,
            reminder_sent=int(row["reminder_sent"] or 0),
        )

    @staticmethod
    def _deleted_from_row(row: sqlite3.Row) -> DeletedTask:
        return DeletedTask(
            id=row["id"],
            original_task_id=row["original_task_id"],
            title=row["title"],
            content=row["content"] or "",
            status=int(row["status"] or STATUS_ACTIVE),
            create_time=row["create_time"],
            update_time=row["update_time"],
            due_date=row["due_date"] or "",
            priority=clamp_priority(row["priority"]),
            category=row["category"] or DEFAULT_CATEGORY,
            reminder_sent=int(row["reminder_sent"] or 0),
            deleted_time=row["deleted_time"] or "",
        )
