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

    @property
    def is_done(self) -> bool:
        return self.status == 1

