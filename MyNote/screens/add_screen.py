"""Screen for creating a new task."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from date_utils import normalize_date_text, today_text
from font_utils import FONT_NAME
from priority import PRIORITY_VALUES
from ui_components import DatePickerField, PriorityPicker


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
            size_hint_y=None,
        )
        root.bind(minimum_height=root.setter("height"))

        header = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        back = Button(text="<", size_hint_x=None, width=dp(52), font_name=FONT_NAME)
        back.bind(on_release=lambda *_: self._back_home())
        title = Label(
            text="新增任务",
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
            hint_text="分类，例如 工作/生活",
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

        self.error_label = Label(
            text="",
            size_hint_y=None,
            height=dp(28),
            color=(0.75, 0.18, 0.16, 1),
            font_name=FONT_NAME,
        )

        save = Button(
            text="保存",
            size_hint_y=None,
            height=dp(54),
            background_normal="",
            background_color=(0.18, 0.55, 0.28, 1),
            color=(1, 1, 1, 1),
            font_size=dp(18),
            font_name=FONT_NAME,
        )
        save.bind(on_release=lambda *_: self._save())

        root.add_widget(header)
        root.add_widget(self.title_input)
        root.add_widget(self.content_input)
        root.add_widget(self.date_picker)
        root.add_widget(option_row)
        root.add_widget(self.error_label)
        root.add_widget(save)
        root.add_widget(Label(size_hint_y=None, height=dp(12), font_name=FONT_NAME))

        scroll = ScrollView()
        scroll.add_widget(root)
        self.add_widget(scroll)

    def on_pre_enter(self, *_args):
        self.title_input.text = ""
        self.content_input.text = ""
        self.date_picker.set_date(today_text())
        self.priority_picker.set_priority(PRIORITY_VALUES["普通"])
        self.category_input.text = ""
        self.error_label.text = ""

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

        self.app_state.database.add_task(
            title=title,
            content=self.content_input.text.strip(),
            due_date=due_date,
            priority=self.priority_picker.priority_value,
            category=self.category_input.text.strip() or "默认",
        )
        self._back_home()

    def _back_home(self):
        self.manager.current = "home"
