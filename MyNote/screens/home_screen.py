"""Home screen with search, filters, reminders, and task cards."""

from datetime import date, datetime

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.utils import escape_markup

from date_utils import deadline_datetime, human_remaining
from font_utils import FONT_NAME
from models import STATUS_ACTIVE, STATUS_DONE
from priority import priority_option
from ui_components import (
    DANGER,
    MUTED,
    PRIMARY,
    SUCCESS,
    TEXT,
    WARNING,
    MobileButton,
    MobileTextInput,
    RoundedPanel,
    bind_text_size,
)


FILTERS = [
    ("all", "全部"),
    ("active", "待办"),
    ("done", "已完成"),
    ("today", "今日"),
    ("important", "重要"),
]
FILTER_ORDER = [key for key, _label in FILTERS]
TASK_PREVIEW_COLOR = (0.90, 0.68, 0.08, 1)


def due_state(due_date: str, is_done: bool) -> tuple[str, tuple[float, float, float, float]]:
    if not due_date:
        return "无截止日期", MUTED
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
    except ValueError:
        return f"截止：{due_date}", MUTED
    if is_done:
        return f"截止：{due_date}", MUTED
    if due < date.today():
        return f"已逾期：{due_date}", DANGER
    if due == date.today():
        return f"今日截止：{due_date}", WARNING
    return f"截止：{due_date}", PRIMARY


class TaskRow(RoundedPanel):
    """Task card with tap, complete, long press, and swipe gestures."""

    def __init__(self, task, on_open, on_toggle, on_delete, on_next_filter=None, **kwargs):
        super().__init__(bg_color=(1, 1, 1, 1), **kwargs)
        self.task = task
        self.on_open = on_open
        self.on_toggle = on_toggle
        self.on_delete = on_delete
        self.on_next_filter = on_next_filter or (lambda: None)
        self._long_press_event = None
        self._long_press_fired = False
        self._touch_start_x = 0
        self._touch_start_y = 0
        self._row_origin_x = 0

        self.orientation = "horizontal"
        self.spacing = dp(10)
        self.padding = (dp(14), dp(10), dp(12), dp(10))
        self.size_hint_y = None
        self.height = dp(88)

        if task.is_done:
            self.add_widget(
                Label(
                    text="✓",
                    size_hint=(None, 1),
                    width=dp(28),
                    color=SUCCESS,
                    bold=True,
                    font_size=dp(22),
                    font_name=FONT_NAME,
                )
            )

        info = BoxLayout(orientation="vertical", spacing=dp(3))
        self.title_label = bind_text_size(
            Label(
                text=self._title_text(),
                size_hint_y=None,
                height=dp(32),
                halign="left",
                valign="middle",
                color=MUTED if task.is_done else TEXT,
                bold=not task.is_done,
                font_size=dp(16),
                font_name=FONT_NAME,
                markup=True,
            )
        )
        deadline_text, deadline_color = due_state(task.due_date, task.is_done)
        priority = priority_option(task.priority)
        meta_color = MUTED if task.is_done else (priority["color"] if task.priority > 0 else deadline_color)
        meta = bind_text_size(
            Label(
                text=f"{task.category} | {task.priority_text} | {deadline_text}",
                size_hint_y=None,
                height=dp(30),
                halign="left",
                valign="middle",
                color=meta_color,
                font_size=dp(12),
                font_name=FONT_NAME,
            )
        )
        info.add_widget(self.title_label)
        info.add_widget(meta)

        self.status_button = MobileButton(
            text="恢复" if task.is_done else "完成",
            size_hint=(None, 1),
            width=dp(64),
            background_color=(0.86, 0.88, 0.82, 1) if task.is_done else SUCCESS,
            color=TEXT if task.is_done else (1, 1, 1, 1),
            font_size=dp(13),
        )
        self.status_button.bind(on_release=self._toggle)

        self.add_widget(info)
        self.add_widget(self.status_button)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self.status_button.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        touch.grab(self)
        self._touch_start_x = touch.x
        self._touch_start_y = touch.y
        self._row_origin_x = self.x
        self._long_press_fired = False
        Animation.cancel_all(self, "x")
        self._long_press_event = Clock.schedule_once(self._trigger_long_press, 2.0)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        dx = touch.x - self._touch_start_x
        dy = touch.y - self._touch_start_y
        if abs(dx) > dp(8) and abs(dx) > abs(dy) * 1.1:
            self._cancel_long_press()
            if dx > 0:
                offset = min(dx, max(dp(132), self.width * 0.45))
                self.x = self._row_origin_x + offset
                self.set_bg_color((1, 0.92, 0.90, 1) if offset > dp(96) else (1, 1, 1, 1))
            return True
        if abs(dy) > dp(18):
            self._cancel_long_press()
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        touch.ungrab(self)
        self._cancel_long_press()
        dx = touch.x - self._touch_start_x
        dy = touch.y - self._touch_start_y
        if self._long_press_fired:
            self._set_title_preview(False)
            self._animate_back()
            return True
        if dx > dp(96) and abs(dx) > abs(dy) * 1.2:
            target_x = self._row_origin_x + max(self.width, dp(420))
            Animation(x=target_x, opacity=0, duration=0.16, t="out_quad").start(self)
            Clock.schedule_once(lambda *_: self.on_delete(self.task.id), 0.17)
            return True
        if dx < -dp(96) and abs(dx) > abs(dy) * 1.2:
            self._animate_back()
            self.on_next_filter()
            return True
        if abs(dx) < dp(16) and abs(dy) < dp(16) and self.collide_point(*touch.pos):
            self._animate_back()
            self.on_open(self.task.id)
            return True
        self._animate_back()
        return True

    def _title_text(self) -> str:
        title = escape_markup(self.task.title)
        return f"[s]{title}[/s]" if self.task.is_done else title

    def _trigger_long_press(self, *_args):
        self._long_press_fired = True
        self._set_title_preview(True)

    def _set_title_preview(self, preview: bool):
        self.title_label.text = self._title_text()
        self.title_label.color = TASK_PREVIEW_COLOR if preview else (MUTED if self.task.is_done else TEXT)

    def _cancel_long_press(self):
        if self._long_press_event is not None:
            self._long_press_event.cancel()
            self._long_press_event = None

    def _animate_back(self):
        self.set_bg_color((1, 1, 1, 1))
        Animation(x=self._row_origin_x, opacity=1, duration=0.12, t="out_quad").start(self)

    def _toggle(self, *_args):
        self.on_toggle(self.task.id, STATUS_ACTIVE if self.task.is_done else STATUS_DONE)


class HomeScreen(Screen):
    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.current_filter = "all"
        self.filter_buttons = {}
        self._active_reminder_popup = None
        self._swipe_start = (0, 0)
        self._swipe_allowed = False
        self._swipe_started_on_task = False
        self._build_ui()
        self._reminder_event = Clock.schedule_interval(self._poll_due_reminders, 30)
        self._cleanup_event = Clock.schedule_interval(
            lambda *_: self.app_state.database.purge_expired_deleted_tasks(),
            6 * 60 * 60,
        )

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)
        header = BoxLayout(size_hint_y=None, height=dp(66), spacing=dp(8), padding=(dp(12), dp(5)))
        title = bind_text_size(
            Label(
                text="MyNote",
                halign="left",
                valign="middle",
                color=TEXT,
                bold=True,
                font_size=dp(24),
                font_name=FONT_NAME,
            )
        )
        self.reminder_button = MobileButton(text="提醒", size_hint_x=None, width=dp(72), background_color=(0.62, 0.56, 0.42, 1), color=(1, 1, 1, 1))
        self.recycle_button = MobileButton(text="回收站", size_hint_x=None, width=dp(88), background_color=PRIMARY, color=(1, 1, 1, 1))
        self.reminder_button.bind(on_release=lambda *_: self._open_reminder_settings())
        self.recycle_button.bind(on_release=lambda *_: self._go_recycle_bin())
        header.add_widget(title)
        header.add_widget(self.reminder_button)
        header.add_widget(self.recycle_button)

        self.search_input = MobileTextInput(
            hint_text="搜索任务标题或备注",
            multiline=False,
            size_hint_y=None,
            height=dp(58),
        )
        self.search_input.bind(text=lambda *_: self.refresh())

        self.filter_bar = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6), padding=(dp(10), dp(4)))
        for key, text in FILTERS:
            button = MobileButton(text=text, background_color=(0.88, 0.90, 0.88, 1), color=TEXT, font_size=dp(13))
            button.bind(on_release=lambda _button, filter_key=key: self._set_filter(filter_key))
            self.filter_buttons[key] = button
            self.filter_bar.add_widget(button)

        self.summary_label = Label(
            text="",
            size_hint_y=None,
            height=dp(32),
            color=MUTED,
            font_size=dp(12),
            font_name=FONT_NAME,
        )

        self.scroll = ScrollView(do_scroll_x=False)
        self.list_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=(dp(10), dp(8), dp(10), dp(12)),
        )
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.scroll.add_widget(self.list_box)

        self.add_button = MobileButton(text="+ 添加任务", background_color=SUCCESS, color=(1, 1, 1, 1), font_size=dp(18))
        self.add_button.bind(on_release=lambda *_: self._go_add())

        for widget in (header, self.search_input, self.filter_bar, self.summary_label, self.scroll, self.add_button):
            root.add_widget(widget)
        self.add_widget(root)
        self._refresh_filter_buttons()

    def on_pre_enter(self, *_args):
        self.refresh()
        self._poll_due_reminders()

    def on_touch_down(self, touch):
        self._swipe_start = (touch.x, touch.y)
        self._swipe_allowed = self._can_start_filter_swipe(touch)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        handled = super().on_touch_up(touch)
        if not self._swipe_allowed:
            return handled
        dx = touch.x - self._swipe_start[0]
        dy = touch.y - self._swipe_start[1]
        if self._swipe_started_on_task and dx > 0:
            return handled
        if abs(dx) > dp(96) and abs(dx) > abs(dy) * 1.35:
            self._move_filter(1 if dx < 0 else -1)
            return True
        return handled

    def _can_start_filter_swipe(self, touch) -> bool:
        self._swipe_started_on_task = False
        excluded = (self.search_input, self.filter_bar, self.add_button, self.recycle_button, self.reminder_button)
        if not self.scroll.collide_point(*touch.pos) or any(widget.collide_point(*touch.pos) for widget in excluded):
            return False
        self._swipe_started_on_task = any(
            isinstance(widget, TaskRow) and widget.collide_point(*touch.pos)
            for widget in self.list_box.children
        )
        return True

    def refresh(self):
        self.list_box.clear_widgets()
        all_tasks = self.app_state.database.get_tasks()
        tasks = [task for task in all_tasks if self._matches(task)]
        done_count = sum(1 for task in all_tasks if task.is_done)
        self.summary_label.text = f"总计 {len(all_tasks)} | 待办 {len(all_tasks) - done_count} | 已完成 {done_count}"
        if not tasks:
            self.list_box.add_widget(
                Label(
                    text="暂无符合条件的任务",
                    size_hint_y=None,
                    height=dp(140),
                    color=MUTED,
                    font_size=dp(16),
                    font_name=FONT_NAME,
                )
            )
            return
        for task in tasks:
            self.list_box.add_widget(
                TaskRow(
                    task=task,
                    on_open=self._go_detail,
                    on_toggle=self._toggle_task,
                    on_delete=self._archive_task,
                    on_next_filter=lambda: self._move_filter(1),
                )
            )

    def _matches(self, task) -> bool:
        query = self.search_input.text.strip().lower()
        if query and query not in task.title.lower() and query not in task.content.lower():
            return False
        if self.current_filter == "active":
            return not task.is_done
        if self.current_filter == "done":
            return task.is_done
        if self.current_filter == "today":
            return task.due_date == date.today().strftime("%Y-%m-%d")
        if self.current_filter == "important":
            return task.priority > 0
        return True

    def _set_filter(self, filter_key):
        self.current_filter = filter_key
        self._refresh_filter_buttons()
        self.refresh()

    def _move_filter(self, offset):
        index = FILTER_ORDER.index(self.current_filter)
        self._set_filter(FILTER_ORDER[(index + offset) % len(FILTER_ORDER)])

    def _refresh_filter_buttons(self):
        for key, button in self.filter_buttons.items():
            active = key == self.current_filter
            button.background_color = SUCCESS if active else (0.88, 0.90, 0.88, 1)
            button.color = (1, 1, 1, 1) if active else TEXT

    def _go_add(self):
        self.manager.current = "add"

    def _go_recycle_bin(self):
        recycle = self.manager.get_screen("recycle_bin")
        recycle.refresh()
        self.manager.current = "recycle_bin"

    def _go_detail(self, task_id):
        detail = self.manager.get_screen("detail")
        detail.load_task(task_id)
        self.manager.current = "detail"

    def _toggle_task(self, task_id, status):
        self.app_state.database.set_status(task_id, status)
        self.refresh()

    def _archive_task(self, task_id):
        self.app_state.database.delete_task(task_id)
        self.refresh()

    def _open_reminder_settings(self):
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(16))
        content.add_widget(Label(text="到期前提醒时间（分钟）", color=TEXT, font_name=FONT_NAME))
        threshold_input = MobileTextInput(
            text=str(self.app_state.database.get_reminder_threshold_minutes()),
            hint_text="1-1440",
            multiline=False,
            input_filter="int",
        )
        error = Label(text="", size_hint_y=None, height=dp(28), color=DANGER, font_name=FONT_NAME)
        buttons = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8))
        close = MobileButton(text="关闭", background_color=(0.82, 0.82, 0.78, 1), color=TEXT)
        save = MobileButton(text="保存", background_color=SUCCESS, color=(1, 1, 1, 1))
        buttons.add_widget(close)
        buttons.add_widget(save)
        for widget in (threshold_input, error, buttons):
            content.add_widget(widget)
        popup = Popup(title="提醒设置", content=content, size_hint=(0.86, None), height=dp(260), title_font=FONT_NAME)

        def save_value(*_args):
            try:
                minutes = int(threshold_input.text.strip())
            except ValueError:
                error.text = "请输入 1 到 1440 的分钟数"
                return
            if minutes < 1 or minutes > 1440:
                error.text = "请输入 1 到 1440 的分钟数"
                return
            self.app_state.database.set_reminder_threshold_minutes(minutes)
            popup.dismiss()

        close.bind(on_release=popup.dismiss)
        save.bind(on_release=save_value)
        popup.open()
        threshold_input.focus = True
        return popup

    def _poll_due_reminders(self, *_args):
        if self._active_reminder_popup is not None:
            return
        due_tasks = self.app_state.database.get_due_reminder_tasks()
        if not due_tasks:
            return
        task = due_tasks[0]
        self.app_state.database.mark_reminder_sent(task.id)
        self._show_reminder_popup(task)

    def _show_reminder_popup(self, task):
        try:
            remaining = human_remaining((deadline_datetime(task.due_date) - datetime.now()).total_seconds())
        except ValueError:
            remaining = "未知"
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(16))
        message = bind_text_size(
            Label(
                text=(
                    f"任务：{task.title}\n"
                    f"剩余：{remaining}\n"
                    f"分类：{task.category} | 优先级：{task.priority_text}\n"
                    f"截止：{task.due_date}"
                ),
                halign="left",
                valign="middle",
                color=TEXT,
                font_name=FONT_NAME,
            )
        )
        buttons = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8))
        close = MobileButton(text="关闭", background_color=(0.82, 0.82, 0.78, 1), color=TEXT)
        detail = MobileButton(text="查看详情", background_color=SUCCESS, color=(1, 1, 1, 1))
        buttons.add_widget(close)
        buttons.add_widget(detail)
        content.add_widget(message)
        content.add_widget(buttons)
        popup = Popup(title="任务即将截止", content=content, size_hint=(0.86, None), height=dp(285), title_font=FONT_NAME)

        def clear_popup(*_args):
            self._active_reminder_popup = None

        def jump(*_args):
            popup.dismiss()
            self._go_detail(task.id)

        close.bind(on_release=popup.dismiss)
        detail.bind(on_release=jump)
        popup.bind(on_dismiss=clear_popup)
        self._active_reminder_popup = popup
        popup.open()
