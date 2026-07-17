"""Data models for MyNote."""

from dataclasses import dataclass


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

    @property
    def is_done(self) -> bool:
        return self.status == 1

    @property
    def priority_text(self) -> str:
        return {0: "普通", 1: "重要", 2: "紧急"}.get(self.priority, "普通")
