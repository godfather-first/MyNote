"""Task detail and edit screen."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from date_utils import normalize_date_text, today_text
from font_utils import FONT_NAME
from priority import PRIORITY_LABELS, PRIORITY_VALUES
from ui_components import DatePickerField, PriorityPicker


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
            size_hint_y=None,
        )
        root.bind(minimum_height=root.setter("height"))

        header = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        back = Button(text="<", size_hint_x=None, width=dp(52), font_name=FONT_NAME)
        back.bind(on_release=lambda *_: self._back_home())
        title = Label(
            text="任务详情",
            color=(0.12, 0.12, 0.12, 1),
            font_size=dp(22),
            bold=True,
            font_name=FONT_NAME,
        )
        header.add_widget(back)
        header.add_widget(title)

        self.title_input = TextInput(
            hint_text="任务标题 *",
            multiline=False,
            size_hint_y=None,
            height=dp(52),
            padding=(dp(12), dp(14), dp(12), dp(10)),
            font_name=FONT_NAME,
        )
        self.content_input = TextInput(
            hint_text="备注",
            multiline=True,
            size_hint_y=None,
            height=dp(130),
            padding=(dp(12), dp(12), dp(12), dp(12)),
            font_name=FONT_NAME,
        )
        self.date_picker = DatePickerField(initial_date=today_text())

        option_row = BoxLayout(size_hint_y=None, height=dp(74), spacing=dp(8))
        self.priority_picker = PriorityPicker(initial_value=PRIORITY_VALUES["普通"])
        category_box = BoxLayout(orientation="vertical", spacing=dp(4))
        category_label = Label(
            text="分类",
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            color=(0.34, 0.34, 0.34, 1),
            font_size=dp(12),
            font_name=FONT_NAME,
        )
        category_label.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))
        self.category_input = TextInput(
            hint_text="分类",
            multiline=False,
            size_hint_y=None,
            height=dp(52),
            padding=(dp(12), dp(14), dp(12), dp(10)),
            font_name=FONT_NAME,
        )
        category_box.add_widget(category_label)
        category_box.add_widget(self.category_input)
        option_row.add_widget(self.priority_picker)
        option_row.add_widget(category_box)

        self.status_button = Button(
            text="标记完成",
            size_hint_y=None,
            height=dp(46),
            background_normal="",
            background_color=(0.26, 0.42, 0.64, 1),
            color=(1, 1, 1, 1),
            font_name=FONT_NAME,
        )
        self.status_button.bind(on_release=lambda *_: self._toggle_status())
        self._is_done = False

        self.meta_label = Label(
            text="",
            size_hint_y=None,
            height=dp(54),
            color=(0.45, 0.45, 0.45, 1),
            font_size=dp(13),
            font_name=FONT_NAME,
        )
        self.error_label = Label(
            text="",
            size_hint_y=None,
            height=dp(28),
            color=(0.75, 0.18, 0.16, 1),
            font_name=FONT_NAME,
        )

        buttons = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8))
        save = Button(
            text="保存",
            background_normal="",
            background_color=(0.18, 0.55, 0.28, 1),
            color=(1, 1, 1, 1),
            font_name=FONT_NAME,
        )
        delete = Button(
            text="删除",
            background_normal="",
            background_color=(0.75, 0.18, 0.16, 1),
            color=(1, 1, 1, 1),
            font_name=FONT_NAME,
        )
        save.bind(on_release=lambda *_: self._save())
        delete.bind(on_release=lambda *_: self._confirm_delete())
        buttons.add_widget(save)
        buttons.add_widget(delete)

        root.add_widget(header)
        root.add_widget(self.title_input)
        root.add_widget(self.content_input)
        root.add_widget(self.date_picker)
        root.add_widget(option_row)
        root.add_widget(self.status_button)
        root.add_widget(self.meta_label)
        root.add_widget(self.error_label)
        root.add_widget(buttons)
        root.add_widget(Label(size_hint_y=None, height=dp(12), font_name=FONT_NAME))

        scroll = ScrollView()
        scroll.add_widget(root)
        self.add_widget(scroll)

    def load_task(self, task_id):
        self.task_id = task_id
        task = self.app_state.database.get_task(task_id)
        if task is None:
            self._back_home()
            return
        self.title_input.text = task.title
        self.content_input.text = task.content
        self.date_picker.set_date(task.due_date or today_text())
        self.priority_picker.set_priority(PRIORITY_LABELS.get(task.priority, "普通"))
        self.category_input.text = task.category
        self._is_done = task.is_done
        self._refresh_status_button()
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

        try:
            due_date = normalize_date_text(self.date_picker.get_date())
        except ValueError:
            self.error_label.text = "截止日期必须为 YYYY-MM-DD"
            return

        self.app_state.database.update_task(
            task_id=self.task_id,
            title=title,
            content=self.content_input.text.strip(),
            due_date=due_date,
            status=1 if self._is_done else 0,
            priority=self.priority_picker.priority_value,
            category=self.category_input.text.strip() or "默认",
        )
        self._back_home()

    def _toggle_status(self):
        self._is_done = not self._is_done
        self._refresh_status_button()

    def _refresh_status_button(self):
        if self._is_done:
            self.status_button.text = "恢复为待办"
            self.status_button.background_color = (0.62, 0.56, 0.42, 1)
        else:
            self.status_button.text = "标记完成"
            self.status_button.background_color = (0.26, 0.42, 0.64, 1)

    def _confirm_delete(self):
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(16))
        content.add_widget(
            Label(
                text="是否将该任务移入回收站？",
                color=(0.12, 0.12, 0.12, 1),
                font_name=FONT_NAME,
            )
        )

        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        cancel = Button(text="取消", font_name=FONT_NAME)
        confirm = Button(
            text="移入回收站",
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
        confirm.bind(on_release=lambda *_: self._delete_task(popup))
        popup.open()

    def _delete_task(self, popup):
        popup.dismiss()
        self.app_state.database.delete_task(self.task_id)
        self._back_home()

    def _back_home(self):
        self.manager.current = "home"
