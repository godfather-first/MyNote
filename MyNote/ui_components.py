"""Reusable Kivy UI components for MyNote."""

from __future__ import annotations

from datetime import date
from functools import partial

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
from priority import PRIORITY_OPTIONS, priority_label, priority_option


class RoundedPanel(BoxLayout):
    """A lightweight rounded background wrapper."""

    def __init__(
        self,
        bg_color=(1, 1, 1, 1),
        radius: float | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._bg_color = bg_color
        self._radius = dp(8) if radius is None else radius
        with self.canvas.before:
            self._color = Color(*self._bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def set_bg_color(self, color):
        self._bg_color = color
        self._color.rgba = color

    def _update_canvas(self, *_args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class StableTextInput(TextInput):
    """Text input that keeps focus stable inside mobile scrollable forms."""

    def __init__(self, **kwargs):
        kwargs.setdefault("unfocus_on_touch", False)
        super().__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.focus = True
        return super().on_touch_down(touch)


class FormScrollView(ScrollView):
    """ScrollView that lets nested TextInput widgets receive taps first."""

    def on_touch_down(self, touch):
        text_input = self._text_input_at(touch)
        if text_input is not None:
            return text_input.on_touch_down(touch)
        return super().on_touch_down(touch)

    def _text_input_at(self, touch):
        for widget in self.walk(restrict=True):
            if isinstance(widget, TextInput) and widget.collide_point(*touch.pos):
                return widget
        return None


class DatePickerField(BoxLayout):
    """Date text field with a calendar picker button."""

    def __init__(self, label_text: str = "截止日期", initial_date: str | None = None, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(4), **kwargs)
        self.size_hint_y = None
        self.height = dp(74)
        self._selected_date = date.today()
        self._visible_year = self._selected_date.year
        self._visible_month = self._selected_date.month
        self._popup: Popup | None = None
        self._month_label: Label | None = None
        self._days_grid: GridLayout | None = None

        caption = Label(
            text=label_text,
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            color=(0.34, 0.34, 0.34, 1),
            font_size=dp(12),
            font_name=FONT_NAME,
        )
        caption.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))

        field_row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6))
        self.input = StableTextInput(
            text="",
            hint_text="YYYY-MM-DD",
            multiline=False,
            padding=(dp(12), dp(14), dp(12), dp(10)),
            font_name=FONT_NAME,
        )
        self.button = Button(
            text="选择",
            size_hint_x=None,
            width=dp(62),
            size_hint_y=None,
            height=dp(52),
            background_normal="",
            background_color=(0.26, 0.42, 0.64, 1),
            color=(1, 1, 1, 1),
            font_size=dp(14),
            font_name=FONT_NAME,
        )
        self.button.bind(on_release=lambda *_: self.open_picker())
        field_row.add_widget(self.input)
        field_row.add_widget(self.button)

        self.add_widget(caption)
        self.add_widget(field_row)
        self.set_date(initial_date or today_text())

    @property
    def date_text(self) -> str:
        return self.input.text.strip()

    def get_date(self) -> str:
        return self.date_text

    def set_date(self, value: str | None) -> None:
        normalized = normalize_date_text(value or today_text())
        year, month, day = (int(part) for part in normalized.split("-"))
        self._selected_date = date(year, month, day)
        self._visible_year = year
        self._visible_month = month
        self.input.text = self._selected_date.strftime("%Y-%m-%d")
        if self._popup:
            self._refresh_calendar()

    def open_picker(self):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))

        header = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        for text, delta in (("<<", -12), ("<", -1)):
            button = Button(text=text, font_name=FONT_NAME, size_hint_x=None, width=dp(48))
            button.bind(on_release=partial(self._change_month, delta))
            header.add_widget(button)

        self._month_label = Label(
            text="",
            color=(0.12, 0.12, 0.12, 1),
            bold=True,
            font_size=dp(17),
            font_name=FONT_NAME,
        )
        header.add_widget(self._month_label)

        for text, delta in ((">", 1), (">>", 12)):
            button = Button(text=text, font_name=FONT_NAME, size_hint_x=None, width=dp(48))
            button.bind(on_release=partial(self._change_month, delta))
            header.add_widget(button)
        content.add_widget(header)

        week_row = GridLayout(cols=7, size_hint_y=None, height=dp(26), spacing=dp(2))
        for text in ("一", "二", "三", "四", "五", "六", "日"):
            week_row.add_widget(
                Label(
                    text=text,
                    color=(0.42, 0.42, 0.42, 1),
                    font_size=dp(12),
                    font_name=FONT_NAME,
                )
            )
        content.add_widget(week_row)

        self._days_grid = GridLayout(cols=7, spacing=dp(4), size_hint_y=None, height=dp(252))
        content.add_widget(self._days_grid)

        footer = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        today = Button(text="今天", font_name=FONT_NAME)
        close = Button(text="关闭", font_name=FONT_NAME)
        today.bind(on_release=lambda *_: self._select_date(date.today()))
        close.bind(on_release=lambda *_: self._popup.dismiss() if self._popup else None)
        footer.add_widget(today)
        footer.add_widget(close)
        content.add_widget(footer)

        self._popup = Popup(
            title="选择截止日期",
            content=content,
            size_hint=(0.92, None),
            height=dp(430),
            title_font=FONT_NAME,
            auto_dismiss=True,
        )
        self._refresh_calendar()
        self._popup.open()
        return self._popup

    def _change_month(self, delta, *_args):
        self._visible_year, self._visible_month = shift_month(
            self._visible_year,
            self._visible_month,
            delta,
        )
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
            bg_color = (0.18, 0.55, 0.28, 1) if selected else (0.92, 0.93, 0.90, 1)
            if is_today and not selected:
                bg_color = (0.76, 0.86, 0.96, 1)
            button = Button(
                text=str(day),
                background_normal="",
                background_color=bg_color,
                color=(1, 1, 1, 1) if selected else (0.12, 0.12, 0.12, 1),
                font_name=FONT_NAME,
            )
            button.bind(on_release=partial(self._select_date, candidate))
            self._days_grid.add_widget(button)

    def _select_date(self, selected: date, *_args):
        self.set_date(selected.strftime("%Y-%m-%d"))
        if self._popup:
            self._popup.dismiss()


def build_priority_popup_content(selected_label: str, on_select, on_close) -> BoxLayout:
    """Build priority popup content with stable trigger paths for every option."""

    content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
    content.add_widget(
        Label(
            text="选择任务优先级",
            size_hint_y=None,
            height=dp(32),
            color=(0.12, 0.12, 0.12, 1),
            bold=True,
            font_size=dp(17),
            font_name=FONT_NAME,
        )
    )

    option_buttons = []
    for item in PRIORITY_OPTIONS:
        selected = item["label"] == selected_label
        option = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8))
        button = Button(
            text=item["label"],
            size_hint_x=None,
            width=dp(76),
            background_normal="",
            background_color=item["color"] if selected else (0.90, 0.91, 0.88, 1),
            color=(1, 1, 1, 1) if selected else (0.12, 0.12, 0.12, 1),
            font_name=FONT_NAME,
        )
        button.bind(on_release=partial(on_select, item["label"]))
        detail = Label(
            text=item["description"],
            halign="left",
            valign="middle",
            color=(0.30, 0.30, 0.30, 1),
            font_size=dp(13),
            font_name=FONT_NAME,
        )
        detail.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))
        option.add_widget(button)
        option.add_widget(detail)
        content.add_widget(option)
        option_buttons.append(button)

    close = Button(
        text="关闭",
        size_hint_y=None,
        height=dp(44),
        font_name=FONT_NAME,
    )
    close.bind(on_release=on_close)
    content.add_widget(close)
    content.priority_option_buttons = option_buttons
    return content


class PriorityPicker(BoxLayout):
    """Button field that opens the priority popup."""

    def __init__(self, initial_value: int = 0, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(4), **kwargs)
        self.size_hint_y = None
        self.height = dp(74)
        self.priority_value = initial_value
        self._popup: Popup | None = None

        caption = Label(
            text="优先级",
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            color=(0.34, 0.34, 0.34, 1),
            font_size=dp(12),
            font_name=FONT_NAME,
        )
        caption.bind(size=lambda widget, _value: setattr(widget, "text_size", widget.size))
        self.button = Button(
            text="",
            size_hint_y=None,
            height=dp(52),
            background_normal="",
            background_color=(0.97, 0.97, 0.95, 1),
            color=(0.12, 0.12, 0.12, 1),
            font_size=dp(16),
            font_name=FONT_NAME,
        )
        self.button.bind(on_release=lambda *_: self.open_popup())
        self.add_widget(caption)
        self.add_widget(self.button)
        self.set_priority(initial_value)

    @property
    def label(self) -> str:
        return priority_label(self.priority_value)

    def set_priority(self, value: int | str) -> None:
        if isinstance(value, str):
            value = priority_option(value)["value"]
        self.priority_value = int(value)
        item = priority_option(self.label)
        self.button.text = f"优先级：{self.label}"
        self.button.background_color = item["color"]
        self.button.color = (1, 1, 1, 1)

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
            height=dp(330),
            title_font=FONT_NAME,
            auto_dismiss=True,
        )
        self._popup.open()
        return self._popup
