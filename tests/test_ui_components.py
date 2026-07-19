from models import Task
from kivy.uix.popup import Popup
from screens.add_screen import AddScreen
from screens.detail_screen import DetailScreen
from screens.home_screen import TASK_PREVIEW_COLOR, TaskRow
from ui_components import DatePickerField, FormScrollView, PriorityPicker, StableTextInput


def test_stable_text_input_disables_mobile_copy_paste_bubble():
    field = StableTextInput()

    assert field.unfocus_on_touch is False
    assert field.use_bubble is False
    assert field.use_handles is False
    assert field.allow_copy is False


def test_stable_text_input_blocks_copy_paste_selection_actions():
    field = StableTextInput(text="只能手打")

    assert field.copy() == ""
    assert field.cut() == ""
    assert field.paste() is None
    assert field.select_all() is None
    assert field.select_text(0, 2) is None
    assert field.text == "只能手打"


def test_form_scroll_view_does_not_manually_redirect_touches_to_inputs():
    scroll = FormScrollView()

    assert not hasattr(scroll, "_text_input_at")


def test_date_picker_field_allows_manual_text_entry():
    field = DatePickerField(initial_date="2026-07-19")

    field.input.text = "2024-02-29"

    assert field.get_date() == "2024-02-29"


def test_date_picker_syncs_valid_manual_date_before_opening():
    field = DatePickerField(initial_date="2026-07-19")
    field.input.text = "2024-02-29"

    field._sync_valid_input_date()

    assert field._visible_year == 2024
    assert field._visible_month == 2


def test_date_picker_recovers_from_legacy_invalid_saved_date():
    field = DatePickerField(initial_date="bad-date")

    assert field.get_date()
    assert field.get_date().count("-") == 2


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


def test_long_press_preview_marks_title_yellow():
    task = Task(
        id=1,
        title="长按预览",
        content="",
        status=0,
        create_time="2026-07-19 10:00:00",
        update_time="2026-07-19 10:00:00",
        due_date="2026-07-19",
        priority=0,
        category="默认",
    )

    row = TaskRow(task, on_open=lambda *_: None, on_toggle=lambda *_: None, on_delete=lambda *_: None)

    row._trigger_long_press()

    assert row.title_label.color == list(TASK_PREVIEW_COLOR)


def test_mobile_form_controls_keep_large_touch_targets():
    class AppState:
        database = None

    add_screen = AddScreen(app_state=AppState())
    detail_screen = DetailScreen(app_state=AppState())
    priority_picker = PriorityPicker()

    assert add_screen.title_input.height >= 56
    assert add_screen.content_input.height >= 56
    assert add_screen.category_input.height >= 56
    assert detail_screen.status_button.height >= 56
    assert priority_picker.button.height >= 56


def test_priority_picker_clamps_legacy_invalid_value():
    priority_picker = PriorityPicker(initial_value=99)

    assert priority_picker.priority_value == 0
    assert priority_picker.label == "普通"


def test_picker_popups_keep_mobile_sized_touch_targets(monkeypatch):
    opened = []
    monkeypatch.setattr(Popup, "open", lambda self, *_args, **_kwargs: opened.append(self))

    date_field = DatePickerField(initial_date="2026-07-19")
    date_popup = date_field.open_picker()
    priority_picker = PriorityPicker()
    priority_popup = priority_picker.open_popup()

    assert date_popup.height >= 500
    assert date_field._days_grid.height >= 300
    assert priority_popup.height >= 360
    assert len(opened) == 2
