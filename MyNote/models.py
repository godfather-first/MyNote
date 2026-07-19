"""Data models for MyNote."""

from dataclasses import dataclass

from priority import priority_label


@dataclass
class Task:
    """A single local task note."""

    id: int | None
    title: str
    content: str
    status: int
    create_time: str
    update_time: str
    due_date: str = ""
    priority: int = 0
    category: str = "默认"
    reminder_sent: int = 0

    @property
    def is_done(self) -> bool:
        return self.status == 1

    @property
    def priority_text(self) -> str:
        return priority_label(self.priority)


@dataclass
class DeletedTask:
    """A task archived in the recycle bin."""

    id: int
    original_task_id: int | None
    title: str
    content: str
    status: int
    create_time: str
    update_time: str
    due_date: str
    priority: int
    category: str
    reminder_sent: int
    deleted_time: str

    @property
    def priority_text(self) -> str:
        return priority_label(self.priority)
