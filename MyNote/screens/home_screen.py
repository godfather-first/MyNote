"""Home screen with task search, filters, and list."""

from datetime import date, datetime

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from font_utils import FONT_NAME


FILTERS = [
    ("all", "全部"),
    ("active", "待办"),
    ("done", "已完成"),
    ("today", "今日"),
    ("important", "重要"),
]


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


class TaskRow(BoxLayout):
    """Single task row used by the home list."""

    def __init__(self, task, on_open, on_toggle, on_delete, **kwargs):
        super().__init__(**kwargs)
        self.task = task
        self.on_open = on_open
        self.on_toggle = on_toggle
        self.on_delete = on_delete
        self._long_press_event = None
        self._long_press_fired = False

        self.orientation = "horizontal"
        self.spacing = dp(8)
        self.padding = (dp(12), dp(8), dp(12), dp(8))
        self.size_hint_y = None
        self.height = dp(92)

        self.status_button = Button(
            text="☑" if task.is_done else "☐",
            size_hint=(None, 1),
            width=dp(48),
            background_normal="",
            background_color=(0.92, 0.95, 0.92, 1),
            color=(0.15, 0.45, 0.18, 1),
            font_size=dp(20),
            font_name=FONT_NAME,
        )
        self.status_button.bind(on_release=self._toggle)

        info = BoxLayout(orientation="vertical", spacing=dp(3))
        text_color = (0.48, 0.48, 0.48, 1) if task.is_done else (0.12, 0.12, 0.12, 1)
        title = Label(
            text=task.title,
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
            color=text_color,
            bold=not task.is_done,
            font_size=dp(16),
            font_name=FONT_NAME,
        )
        title.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))
        title.bind(on_touch_down=self._open_from_label)

        deadline_text, deadline_color = due_state(task.due_date, task.is_done)
        meta = Label(
            text=f"{task.category} | {task.priority_text} | {deadline_text}",
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            color=deadline_color if not task.is_done else (0.55, 0.55, 0.55, 1),
            font_size=dp(12),
            font_name=FONT_NAME,
        )
        meta.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))

        created = Label(
            text=f"创建: {task.create_time}",
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            color=(0.58, 0.58, 0.58, 1),
            font_size=dp(11),
            font_name=FONT_NAME,
        )
        created.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))

        info.add_widget(title)
        info.add_widget(meta)
        info.add_widget(created)
        info.bind(on_touch_down=self._open_from_label)

        self.add_widget(self.status_button)
        self.add_widget(info)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if touch.is_double_tap:
            self._open_detail()
            return True
        self._long_press_fired = False
        self._long_press_event = Clock.schedule_once(self._trigger_long_press, 0.7)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._long_press_event is not None:
            self._long_press_event.cancel()
            self._long_press_event = None
        if self._long_press_fired and self.collide_point(*touch.pos):
            return True
        return super().on_touch_up(touch)

    def _open_from_label(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self._open_detail()
            return True
        return False

    def _trigger_long_press(self, *_args):
        self._long_press_fired = True
        self.on_delete(self.task.id)

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
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)

        header = Label(
            text="MyNote",
            size_hint_y=None,
            height=dp(58),
            font_size=dp(24),
            bold=True,
            color=(0.12, 0.12, 0.12, 1),
            font_name=FONT_NAME,
        )

        self.search_input = TextInput(
            hint_text="搜索任务标题或备注",
            multiline=False,
            size_hint_y=None,
            height=dp(46),
            padding=(dp(14), dp(12), dp(14), dp(8)),
            font_name=FONT_NAME,
        )
        self.search_input.bind(text=lambda *_: self.refresh())

        filter_bar = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6), padding=(dp(10), 0))
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
            filter_bar.add_widget(button)

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

        add_button = Button(
            text="+ 添加任务",
            size_hint_y=None,
            height=dp(56),
            background_normal="",
            background_color=(0.18, 0.55, 0.28, 1),
            color=(1, 1, 1, 1),
            font_size=dp(18),
            font_name=FONT_NAME,
        )
        add_button.bind(on_release=lambda *_: self._go_add())

        root.add_widget(header)
        root.add_widget(self.search_input)
        root.add_widget(filter_bar)
        root.add_widget(self.summary_label)
        root.add_widget(self.scroll)
        root.add_widget(add_button)
        self.add_widget(root)
        self._refresh_filter_buttons()

    def on_pre_enter(self, *_args):
        self.refresh()

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
                    on_delete=self._confirm_delete,
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

    def _refresh_filter_buttons(self):
        for filter_key, button in self.filter_buttons.items():
            active = filter_key == self.current_filter
            button.background_color = (0.18, 0.55, 0.28, 1) if active else (0.88, 0.90, 0.88, 1)
            button.color = (1, 1, 1, 1) if active else (0.18, 0.18, 0.18, 1)

    def _go_add(self):
        self.manager.current = "add"

    def _go_detail(self, task_id):
        detail = self.manager.get_screen("detail")
        detail.load_task(task_id)
        self.manager.current = "detail"

    def _toggle_task(self, task_id, status):
        self.app_state.database.set_status(task_id, status)
        self.refresh()

    def _confirm_delete(self, task_id):
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(16))
        content.add_widget(
            Label(
                text="是否删除该任务？",
                color=(0.12, 0.12, 0.12, 1),
                font_name=FONT_NAME,
            )
        )

        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        cancel = Button(text="取消", font_name=FONT_NAME)
        confirm = Button(
            text="确认删除",
            background_normal="",
            background_color=(0.75, 0.18, 0.16, 1),
            color=(1, 1, 1, 1),
            font_name=FONT_NAME,
        )
        buttons.add_widget(cancel)
        buttons.add_widget(confirm)
        content.add_widget(buttons)

        popup = Popup(
            title="确认",
            content=content,
            size_hint=(0.8, None),
            height=dp(190),
            title_font=FONT_NAME,
        )
        cancel.bind(on_release=popup.dismiss)
        confirm.bind(on_release=lambda *_: self._delete_task(task_id, popup))
        popup.open()

    def _delete_task(self, task_id, popup):
        popup.dismiss()
        self.app_state.database.delete_task(task_id)
        self.refresh()

