"""Font registration with a stable app font name."""

from __future__ import annotations

from pathlib import Path

from kivy.core.text import LabelBase
from kivy.resources import resource_find


FONT_NAME = "MyNoteCN"

ASSET_FONT_NAMES = (
    "NotoSansCJKsc-Regular.otf",
    "SourceHanSansSC-Regular.otf",
    "NotoSansSC-Regular.otf",
    "DroidSansFallback.ttf",
)

SYSTEM_FONT_PATHS = (
    Path("/system/fonts/NotoSansCJK-Regular.ttc"),
    Path("/system/fonts/NotoSansSC-Regular.otf"),
    Path("/system/fonts/NotoSansCJKsc-Regular.otf"),
    Path("/system/fonts/SourceHanSansSC-Regular.otf"),
    Path("/system/fonts/DroidSansFallback.ttf"),
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
)


def register_chinese_font() -> str:
    """Register FONT_NAME even when a real CJK font is unavailable."""

    base_dir = Path(__file__).resolve().parent
    candidates = [base_dir / "assets" / name for name in ASSET_FONT_NAMES]
    candidates.extend(SYSTEM_FONT_PATHS)

    for font_path in candidates:
        if not font_path.exists():
            continue
        try:
            LabelBase.register(name=FONT_NAME, fn_regular=str(font_path))
            return FONT_NAME
        except Exception:
            continue

    fallback = resource_find("data/fonts/DejaVuSans.ttf")
    if fallback:
        LabelBase.register(name=FONT_NAME, fn_regular=fallback)
        return FONT_NAME
    return "Roboto"
