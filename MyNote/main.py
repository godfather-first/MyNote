"""MyNote application entry point."""

from __future__ import annotations

import ctypes
import sys
from dataclasses import dataclass


def enable_windows_dpi_awareness() -> None:
    """Prevent pointer/widget coordinate drift on scaled Windows desktops."""

    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


enable_windows_dpi_awareness()

from kivy.app import App
from kivy.config import Config

Config.set("input", "mouse", "mouse,disable_multitouch")
Config.set("graphics", "width", "720")
Config.set("graphics", "height", "1080")
Config.set("graphics", "minimum_width", "360")
Config.set("graphics", "minimum_height", "640")

from kivy.core.window import Window
from kivy.uix.screenmanager import NoTransition, ScreenManager

from database import TaskDatabase
from font_utils import register_chinese_font
from screens.add_screen import AddScreen
from screens.detail_screen import DetailScreen
from screens.home_screen import HomeScreen
from screens.recycle_bin_screen import RecycleBinScreen


@dataclass
class AppState:
    database: TaskDatabase


class MyNoteApp(App):
    title = "MyNote"

    def build(self):
        Window.clearcolor = (0.96, 0.96, 0.94, 1)
        Window.softinput_mode = "below_target"
        register_chinese_font()
        self.state = AppState(database=TaskDatabase(db_dir=self.user_data_dir))

        manager = ScreenManager(transition=NoTransition())
        manager.add_widget(HomeScreen(name="home", app_state=self.state))
        manager.add_widget(AddScreen(name="add", app_state=self.state))
        manager.add_widget(DetailScreen(name="detail", app_state=self.state))
        manager.add_widget(RecycleBinScreen(name="recycle_bin", app_state=self.state))
        return manager

    def on_pause(self):
        return True

    def on_stop(self):
        self.state.database.close()


if __name__ == "__main__":
    MyNoteApp().run()
