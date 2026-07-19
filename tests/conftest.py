import os
import sys
from pathlib import Path

os.environ.setdefault("KIVY_NO_ARGS", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "MyNote"))

from font_utils import register_chinese_font

register_chinese_font()
