"""Chinese font setup for Kivy widgets."""

from __future__ import annotations

from pathlib import Path

from kivy.core.text import LabelBase


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

