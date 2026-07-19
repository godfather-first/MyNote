"""Date helpers shared by the form, reminder service, and tests."""

from __future__ import annotations

import calendar
from datetime import date, datetime, time


DATE_FORMAT = "%Y-%m-%d"


def today_text() -> str:
    """Return the current local date in the app's storage format."""

    return date.today().strftime(DATE_FORMAT)


def parse_date_text(value: str) -> date:
    """Parse a YYYY-MM-DD date and reject loosely formatted inputs."""

    stripped = value.strip()
    parsed = datetime.strptime(stripped, DATE_FORMAT).date()
    if parsed.strftime(DATE_FORMAT) != stripped:
        raise ValueError("date must use YYYY-MM-DD")
    return parsed


def normalize_date_text(value: str) -> str:
    """Return a canonical YYYY-MM-DD date string."""

    return parse_date_text(value).strftime(DATE_FORMAT)


def is_valid_date_text(value: str) -> bool:
    try:
        parse_date_text(value)
    except ValueError:
        return False
    return True


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    """Move across month/year boundaries."""

    month_index = (year * 12 + (month - 1)) + delta
    return month_index // 12, month_index % 12 + 1


def safe_date(year: int, month: int, day: int) -> date:
    """Create a date, clamping the day to the target month's end."""

    return date(year, month, min(day, days_in_month(year, month)))


def deadline_datetime(due_date: str) -> datetime:
    """Map a date-only deadline to the end of that local day."""

    return datetime.combine(parse_date_text(due_date), time(hour=23, minute=59, second=59))


def human_remaining(total_seconds: float) -> str:
    seconds = max(0, int(total_seconds))
    minutes, sec = divmod(seconds, 60)
    hours, minute = divmod(minutes, 60)
    days, hour = divmod(hours, 24)
    if days:
        return f"{days}天{hour}小时"
    if hour:
        return f"{hour}小时{minute}分钟"
    if minute:
        return f"{minute}分钟"
    return f"{sec}秒"
