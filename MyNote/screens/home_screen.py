"""Home screen with the task list."""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView


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
        self.height = dp(76)

        checkbox_text = "☑" if task.is_done else "☐"
        self.status_button = Button(
            text=checkbox_text,
            size_hint=(None, 1),
            width=dp(48),
            background_normal="",
            background_color=(0.92, 0.95, 0.92, 1),
            color=(0.15, 0.45, 0.18, 1),
            font_size=dp(18),
        )
        self.status_button.bind(on_release=self._toggle)

        text_color = (0.48, 0.48, 0.48, 1) if task.is_done else (0.12, 0.12, 0.12, 1)
        title_prefix = "☑ " if task.is_done else "☐ "
        due = f" | 截止: {task.due_date}" if task.due_date else ""
        self.info_button = Button(
            text=f"{title_prefix}{task.title}\n创建: {task.create_time}{due}",
            halign="left",
            valign="middle",
            background_normal="",
            background_color=(1, 1, 1, 1),
            color=text_color,
            font_size=dp(15),
        )
        self.info_button.bind(size=self._sync_text_size)
        self.info_button.bind(on_release=self._open_detail)

        self.add_widget(self.status_button)
        self.add_widget(self.info_button)

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

    def _trigger_long_press(self, *_args):
        self._long_press_fired = True
        self.on_delete(self.task.id)

    def _sync_text_size(self, widget, _value):
        widget.text_size = (widget.width - dp(16), None)

    def _open_detail(self, *_args):
        self.on_open(self.task.id)

    def _toggle(self, *_args):
        self.on_toggle(self.task.id, 0 if self.task.is_done else 1)


class HomeScreen(Screen):
    """Main task list screen."""

    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)

        header = Label(
            text="MyNote",
            size_hint_y=None,
            height=dp(64),
            font_size=dp(24),
            bold=True,
            color=(0.12, 0.12, 0.12, 1),
        )

        self.scroll = ScrollView()
        self.list_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(6),
            padding=(dp(10), dp(10), dp(10), dp(10)),
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
        )
        add_button.bind(on_release=lambda *_: self._go_add())

        root.add_widget(header)
        root.add_widget(self.scroll)
        root.add_widget(add_button)
        self.add_widget(root)

    def on_pre_enter(self, *_args):
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        tasks = self.app_state.database.get_tasks()
        if not tasks:
            self.list_box.add_widget(
                Label(
                    text="暂无任务",
                    size_hint_y=None,
                    height=dp(120),
                    color=(0.5, 0.5, 0.5, 1),
                    font_size=dp(16),
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
        content.add_widget(Label(text="是否删除该任务？", color=(0.12, 0.12, 0.12, 1)))

        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        cancel = Button(text="取消")
        confirm = Button(
            text="确认删除",
            background_normal="",
            background_color=(0.75, 0.18, 0.16, 1),
            color=(1, 1, 1, 1),
        )
        buttons.add_widget(cancel)
        buttons.add_widget(confirm)
        content.add_widget(buttons)

        popup = Popup(title="确认", content=content, size_hint=(0.8, None), height=dp(190))
        cancel.bind(on_release=popup.dismiss)
        confirm.bind(on_release=lambda *_: self._delete_task(task_id, popup))
        popup.open()

    def _delete_task(self, task_id, popup):
        popup.dismiss()
        self.app_state.database.delete_task(task_id)
        self.refresh()
