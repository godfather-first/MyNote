from models import Task
from screens.home_screen import TaskRow
from ui_components import DatePickerField


def test_date_picker_field_allows_manual_text_entry():
    field = DatePickerField(initial_date="2026-07-19")

    field.input.text = "2024-02-29"

    assert field.get_date() == "2024-02-29"


def test_done_task_row_shows_green_check_and_strikethrough_title():
    task = Task(
        id=1,
        title="已完成任务",
        content="",
        status=1,
        create_time="2026-07-19 10:00:00",
        update_time="2026-07-19 10:00:00",
        due_date="2026-07-19",
        priority=0,
        category="默认",
    )

    row = TaskRow(task, on_open=lambda *_: None, on_toggle=lambda *_: None, on_delete=lambda *_: None)

    assert row.children[-1].text == "✓"
    assert row.children[-1].color == [0.18, 0.55, 0.28, 1]
    assert row.title_label.text == "[s]已完成任务[/s]"
