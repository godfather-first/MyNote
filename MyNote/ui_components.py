"""Reusable mobile-first Kivy widgets for MyNote."""

from __future__ import annotations

from datetime import date
from functools import partial

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from date_utils import days_in_month, normalize_date_text, safe_date, shift_month, today_text
from font_utils import FONT_NAME
from priority import PRIORITY_OPTIONS, clamp_priority, priority_label, priority_option


BG = (0.96, 0.96, 0.94, 1)
PAPER = (1, 1, 1, 1)
TEXT = (0.12, 0.12, 0.12, 1)
MUTED = (0.42, 0.42, 0.42, 1)
PRIMARY = (0.25, 0.43, 0.68, 1)
SUCCESS = (0.18, 0.55, 0.28, 1)
DANGER = (0.76, 0.18, 0.16, 1)
WARNING = (0.86, 0.53, 0.12, 1)
TOUCH_HEIGHT = dp(58)


def bind_text_size(label: Label) -> Label:
    label.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))
    return label


class RoundedPanel(BoxLayout):
    """Simple rounded white/card background."""

    def __init__(self, bg_color=PAPER, radius=None, **kwargs):
        super().__init__(**kwargs)
        self._bg_color = bg_color
        self._radius = dp(8) if radius is None else radius
        with self.canvas.before:
            self._color = Color(*self._bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def set_bg_color(self, color) -> None:
        self._bg_color = color
        self._color.rgba = color

    def _update_canvas(self, *_args) -> None:
        self._rect.pos = self.pos
        self._rect.size = self.size


class MobileButton(Button):
    """Button with a reliable mobile-sized touch target."""

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", TOUCH_HEIGHT)
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("font_name", FONT_NAME)
        kwargs.setdefault("font_size", dp(16))
        super().__init__(**kwargs)


class MobileTextInput(TextInput):
    """TextInput tuned for direct mobile tapping and no copy/paste overlay."""

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", TOUCH_HEIGHT)
        kwargs.setdefault("padding", (dp(14), dp(16), dp(14), dp(10)))
        kwargs.setdefault("font_name", FONT_NAME)
        kwargs.setdefault("unfocus_on_touch", False)
        kwargs.setdefault("use_bubble", False)
        kwargs.setdefault("use_handles", False)
        kwargs.setdefault("allow_copy", False)
        super().__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.focus = True
            self.cancel_selection()
        return super().on_touch_down(touch)

    def on_double_tap(self):
        self.cancel_selection()
        return True

    def on_triple_tap(self):
        self.cancel_selection()
        return True

    def copy(self, data=""):
        return ""

    def cut(self):
        self.cancel_selection()
        return ""

    def paste(self):
        self.cancel_selection()
        return None

    def select_all(self):
        self.cancel_selection()
        return None

    def select_text(self, start, end):
        self.cancel_selection()
        return None

    def _show_cut_copy_paste(self, *args, **kwargs):
        self.cancel_selection()
        return None

    def _show_handles(self, *args, **kwargs):
        self.cancel_selection()
        return None

    def _handle_command(self, command):
        if command in ("copy", "cut", "paste", "selectall"):
            self.cancel_selection()
            return True
        handler = getattr(super(), "_handle_command", None)
        return handler(command) if handler else False

    def _handle_shortcut(self, key):
        if key in ("a", "c", "v", "x"):
            self.cancel_selection()
            return True
        handler = getattr(super(), "_handle_shortcut", None)
        return handler(key) if handler else False


StableTextInput = MobileTextInput


class FormScrollView(ScrollView):
    """Scrolls focused fields into view without changing touch dispatch."""

    def register_focus_widgets(self, *widgets):
        for widget in widgets:
            widget.bind(focus=self._scroll_to_focused)

    def _scroll_to_focused(self, widget, focused):
        if focused:
            Clock.schedule_once(lambda *_: self.scroll_to(widget, padding=dp(160), animate=True), 0.08)


class DatePickerField(BoxLayout):
    """Strict date input with a touch-friendly calendar popup."""

    def __init__(self, label_text="截止日期", initial_date=None, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(86), **kwargs)
        self._selected_date = date.today()
        self._visible_year = self._selected_date.year
        self._visible_month = self._selected_date.month
        self._popup = None
        self._month_label = None
        self._days_grid = None

        self.add_widget(
            bind_text_size(
                Label(
                    text=label_text,
                    size_hint_y=None,
                    height=dp(20),
                    halign="left",
                    valign="middle",
                    color=MUTED,
                    font_size=dp(12),
                    font_name=FONT_NAME,
                )
            )
        )

        row = BoxLayout(size_hint_y=None, height=TOUCH_HEIGHT, spacing=dp(8))
        self.input = MobileTextInput(text="", hint_text="YYYY-MM-DD", multiline=False)
        self.button = MobileButton(
            text="选择",
            size_hint_x=None,
            width=dp(82),
            background_color=PRIMARY,
            color=(1, 1, 1, 1),
        )
        self.button.bind(on_release=lambda *_: self.open_picker())
        row.add_widget(self.input)
        row.add_widget(self.button)
        self.add_widget(row)
        self.set_date(initial_date or today_text())

    @property
    def date_text(self) -> str:
        return self.input.text.strip()

    def get_date(self) -> str:
        return self.date_text

    def set_date(self, value: str | None) -> None:
        try:
            normalized = normalize_date_text(value or today_text())
        except ValueError:
            normalized = today_text()
        year, month, day = (int(part) for part in normalized.split("-"))
        self._selected_date = date(year, month, day)
        self._visible_year = year
        self._visible_month = month
        self.input.text = normalized
        if self._popup:
            self._refresh_calendar()

    def open_picker(self):
        self._sync_valid_input_date()
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))

        header = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(6))
        for text, delta in (("<<", -12), ("<", -1)):
            button = MobileButton(text=text, size_hint_x=None, width=dp(58))
            button.bind(on_release=partial(self._change_month, delta))
            header.add_widget(button)
        self._month_label = Label(
            text="",
            color=TEXT,
            bold=True,
            font_size=dp(17),
            font_name=FONT_NAME,
        )
        header.add_widget(self._month_label)
        for text, delta in ((">", 1), (">>", 12)):
            button = MobileButton(text=text, size_hint_x=None, width=dp(58))
            button.bind(on_release=partial(self._change_month, delta))
            header.add_widget(button)
        content.add_widget(header)

        week_row = GridLayout(cols=7, size_hint_y=None, height=dp(28), spacing=dp(2))
        for text in ("一", "二", "三", "四", "五", "六", "日"):
            week_row.add_widget(Label(text=text, color=MUTED, font_size=dp(12), font_name=FONT_NAME))
        content.add_widget(week_row)

        self._days_grid = GridLayout(cols=7, spacing=dp(4), size_hint_y=None, height=dp(300))
        content.add_widget(self._days_grid)

        footer = BoxLayout(size_hint_y=None, height=TOUCH_HEIGHT, spacing=dp(8))
        today = MobileButton(text="今天", background_color=SUCCESS, color=(1, 1, 1, 1))
        close = MobileButton(text="关闭", background_color=(0.82, 0.82, 0.78, 1), color=TEXT)
        today.bind(on_release=lambda *_: self._select_date(date.today()))
        close.bind(on_release=lambda *_: self._popup.dismiss() if self._popup else None)
        footer.add_widget(today)
        footer.add_widget(close)
        content.add_widget(footer)

        self._popup = Popup(
            title="选择截止日期",
            content=content,
            size_hint=(0.92, None),
            height=dp(515),
            title_font=FONT_NAME,
            auto_dismiss=True,
        )
        self._refresh_calendar()
        self._popup.open()
        return self._popup

    def _sync_valid_input_date(self):
        try:
            self.set_date(normalize_date_text(self.date_text))
        except ValueError:
            return

    def _change_month(self, delta, *_args):
        self._visible_year, self._visible_month = shift_month(self._visible_year, self._visible_month, delta)
        self._refresh_calendar()

    def _refresh_calendar(self):
        if not self._month_label or not self._days_grid:
            return
        self._month_label.text = f"{self._visible_year}年{self._visible_month:02d}月"
        self._days_grid.clear_widgets()
        first_weekday = date(self._visible_year, self._visible_month, 1).weekday()
        total_days = days_in_month(self._visible_year, self._visible_month)
        for index in range(42):
            day = index - first_weekday + 1
            if day < 1 or day > total_days:
                self._days_grid.add_widget(Label(text="", font_name=FONT_NAME))
                continue
            candidate = safe_date(self._visible_year, self._visible_month, day)
            selected = candidate == self._selected_date
            is_today = candidate == date.today()
            bg_color = SUCCESS if selected else (0.91, 0.92, 0.88, 1)
            if is_today and not selected:
                bg_color = (0.78, 0.87, 0.96, 1)
            button = MobileButton(
                text=str(day),
                background_color=bg_color,
                color=(1, 1, 1, 1) if selected else TEXT,
                font_size=dp(14),
            )
            button.bind(on_release=partial(self._select_date, candidate))
            self._days_grid.add_widget(button)

    def _select_date(self, selected: date, *_args):
        self.set_date(selected.strftime("%Y-%m-%d"))
        if self._popup:
            self._popup.dismiss()


def build_priority_popup_content(selected_label: str, on_select, on_close) -> BoxLayout:
    content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
    content.add_widget(
        Label(
            text="选择任务优先级",
            size_hint_y=None,
            height=dp(34),
            color=TEXT,
            bold=True,
            font_size=dp(17),
            font_name=FONT_NAME,
        )
    )
    option_buttons = []
    for item in PRIORITY_OPTIONS:
        selected = item["label"] == selected_label
        row = BoxLayout(size_hint_y=None, height=dp(66), spacing=dp(8))
        button = MobileButton(
            text=item["label"],
            size_hint_x=None,
            width=dp(88),
            background_color=item["color"] if selected else (0.90, 0.91, 0.88, 1),
            color=(1, 1, 1, 1) if selected else TEXT,
        )
        button.bind(on_release=partial(on_select, item["label"]))
        detail = bind_text_size(
            Label(
                text=item["description"],
                halign="left",
                valign="middle",
                color=MUTED,
                font_size=dp(13),
                font_name=FONT_NAME,
            )
        )
        row.add_widget(button)
        row.add_widget(detail)
        content.add_widget(row)
        option_buttons.append(button)
    close = MobileButton(text="关闭", background_color=(0.82, 0.82, 0.78, 1), color=TEXT)
    close.bind(on_release=on_close)
    content.add_widget(close)
    content.priority_option_buttons = option_buttons
    return content


class PriorityPicker(BoxLayout):
    """Large button field that opens a three-option priority popup."""

    def __init__(self, initial_value=0, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(4), size_hint_y=None, height=dp(86), **kwargs)
        self.priority_value = clamp_priority(initial_value)
        self._popup = None
        self.add_widget(
            bind_text_size(
                Label(
                    text="优先级",
                    size_hint_y=None,
                    height=dp(20),
                    halign="left",
                    valign="middle",
                    color=MUTED,
                    font_size=dp(12),
                    font_name=FONT_NAME,
                )
            )
        )
        self.button = MobileButton(text="", background_color=PRIMARY, color=(1, 1, 1, 1))
        self.button.bind(on_release=lambda *_: self.open_popup())
        self.add_widget(self.button)
        self.set_priority(self.priority_value)

    @property
    def label(self) -> str:
        return priority_label(self.priority_value)

    def set_priority(self, value) -> None:
        self.priority_value = clamp_priority(value)
        item = priority_option(self.priority_value)
        self.button.text = f"优先级：{item['label']}"
        self.button.background_color = item["color"]

    def open_popup(self):
        def select(label, *_args):
            self.set_priority(label)
            if self._popup:
                self._popup.dismiss()

        def close(*_args):
            if self._popup:
                self._popup.dismiss()

        content = build_priority_popup_content(self.label, select, close)
        self._popup = Popup(
            title="任务优先级",
            content=content,
            size_hint=(0.86, None),
            height=dp(390),
            title_font=FONT_NAME,
            auto_dismiss=True,
        )
        self._popup.open()
        return self._popup
