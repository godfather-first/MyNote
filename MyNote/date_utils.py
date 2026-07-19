"""Date helpers for storage, validation, calendars, and reminders."""

from __future__ import annotations

import calendar
from datetime import date, datetime, time


DATE_FORMAT = "%Y-%m-%d"


def today_text() -> str:
    return date.today().strftime(DATE_FORMAT)


def parse_date_text(value: str) -> date:
    """Parse a strict YYYY-MM-DD date."""

    text = (value or "").strip()
    parsed = datetime.strptime(text, DATE_FORMAT).date()
    if parsed.strftime(DATE_FORMAT) != text:
        raise ValueError("date must use YYYY-MM-DD")
    return parsed


def normalize_date_text(value: str) -> str:
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
    month_index = year * 12 + month - 1 + delta
    return month_index // 12, month_index % 12 + 1


def safe_date(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, days_in_month(year, month)))


def deadline_datetime(due_date: str) -> datetime:
    return datetime.combine(parse_date_text(due_date), time(23, 59, 59))


def human_remaining(total_seconds: float) -> str:
    seconds = max(0, int(total_seconds))
    minutes, second = divmod(seconds, 60)
    hours, minute = divmod(minutes, 60)
    days, hour = divmod(hours, 24)
    if days:
        return f"{days}天{hour}小时"
    if hour:
        return f"{hour}小时{minute}分钟"
    if minute:
        return f"{minute}分钟"
    return f"{second}秒"
