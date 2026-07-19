import pytest

from date_utils import (
    deadline_datetime,
    is_valid_date_text,
    normalize_date_text,
    safe_date,
    shift_month,
)


def test_normalize_date_text_accepts_leap_day():
    assert normalize_date_text("2024-02-29") == "2024-02-29"


@pytest.mark.parametrize("value", ["2023-02-29", "2024-2-29", "2024-13-01", "2024-04-31"])
def test_normalize_date_text_rejects_invalid_or_loose_dates(value):
    assert not is_valid_date_text(value)
    with pytest.raises(ValueError):
        normalize_date_text(value)


def test_shift_month_crosses_year_boundaries():
    assert shift_month(2026, 1, -1) == (2025, 12)
    assert shift_month(2026, 12, 1) == (2027, 1)
    assert shift_month(2026, 7, 12) == (2027, 7)


def test_safe_date_clamps_month_end():
    assert safe_date(2025, 2, 31).isoformat() == "2025-02-28"
    assert safe_date(2024, 2, 31).isoformat() == "2024-02-29"


def test_deadline_datetime_uses_end_of_day():
    assert deadline_datetime("2026-07-19").strftime("%Y-%m-%d %H:%M:%S") == (
        "2026-07-19 23:59:59"
    )
