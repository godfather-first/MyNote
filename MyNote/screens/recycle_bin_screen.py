"""Recycle bin screen for recently deleted tasks."""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from font_utils import FONT_NAME
from ui_components import RoundedPanel


class DeletedTaskRow(RoundedPanel):
    """Deleted task row with restore action."""

    def __init__(self, task, on_restore, **kwargs):
        super().__init__(bg_color=(1, 1, 1, 1), **kwargs)
        self.task = task
        self.on_restore = on_restore
        self.orientation = "horizontal"
        self.spacing = dp(10)
        self.padding = (dp(14), dp(10), dp(12), dp(10))
        self.size_hint_y = None
        self.height = dp(96)

        info = BoxLayout(orientation="vertical", spacing=dp(3))
        title = Label(
            text=task.title,
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
            color=(0.12, 0.12, 0.12, 1),
            bold=True,
            font_size=dp(16),
            font_name=FONT_NAME,
        )
        title.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))

        meta = Label(
            text=f"原分类：{task.category} | 优先级：{task.priority_text} | 截止：{task.due_date or '无'}",
            size_hint_y=None,
            height=dp(26),
            halign="left",
            valign="middle",
            color=(0.34, 0.34, 0.34, 1),
            font_size=dp(12),
            font_name=FONT_NAME,
        )
        meta.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))

        deleted_time = Label(
            text=f"删除时间：{task.deleted_time}",
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            color=(0.58, 0.58, 0.58, 1),
            font_size=dp(12),
            font_name=FONT_NAME,
        )
        deleted_time.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))

        restore = Button(
            text="恢复",
            size_hint=(None, 1),
            width=dp(66),
            background_normal="",
            background_color=(0.18, 0.55, 0.28, 1),
            color=(1, 1, 1, 1),
            font_name=FONT_NAME,
        )
        restore.bind(on_release=lambda *_: self.on_restore(task.id))

        info.add_widget(title)
        info.add_widget(meta)
        info.add_widget(deleted_time)
        self.add_widget(info)
        self.add_widget(restore)


class RecycleBinScreen(Screen):
    """List deleted tasks retained for ten days."""

    def __init__(self, app_state, **kwargs):
        super().__init__(**kwargs)
        self.app_state = app_state
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=0)

        header = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(8), padding=(dp(12), dp(4)))
        back = Button(text="<", size_hint=(None, None), width=dp(56), height=dp(56), font_name=FONT_NAME)
        back.bind(on_release=lambda *_: self._back_home())
        title = Label(
            text="回收站",
            halign="left",
            valign="middle",
            color=(0.12, 0.12, 0.12, 1),
            font_size=dp(22),
            bold=True,
            font_name=FONT_NAME,
        )
        title.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))
        header.add_widget(back)
        header.add_widget(title)

        self.summary_label = Label(
            text="",
            size_hint_y=None,
            height=dp(34),
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

        root.add_widget(header)
        root.add_widget(self.summary_label)
        root.add_widget(self.scroll)
        self.add_widget(root)

    def on_pre_enter(self, *_args):
        self.refresh()

    def refresh(self):
        self.app_state.database.purge_expired_deleted_tasks()
        deleted_tasks = self.app_state.database.get_deleted_tasks()
        self.summary_label.text = f"保留最近 10 天删除的任务，共 {len(deleted_tasks)} 条"
        self.list_box.clear_widgets()

        if not deleted_tasks:
            self.list_box.add_widget(
                Label(
                    text="回收站为空",
                    size_hint_y=None,
                    height=dp(140),
                    color=(0.5, 0.5, 0.5, 1),
                    font_size=dp(16),
                    font_name=FONT_NAME,
                )
            )
            return

        for task in deleted_tasks:
            self.list_box.add_widget(
                DeletedTaskRow(
                    task=task,
                    on_restore=self._restore_task,
                )
            )

    def _restore_task(self, deleted_task_id):
        self.app_state.database.restore_deleted_task(deleted_task_id)
        self.refresh()

    def _back_home(self):
        home = self.manager.get_screen("home")
        home.refresh()
        self.manager.current = "home"
