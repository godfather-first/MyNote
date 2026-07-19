"""Data models for MyNote."""

from dataclasses import dataclass

from priority import priority_label


STATUS_ACTIVE = 0
STATUS_DONE = 1
DEFAULT_CATEGORY = "默认"


@dataclass(frozen=True)
class Task:
    id: int | None
    title: str
    content: str
    status: int
    create_time: str
    update_time: str
    due_date: str = ""
    priority: int = 0
    category: str = DEFAULT_CATEGORY
    reminder_sent: int = 0

    @property
    def is_done(self) -> bool:
        return self.status == STATUS_DONE

    @property
    def priority_text(self) -> str:
        return priority_label(self.priority)


@dataclass(frozen=True)
class DeletedTask:
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
