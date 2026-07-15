"""Screen for creating a new task."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput


class AddScreen(Screen):
    """Task creation form."""

    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(
            orientation="vertical",
            padding=(dp(16), dp(16), dp(16), dp(16)),
            spacing=dp(12),
        )

        header = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        back = Button(text="<", size_hint_x=None, width=dp(52))
        back.bind(on_release=lambda *_: self._back_home())
        title = Label(
            text="新增任务",
            color=(0.12, 0.12, 0.12, 1),
            font_size=dp(22),
            bold=True,
        )
        header.add_widget(back)
        header.add_widget(title)

        self.title_input = TextInput(
            hint_text="任务标题 *",
            multiline=False,
            size_hint_y=None,
            height=dp(52),
            padding=(dp(12), dp(14), dp(12), dp(10)),
        )
        self.content_input = TextInput(
            hint_text="备注",
            multiline=True,
            size_hint_y=None,
            height=dp(140),
            padding=(dp(12), dp(12), dp(12), dp(12)),
        )
        self.date_input = TextInput(
            hint_text="截止日期，例如 2026-07-20",
            multiline=False,
            size_hint_y=None,
            height=dp(52),
            padding=(dp(12), dp(14), dp(12), dp(10)),
        )
        self.error_label = Label(
            text="",
            size_hint_y=None,
            height=dp(28),
            color=(0.75, 0.18, 0.16, 1),
        )

        save = Button(
            text="保存",
            size_hint_y=None,
            height=dp(54),
            background_normal="",
            background_color=(0.18, 0.55, 0.28, 1),
            color=(1, 1, 1, 1),
            font_size=dp(18),
        )
        save.bind(on_release=lambda *_: self._save())

        root.add_widget(header)
        root.add_widget(self.title_input)
        root.add_widget(self.content_input)
        root.add_widget(self.date_input)
        root.add_widget(self.error_label)
        root.add_widget(save)
        root.add_widget(Label())
        self.add_widget(root)

    def on_pre_enter(self, *_args):
        self.title_input.text = ""
        self.content_input.text = ""
        self.date_input.text = ""
        self.error_label.text = ""

    def _save(self):
        title = self.title_input.text.strip()
        if not title:
            self.error_label.text = "任务标题不能为空"
            return

        self.app_state.database.add_task(
            title=title,
            content=self.content_input.text.strip(),
            due_date=self.date_input.text.strip(),
        )
        self._back_home()

    def _back_home(self):
        self.manager.current = "home"
