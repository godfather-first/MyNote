"""Task creation screen."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from date_utils import normalize_date_text, today_text
from font_utils import FONT_NAME
from models import DEFAULT_CATEGORY
from priority import PRIORITY_VALUES
from ui_components import (
    DANGER,
    SUCCESS,
    TEXT,
    DatePickerField,
    FormScrollView,
    MobileButton,
    MobileTextInput,
    PriorityPicker,
    bind_text_size,
)


class AddScreen(Screen):
    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(
            orientation="vertical",
            spacing=dp(14),
            padding=(dp(16), dp(16), dp(16), dp(28)),
            size_hint_y=None,
        )
        root.bind(minimum_height=root.setter("height"))

        header = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(8))
        back = MobileButton(text="<", size_hint_x=None, width=dp(60), background_color=(0.28, 0.28, 0.28, 1), color=(1, 1, 1, 1))
        back.bind(on_release=lambda *_: self._back_home())
        title = Label(text="新增任务", color=TEXT, bold=True, font_size=dp(22), font_name=FONT_NAME)
        header.add_widget(back)
        header.add_widget(title)

        self.title_input = MobileTextInput(hint_text="任务标题 *", multiline=False)
        self.content_input = MobileTextInput(
            hint_text="备注",
            multiline=True,
            height=dp(150),
            padding=(dp(14), dp(14), dp(14), dp(14)),
        )
        self.date_picker = DatePickerField(initial_date=today_text())
        self.priority_picker = PriorityPicker(initial_value=PRIORITY_VALUES["普通"])
        self.category_input = self._build_category_input()
        self.error_label = bind_text_size(
            Label(
                text="",
                size_hint_y=None,
                height=dp(30),
                halign="left",
                valign="middle",
                color=DANGER,
                font_size=dp(13),
                font_name=FONT_NAME,
            )
        )
        save = MobileButton(text="保存", background_color=SUCCESS, color=(1, 1, 1, 1), font_size=dp(18))
        save.bind(on_release=lambda *_: self._save())

        for widget in (
            header,
            self.title_input,
            self.content_input,
            self.date_picker,
            self.priority_picker,
            self.category_input.parent,
            self.error_label,
            save,
            Label(size_hint_y=None, height=dp(190), font_name=FONT_NAME),
        ):
            root.add_widget(widget)

        scroll = FormScrollView(do_scroll_x=False, scroll_distance=dp(32), scroll_timeout=420)
        scroll.add_widget(root)
        scroll.register_focus_widgets(
            self.title_input,
            self.content_input,
            self.date_picker.input,
            self.category_input,
        )
        self.add_widget(scroll)

    def _build_category_input(self):
        box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(86))
        box.add_widget(
            bind_text_size(
                Label(
                    text="分类",
                    size_hint_y=None,
                    height=dp(20),
                    halign="left",
                    valign="middle",
                    color=(0.42, 0.42, 0.42, 1),
                    font_size=dp(12),
                    font_name=FONT_NAME,
                )
            )
        )
        field = MobileTextInput(hint_text="分类，例如 工作/生活", multiline=False)
        box.add_widget(field)
        return field

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
            category=self.category_input.text.strip() or DEFAULT_CATEGORY,
        )
        self._back_home()

    def _back_home(self):
        home = self.manager.get_screen("home")
        home.refresh()
        self.manager.current = "home"
