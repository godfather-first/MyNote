"""MyNote application entry point."""

from dataclasses import dataclass

from kivy.app import App
from kivy.config import Config

# Disable multitouch visual feedback (red circles on right-click).
# Must be set before Window is created to take effect.
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.core.window import Window
from kivy.uix.screenmanager import NoTransition, ScreenManager

from database import TaskDatabase
from font_utils import register_chinese_font
from screens.add_screen import AddScreen
from screens.detail_screen import DetailScreen
from screens.home_screen import HomeScreen


@dataclass
class AppState:
    """Shared app dependencies passed to screens."""

    database: TaskDatabase


class MyNoteApp(App):
    """Kivy Android-ready task note app."""

    title = "MyNote"

    def build(self):
        Window.clearcolor = (0.96, 0.96, 0.94, 1)
        register_chinese_font()
        # Use user_data_dir so the db file is stored in a writable location
        # on both desktop and Android (never inside the APK).
        self.state = AppState(database=TaskDatabase(db_dir=self.user_data_dir))

        manager = ScreenManager(transition=NoTransition())
        manager.add_widget(HomeScreen(name="home", app_state=self.state))
        manager.add_widget(AddScreen(name="add", app_state=self.state))
        manager.add_widget(DetailScreen(name="detail", app_state=self.state))
        return manager

    def on_stop(self):
        self.state.database.close()


if __name__ == "__main__":
    MyNoteApp().run()
