"""Task detail, edit, completion, and delete screen."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

from date_utils import normalize_date_text, today_text
from font_utils import FONT_NAME
from models import DEFAULT_CATEGORY, STATUS_ACTIVE, STATUS_DONE
from priority import PRIORITY_VALUES
from ui_components import (
    DANGER,
    PRIMARY,
    SUCCESS,
    TEXT,
    DatePickerField,
    FormScrollView,
    MobileButton,
    MobileTextInput,
    PriorityPicker,
    bind_text_size,
)


class DetailScreen(Screen):
    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self.task_id = None
        self._status = STATUS_ACTIVE
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
        title = Label(text="任务详情", color=TEXT, bold=True, font_size=dp(22), font_name=FONT_NAME)
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
        self.status_button = MobileButton(text="标记完成", background_color=PRIMARY, color=(1, 1, 1, 1))
        self.status_button.bind(on_release=lambda *_: self._toggle_status())
        self.meta_label = bind_text_size(
            Label(
                text="",
                size_hint_y=None,
                height=dp(58),
                halign="left",
                valign="middle",
                color=(0.42, 0.42, 0.42, 1),
                font_size=dp(13),
                font_name=FONT_NAME,
            )
        )
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
        buttons = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8))
        save = MobileButton(text="保存", background_color=SUCCESS, color=(1, 1, 1, 1))
        delete = MobileButton(text="删除", background_color=DANGER, color=(1, 1, 1, 1))
        save.bind(on_release=lambda *_: self._save())
        delete.bind(on_release=lambda *_: self._confirm_delete())
        buttons.add_widget(save)
        buttons.add_widget(delete)

        for widget in (
            header,
            self.title_input,
            self.content_input,
            self.date_picker,
            self.priority_picker,
            self.category_input.parent,
            self.status_button,
            self.meta_label,
            self.error_label,
            buttons,
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
        field = MobileTextInput(hint_text="分类", multiline=False)
        box.add_widget(field)
        return field

    def load_task(self, task_id):
        self.task_id = task_id
        task = self.app_state.database.get_task(task_id)
        if task is None:
            self._back_home()
            return
        self.title_input.text = task.title
        self.content_input.text = task.content
        self.date_picker.set_date(task.due_date or today_text())
        self.priority_picker.set_priority(task.priority)
        self.category_input.text = task.category
        self._status = task.status
        self.meta_label.text = f"创建时间：{task.create_time}\n更新时间：{task.update_time}"
        self.error_label.text = ""
        self._refresh_status_button()

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
        saved = self.app_state.database.update_task(
            task_id=self.task_id,
            title=title,
            content=self.content_input.text.strip(),
            due_date=due_date,
            status=self._status,
            priority=self.priority_picker.priority_value,
            category=self.category_input.text.strip() or DEFAULT_CATEGORY,
        )
        if not saved:
            self.error_label.text = "任务不存在"
            return
        self._back_home()

    def _toggle_status(self):
        self._status = STATUS_ACTIVE if self._status == STATUS_DONE else STATUS_DONE
        self._refresh_status_button()

    def _refresh_status_button(self):
        if self._status == STATUS_DONE:
            self.status_button.text = "恢复为待办"
            self.status_button.background_color = (0.62, 0.56, 0.42, 1)
        else:
            self.status_button.text = "标记完成"
            self.status_button.background_color = PRIMARY

    def _confirm_delete(self):
        content = BoxLayout(orientation="vertical", spacing=dp(14), padding=dp(16))
        content.add_widget(Label(text="是否将该任务移入回收站？", color=TEXT, font_name=FONT_NAME))
        buttons = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8))
        cancel = MobileButton(text="取消", background_color=(0.82, 0.82, 0.78, 1), color=TEXT)
        confirm = MobileButton(text="移入回收站", background_color=DANGER, color=(1, 1, 1, 1))
        buttons.add_widget(cancel)
        buttons.add_widget(confirm)
        content.add_widget(buttons)
        popup = Popup(title="确认", content=content, size_hint=(0.82, None), height=dp(220), title_font=FONT_NAME)
        cancel.bind(on_release=popup.dismiss)
        confirm.bind(on_release=lambda *_: self._delete_task(popup))
        popup.open()

    def _delete_task(self, popup):
        popup.dismiss()
        if self.task_id is not None:
            self.app_state.database.delete_task(self.task_id)
        self._back_home()

    def _back_home(self):
        home = self.manager.get_screen("home")
        home.refresh()
        self.manager.current = "home"
