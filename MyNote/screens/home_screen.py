"""Home screen with task search, filters, and list."""

from datetime import date, datetime

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.utils import escape_markup

from date_utils import deadline_datetime, human_remaining
from font_utils import FONT_NAME
from priority import priority_option
from ui_components import RoundedPanel, StableTextInput


FILTERS = [
    ("all", "全部"),
    ("active", "待办"),
    ("done", "已完成"),
    ("today", "今日"),
    ("important", "重要"),
]
FILTER_ORDER = [filter_key for filter_key, _text in FILTERS]
TASK_PREVIEW_COLOR = (0.90, 0.68, 0.08, 1)


def due_state(due_date: str, is_done: bool) -> tuple[str, tuple[float, float, float, float]]:
    """Return deadline display text and color."""

    if not due_date:
        return "无截止日期", (0.45, 0.45, 0.45, 1)

    try:
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
    except ValueError:
        return f"截止: {due_date}", (0.45, 0.45, 0.45, 1)

    if is_done:
        return f"截止: {due_date}", (0.45, 0.45, 0.45, 1)
    if due < date.today():
        return f"已逾期: {due_date}", (0.75, 0.18, 0.16, 1)
    if due == date.today():
        return f"今日截止: {due_date}", (0.85, 0.48, 0.05, 1)
    return f"截止: {due_date}", (0.24, 0.42, 0.70, 1)


class TaskRow(RoundedPanel):
    """Single task row used by the home list."""

    def __init__(self, task, on_open, on_toggle, on_delete, **kwargs):
        super().__init__(bg_color=(1, 1, 1, 1), **kwargs)
        self.task = task
        self.on_open = on_open
        self.on_toggle = on_toggle
        self.on_delete = on_delete
        self._long_press_event = None
        self._long_press_fired = False
        self._touch_start_x = 0
        self._touch_start_y = 0
        self._row_origin_x = 0
        self._swipe_deleted = False

        self.orientation = "horizontal"
        self.spacing = dp(10)
        self.padding = (dp(14), dp(10), dp(12), dp(10))
        self.size_hint_y = None
        self.height = dp(82)

        if task.is_done:
            self.add_widget(
                Label(
                    text="✓",
                    size_hint=(None, 1),
                    width=dp(26),
                    color=(0.18, 0.55, 0.28, 1),
                    bold=True,
                    font_size=dp(22),
                    font_name=FONT_NAME,
                )
            )

        info = BoxLayout(orientation="vertical", spacing=dp(3))
        text_color = (0.48, 0.48, 0.48, 1) if task.is_done else (0.12, 0.12, 0.12, 1)
        self.title_label = Label(
            text=self._title_text(),
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
            color=text_color,
            bold=not task.is_done,
            font_size=dp(16),
            font_name=FONT_NAME,
            markup=True,
        )
        self.title_label.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))

        deadline_text, deadline_color = due_state(task.due_date, task.is_done)
        priority = priority_option(task.priority_text)
        meta_color = (0.55, 0.55, 0.55, 1) if task.is_done else (
            priority["color"] if task.priority > 0 else deadline_color
        )
        meta = Label(
            text=f"{task.category} | {task.priority_text} | {deadline_text}",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            color=meta_color,
            font_size=dp(12),
            font_name=FONT_NAME,
        )
        meta.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))

        self.status_button = Button(
            text="恢复" if task.is_done else "完成",
            size_hint=(None, 1),
            width=dp(58),
            background_normal="",
            background_color=(0.86, 0.88, 0.82, 1) if task.is_done else (0.18, 0.55, 0.28, 1),
            color=(0.20, 0.20, 0.20, 1) if task.is_done else (1, 1, 1, 1),
            font_size=dp(13),
            font_name=FONT_NAME,
        )
        self.status_button.bind(on_release=self._toggle)

        info.add_widget(self.title_label)
        info.add_widget(meta)

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
        self._swipe_deleted = False
        self._long_press_fired = False
        Animation.cancel_all(self, "x")
        self._long_press_event = Clock.schedule_once(self._trigger_long_press, 2.0)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        dx = touch.x - self._touch_start_x
        dy = touch.y - self._touch_start_y
        if dx > dp(8) and abs(dx) > abs(dy) * 1.1:
            self._cancel_long_press()
            offset = min(dx, max(dp(124), self.width * 0.42))
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
            self._swipe_deleted = True
            target_x = self._row_origin_x + max(self.width, dp(360))
            Animation(x=target_x, opacity=0, duration=0.16, t="out_quad").start(self)
            Clock.schedule_once(lambda *_: self.on_delete(self.task.id), 0.17)
            return True
        if not self._swipe_deleted and abs(dx) < dp(16) and abs(dy) < dp(16) and self.collide_point(*touch.pos):
            self._animate_back()
            self._open_detail()
            return True
        self._animate_back()
        return True

    def _cancel_long_press(self):
        if self._long_press_event is not None:
            self._long_press_event.cancel()
            self._long_press_event = None

    def _trigger_long_press(self, *_args):
        self._long_press_fired = True
        self._set_title_preview(True)

    def _title_text(self) -> str:
        title = escape_markup(self.task.title)
        return f"[s]{title}[/s]" if self.task.is_done else title

    def _set_title_preview(self, preview: bool):
        if preview:
            self.title_label.text = self._title_text()
            self.title_label.color = TASK_PREVIEW_COLOR
        else:
            self.title_label.text = self._title_text()
            self.title_label.color = (0.48, 0.48, 0.48, 1) if self.task.is_done else (0.12, 0.12, 0.12, 1)

    def _animate_back(self):
        self.set_bg_color((1, 1, 1, 1))
        Animation(x=self._row_origin_x, opacity=1, duration=0.12, t="out_quad").start(self)

    def _open_detail(self, *_args):
        self.on_open(self.task.id)

    def _toggle(self, *_args):
        self.on_toggle(self.task.id, 0 if self.task.is_done else 1)


class HomeScreen(Screen):
    """Main task list screen."""

    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.current_filter = "all"
        self.filter_buttons = {}
        self._active_reminder_popup = None
        self._filter_swipe_start = (0, 0)
        self._filter_swipe_allowed = False
        self._filter_swipe_started_on_task = False
        self._build_ui()
        self._reminder_event = Clock.schedule_interval(self._poll_due_reminders, 30)
        self._cleanup_event = Clock.schedule_interval(
            lambda *_: self.app_state.database.purge_expired_deleted_tasks(),
            6 * 60 * 60,
        )

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)

        header = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(8), padding=(dp(12), dp(4)))
        title = Label(
            text="MyNote",
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(56),
            font_size=dp(24),
            bold=True,
            color=(0.12, 0.12, 0.12, 1),
            font_name=FONT_NAME,
        )
        title.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))
        self.reminder_button = Button(
            text="提醒",
            size_hint=(None, None),
            width=dp(68),
            height=dp(56),
            background_normal="",
            background_color=(0.62, 0.56, 0.42, 1),
            color=(1, 1, 1, 1),
            font_name=FONT_NAME,
        )
        self.reminder_button.bind(on_release=lambda *_: self._open_reminder_settings())
        self.recycle_button = Button(
            text="回收站",
            size_hint=(None, None),
            width=dp(84),
            height=dp(56),
            background_normal="",
            background_color=(0.26, 0.42, 0.64, 1),
            color=(1, 1, 1, 1),
            font_name=FONT_NAME,
        )
        self.recycle_button.bind(on_release=lambda *_: self._go_recycle_bin())
        header.add_widget(title)
        header.add_widget(self.reminder_button)
        header.add_widget(self.recycle_button)

        self.search_input = StableTextInput(
            hint_text="搜索任务标题或备注",
            multiline=False,
            size_hint_y=None,
            height=dp(56),
            padding=(dp(14), dp(16), dp(14), dp(10)),
            font_name=FONT_NAME,
        )
        self.search_input.bind(text=lambda *_: self.refresh())

        self.filter_bar = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6), padding=(dp(10), 0))
        for filter_key, filter_text in FILTERS:
            button = Button(
                text=filter_text,
                background_normal="",
                background_color=(0.88, 0.90, 0.88, 1),
                color=(0.18, 0.18, 0.18, 1),
                font_size=dp(13),
                font_name=FONT_NAME,
            )
            button.bind(on_release=lambda _button, key=filter_key: self._set_filter(key))
            self.filter_buttons[filter_key] = button
            self.filter_bar.add_widget(button)

        self.summary_label = Label(
            text="",
            size_hint_y=None,
            height=dp(30),
            color=(0.45, 0.45, 0.45, 1),
            font_size=dp(12),
            font_name=FONT_NAME,
        )

        self.scroll = ScrollView()
        self.list_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=(dp(10), dp(8), dp(10), dp(10)),
        )
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.scroll.add_widget(self.list_box)

        self.add_button = Button(
            text="+ 添加任务",
            size_hint_y=None,
            height=dp(56),
            background_normal="",
            background_color=(0.18, 0.55, 0.28, 1),
            color=(1, 1, 1, 1),
            font_size=dp(18),
            font_name=FONT_NAME,
        )
        self.add_button.bind(on_release=lambda *_: self._go_add())

        root.add_widget(header)
        root.add_widget(self.search_input)
        root.add_widget(self.filter_bar)
        root.add_widget(self.summary_label)
        root.add_widget(self.scroll)
        root.add_widget(self.add_button)
        self.add_widget(root)
        self._refresh_filter_buttons()

    def on_touch_down(self, touch):
        self._filter_swipe_start = (touch.x, touch.y)
        self._filter_swipe_allowed = self._can_start_filter_swipe(touch)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        handled = super().on_touch_up(touch)
        if not self._filter_swipe_allowed:
            return handled

        dx = touch.x - self._filter_swipe_start[0]
        dy = touch.y - self._filter_swipe_start[1]
        if self._filter_swipe_started_on_task and dx > 0:
            self._filter_swipe_allowed = False
            return handled
        if abs(dx) > dp(92) and abs(dx) > abs(dy) * 1.35:
            self._move_filter(1 if dx < 0 else -1)
            self._filter_swipe_allowed = False
            return True
        return handled

    def _can_start_filter_swipe(self, touch) -> bool:
        self._filter_swipe_started_on_task = False
        if not self.scroll.collide_point(*touch.pos):
            return False
        if self.search_input.collide_point(*touch.pos):
            return False
        if self.filter_bar.collide_point(*touch.pos):
            return False
        if self.add_button.collide_point(*touch.pos):
            return False
        if self.recycle_button.collide_point(*touch.pos):
            return False
        if self.reminder_button.collide_point(*touch.pos):
            return False
        self._filter_swipe_started_on_task = any(
            isinstance(widget, TaskRow) and widget.collide_point(*touch.pos)
            for widget in self.list_box.children
        )
        return True

    def on_pre_enter(self, *_args):
        self.refresh()
        self._poll_due_reminders()

    def refresh(self):
        self.list_box.clear_widgets()
        all_tasks = self.app_state.database.get_tasks()
        tasks = [task for task in all_tasks if self._matches(task)]
        done_count = sum(1 for task in all_tasks if task.is_done)
        self.summary_label.text = (
            f"总计 {len(all_tasks)} | 待办 {len(all_tasks) - done_count} | 已完成 {done_count}"
        )

        if not tasks:
            self.list_box.add_widget(
                Label(
                    text="暂无符合条件的任务",
                    size_hint_y=None,
                    height=dp(120),
                    color=(0.5, 0.5, 0.5, 1),
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
                )
            )

    def _matches(self, task):
        query = self.search_input.text.strip().lower()
        if query and query not in task.title.lower() and query not in task.content.lower():
            return False
        if self.current_filter == "active":
            return not task.is_done
        if self.current_filter == "done":
            return task.is_done
        if self.current_filter == "important":
            return task.priority > 0
        if self.current_filter == "today":
            return task.due_date == date.today().strftime("%Y-%m-%d")
        return True

    def _set_filter(self, filter_key):
        self.current_filter = filter_key
        self._refresh_filter_buttons()
        self.refresh()

    def _move_filter(self, offset):
        current_index = FILTER_ORDER.index(self.current_filter)
        next_index = (current_index + offset) % len(FILTER_ORDER)
        self._set_filter(FILTER_ORDER[next_index])

    def _refresh_filter_buttons(self):
        for filter_key, button in self.filter_buttons.items():
            active = filter_key == self.current_filter
            button.background_color = (0.18, 0.55, 0.28, 1) if active else (0.88, 0.90, 0.88, 1)
            button.color = (1, 1, 1, 1) if active else (0.18, 0.18, 0.18, 1)

    def _go_add(self):
        self.manager.current = "add"

    def _go_recycle_bin(self):
        recycle_bin = self.manager.get_screen("recycle_bin")
        recycle_bin.refresh()
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
        content.add_widget(
            Label(
                text="到期前提醒时间",
                size_hint_y=None,
                height=dp(30),
                color=(0.12, 0.12, 0.12, 1),
                bold=True,
                font_name=FONT_NAME,
            )
        )
        threshold_input = StableTextInput(
            text=str(self.app_state.database.get_reminder_threshold_minutes()),
            hint_text="1-1440 分钟",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=dp(58),
            padding=(dp(14), dp(16), dp(14), dp(10)),
            font_name=FONT_NAME,
        )
        error = Label(
            text="",
            size_hint_y=None,
            height=dp(26),
            color=(0.75, 0.18, 0.16, 1),
            font_size=dp(13),
            font_name=FONT_NAME,
        )
        content.add_widget(threshold_input)
        content.add_widget(error)

        buttons = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        close = Button(text="关闭", font_name=FONT_NAME)
        save = Button(
            text="保存",
            background_normal="",
            background_color=(0.18, 0.55, 0.28, 1),
            color=(1, 1, 1, 1),
            font_name=FONT_NAME,
        )
        buttons.add_widget(close)
        buttons.add_widget(save)
        content.add_widget(buttons)

        popup = Popup(
            title="提醒设置",
            content=content,
            size_hint=(0.86, None),
            height=dp(245),
            title_font=FONT_NAME,
            auto_dismiss=True,
        )

        def save_threshold(*_args):
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
        save.bind(on_release=save_threshold)
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
            seconds_left = (deadline_datetime(task.due_date) - datetime.now()).total_seconds()
            remaining = human_remaining(seconds_left)
        except ValueError:
            remaining = "未知"

        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(16))
        detail_text = (
            f"任务：{task.title}\n"
            f"剩余：{remaining}\n"
            f"分类：{task.category} | 优先级：{task.priority_text}\n"
            f"截止：{task.due_date}"
        )
        message = Label(
            text=detail_text,
            color=(0.12, 0.12, 0.12, 1),
            halign="left",
            valign="middle",
            font_name=FONT_NAME,
        )
        message.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))
        content.add_widget(message)

        buttons = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        later = Button(text="知道了", font_name=FONT_NAME)
        open_detail = Button(
            text="查看详情",
            background_normal="",
            background_color=(0.18, 0.55, 0.28, 1),
            color=(1, 1, 1, 1),
            font_name=FONT_NAME,
        )
        buttons.add_widget(later)
        buttons.add_widget(open_detail)
        content.add_widget(buttons)

        popup = Popup(
            title="任务即将截止",
            content=content,
            size_hint=(0.86, None),
            height=dp(280),
            title_font=FONT_NAME,
            auto_dismiss=True,
        )

        def clear_popup(*_args):
            self._active_reminder_popup = None

        def jump_to_detail(*_args):
            popup.dismiss()
            self._go_detail(task.id)

        later.bind(on_release=popup.dismiss)
        open_detail.bind(on_release=jump_to_detail)
        popup.bind(on_dismiss=clear_popup)
        self._active_reminder_popup = popup
        popup.open()
