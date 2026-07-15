"""Task detail and edit screen."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput


class DetailScreen(Screen):
    """Edit, complete, and delete a task."""

    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.task_id = None
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
            text="任务详情",
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
            hint_text="截止日期",
            multiline=False,
            size_hint_y=None,
            height=dp(52),
            padding=(dp(12), dp(14), dp(12), dp(10)),
        )

        status_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.status_checkbox = CheckBox(size_hint_x=None, width=dp(48))
        status_label = Label(
            text="已完成",
            color=(0.12, 0.12, 0.12, 1),
            halign="left",
            valign="middle",
        )
        status_label.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))
        status_row.add_widget(self.status_checkbox)
        status_row.add_widget(status_label)

        self.meta_label = Label(
            text="",
            size_hint_y=None,
            height=dp(54),
            color=(0.45, 0.45, 0.45, 1),
            font_size=dp(13),
        )
        self.error_label = Label(
            text="",
            size_hint_y=None,
            height=dp(28),
            color=(0.75, 0.18, 0.16, 1),
        )

        buttons = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8))
        save = Button(
            text="保存",
            background_normal="",
            background_color=(0.18, 0.55, 0.28, 1),
            color=(1, 1, 1, 1),
        )
        delete = Button(
            text="删除",
            background_normal="",
            background_color=(0.75, 0.18, 0.16, 1),
            color=(1, 1, 1, 1),
        )
        save.bind(on_release=lambda *_: self._save())
        delete.bind(on_release=lambda *_: self._confirm_delete())
        buttons.add_widget(save)
        buttons.add_widget(delete)

        root.add_widget(header)
        root.add_widget(self.title_input)
        root.add_widget(self.content_input)
        root.add_widget(self.date_input)
        root.add_widget(status_row)
        root.add_widget(self.meta_label)
        root.add_widget(self.error_label)
        root.add_widget(buttons)
        root.add_widget(Label())
        self.add_widget(root)

    def load_task(self, task_id):
        self.task_id = task_id
        task = self.app_state.database.get_task(task_id)
        if task is None:
            self._back_home()
            return
        self.title_input.text = task.title
        self.content_input.text = task.content
        self.date_input.text = task.due_date
        self.status_checkbox.active = task.is_done
        self.error_label.text = ""
        self.meta_label.text = (
            f"创建时间: {task.create_time}\n"
            f"更新时间: {task.update_time}"
        )

    def _save(self):
        title = self.title_input.text.strip()
        if not title:
            self.error_label.text = "任务标题不能为空"
            return

        self.app_state.database.update_task(
            task_id=self.task_id,
            title=title,
            content=self.content_input.text.strip(),
            due_date=self.date_input.text.strip(),
            status=1 if self.status_checkbox.active else 0,
        )
        self._back_home()

    def _confirm_delete(self):
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
        confirm.bind(on_release=lambda *_: self._delete_task(popup))
        popup.open()

    def _delete_task(self, popup):
        popup.dismiss()
        self.app_state.database.delete_task(self.task_id)
        self._back_home()

    def _back_home(self):
        self.manager.current = "home"
