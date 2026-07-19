from dataclasses import dataclass

from database import TaskDatabase
from date_utils import today_text
from models import Task
from screens.home_screen import FILTER_ORDER, HomeScreen, TaskRow


@dataclass
class AppState:
    database: TaskDatabase


class _ScheduledEvent:
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


class _Touch:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.grab_current = None

    def move_to(self, x, y):
        self.x = x
        self.y = y
        self.pos = (x, y)

    def grab(self, widget):
        self.grab_current = widget

    def ungrab(self, widget):
        if self.grab_current is widget:
            self.grab_current = None


def _close_screen(screen):
    screen._reminder_event.cancel()
    screen._cleanup_event.cancel()


def test_home_search_and_filters_match_required_logic(tmp_path):
    db = TaskDatabase(db_dir=str(tmp_path))
    today = today_text()
    active_id = db.add_task("写周报", content="包含销售数据", due_date=today, priority=0)
    done_id = db.add_task("买牛奶", content="路上顺手", due_date="2099-12-31", priority=0)
    important_id = db.add_task("处理合同", content="客户急迫", due_date=today, priority=2)
    db.set_status(done_id, 1)

    screen = HomeScreen(app_state=AppState(db))
    tasks = {task.id: task for task in db.get_tasks()}

    screen.search_input.text = "销售"
    assert screen._matches(tasks[active_id])
    assert not screen._matches(tasks[done_id])

    screen.search_input.text = ""
    screen.current_filter = "active"
    assert screen._matches(tasks[active_id])
    assert not screen._matches(tasks[done_id])

    screen.current_filter = "done"
    assert screen._matches(tasks[done_id])
    assert not screen._matches(tasks[active_id])

    screen.current_filter = "today"
    assert screen._matches(tasks[active_id])
    assert screen._matches(tasks[important_id])
    assert not screen._matches(tasks[done_id])

    screen.current_filter = "important"
    assert screen._matches(tasks[important_id])
    assert not screen._matches(tasks[active_id])

    _close_screen(screen)
    db.close()


def test_home_filter_swipe_order_wraps_around(tmp_path):
    db = TaskDatabase(db_dir=str(tmp_path))
    screen = HomeScreen(app_state=AppState(db))

    screen.current_filter = FILTER_ORDER[0]
    screen._move_filter(1)
    assert screen.current_filter == FILTER_ORDER[1]

    screen._move_filter(-1)
    assert screen.current_filter == FILTER_ORDER[0]

    screen._move_filter(-1)
    assert screen.current_filter == FILTER_ORDER[-1]

    _close_screen(screen)
    db.close()


def test_task_row_right_swipe_above_threshold_deletes_without_toggling(monkeypatch):
    task = Task(
        id=7,
        title="滑动删除",
        content="",
        status=0,
        create_time="2026-07-19 10:00:00",
        update_time="2026-07-19 10:00:00",
        due_date="2026-07-19",
        priority=0,
        category="默认",
    )
    deleted = []
    toggled = []
    opened = []

    def fake_schedule(callback, timeout=0, *args, **kwargs):
        if timeout < 1:
            callback(0)
        return _ScheduledEvent()

    monkeypatch.setattr("screens.home_screen.Clock.schedule_once", fake_schedule)

    row = TaskRow(
        task,
        on_open=lambda task_id: opened.append(task_id),
        on_toggle=lambda *args: toggled.append(args),
        on_delete=lambda task_id: deleted.append(task_id),
    )
    row.pos = (0, 0)
    row.size = (400, 82)
    row.status_button.pos = (320, 0)
    row.status_button.size = (70, 82)

    touch = _Touch(20, 40)
    assert row.on_touch_down(touch)
    touch.move_to(145, 42)
    assert row.on_touch_move(touch)
    assert row.on_touch_up(touch)

    assert deleted == [7]
    assert toggled == []
    assert opened == []
