"""Chinese font setup for Kivy widgets."""

from __future__ import annotations

from pathlib import Path

from kivy.core.text import LabelBase
from kivy.uix.spinner import Spinner, SpinnerOption


FONT_NAME = "MyNoteCN"


def register_chinese_font() -> str:
    """Register a CJK-capable font and return the Kivy font name."""

    base_dir = Path(__file__).resolve().parent
    candidates = [
        base_dir / "assets" / "NotoSansCJKsc-Regular.otf",
        base_dir / "assets" / "SourceHanSansSC-Regular.otf",
        base_dir / "assets" / "msyh.ttc",
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("/system/fonts/NotoSansCJK-Regular.ttc"),
        Path("/system/fonts/NotoSansSC-Regular.otf"),
        Path("/system/fonts/DroidSansFallback.ttf"),
    ]

    for font_path in candidates:
        if font_path.exists():
            LabelBase.register(name=FONT_NAME, fn_regular=str(font_path))
            return FONT_NAME

    return "Roboto"


class ChineseSpinnerOption(SpinnerOption):
    """Spinner dropdown button with Chinese font preset."""

    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", FONT_NAME)
        super().__init__(**kwargs)


class ChineseSpinner(Spinner):
    """Spinner that uses Chinese font in both the button and dropdown items."""

    def __init__(self, **kwargs):
        kwargs.setdefault("option_cls", ChineseSpinnerOption)
        super().__init__(**kwargs)

