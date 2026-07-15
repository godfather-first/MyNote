# -*- coding: utf-8 -*-
"""
桌面任务便签小工具 v2.0  —  PyQt5 + SQLite
============================================
功能：
  1. SQLite 本地持久化（自动创建 task_notes.db）
  2. 三套全局主题：浅色白底 / 护眼浅灰 / 暗黑深色
  3. 双击任务文字编辑，修改同步数据库
  4. 顶部筛选栏：全部 / 待完成 / 已完成
  5. 一键清除已完成 / 一键清空全部
  6. 窗口置顶开关
  7. 快捷键：Enter 新增、Delete 删除选中
  8. 删除二次确认防误触
  9. 窗口尺寸 / 位置记忆自动复原

运行方式：
  pip install PyQt5
  python task_sticky_note.py
"""

import sys
import os
import uuid
import sqlite3
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QCheckBox, QPushButton, QListWidget, QListWidgetItem,
    QSystemTrayIcon, QMenu, QAction, QLabel, QFrame, QSizePolicy,
    QMessageBox, QInputDialog, QComboBox, QButtonGroup,
)
from PyQt5.QtCore import Qt, QSettings, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QColor

# ============================================================================
#  主题配置
# ============================================================================

@dataclass
class ThemeConfig:
    """单个主题的所有颜色值"""
    name: str
    bg: str
    bg_alt: str
    text: str
    text_secondary: str
    text_done: str
    border: str
    border_light: str
    accent: str
    accent_hover: str
    accent_pressed: str
    danger: str
    danger_bg: str
    input_bg: str
    input_focus_bg: str
    card_bg: str
    filter_active_bg: str
    filter_active_text: str
    checkbox_border: str
    checkbox_checked_bg: str
    title_bg: str
    tray_color: str
    list_item_hover: str
    list_item_selected: str
    scrollbar_bg: str
    scrollbar_thumb: str
THEMES = {
    "light": ThemeConfig(
        name="浅色白底",
        bg="#ffffff",
        bg_alt="#f5f5f5",
        text="#333333",
        text_secondary="#888888",
        text_done="#aaaaaa",
        border="#e0e0e0",
        border_light="#f0f0f0",
        accent="#4caf50",
        accent_hover="#43a047",
        accent_pressed="#388e3c",
        danger="#e74c3c",
        danger_bg="#fde8e8",
        input_bg="#f5f5f5",
        input_focus_bg="#ffffff",
        card_bg="#ffffff",
        filter_active_bg="#e8f5e9",
        filter_active_text="#2e7d32",
        checkbox_border="#c0c0c0",
        checkbox_checked_bg="#4caf50",
        title_bg="#ffffff",
        tray_color="#ffe082",
        list_item_hover="#fafafa",
        list_item_selected="#f0faf0",
        scrollbar_bg="#f5f5f5",
        scrollbar_thumb="#cccccc",
    ),
    "gray": ThemeConfig(
        name="护眼浅灰",
        bg="#eeede8",
        bg_alt="#e3e2dc",
        text="#3d3d3d",
        text_secondary="#888888",
        text_done="#9e9e9e",
        border="#d0cfc8",
        border_light="#e2e1da",
        accent="#6b8e5a",
        accent_hover="#5f7f4f",
        accent_pressed="#527045",
        danger="#c0392b",
        danger_bg="#f5e0de",
        input_bg="#f4f3ee",
        input_focus_bg="#faf9f5",
        card_bg="#f7f6f0",
        filter_active_bg="#dcedc8",
        filter_active_text="#33691e",
        checkbox_border="#b0afa8",
        checkbox_checked_bg="#6b8e5a",
        title_bg="#f7f6f0",
        tray_color="#bcaaa4",
        list_item_hover="#f4f3ee",
        list_item_selected="#eef4e8",
        scrollbar_bg="#eeede8",
        scrollbar_thumb="#c0bfb8",
    ),
    "dark": ThemeConfig(
        name="暗黑深色",
        bg="#2b2b2b",
        bg_alt="#363636",
        text="#e0e0e0",
        text_secondary="#888888",
        text_done="#666666",
        border="#444444",
        border_light="#383838",
        accent="#66bb6a",
        accent_hover="#57a95b",
        accent_pressed="#4a9a4e",
        danger="#ef5350",
        danger_bg="#4a3030",
        input_bg="#3c3c3c",
        input_focus_bg="#444444",
        card_bg="#2f2f2f",
        filter_active_bg="#2e4a2e",
        filter_active_text="#81c784",
        checkbox_border="#666666",
        checkbox_checked_bg="#66bb6a",
        title_bg="#2f2f2f",
        tray_color="#5d5d5d",
        list_item_hover="#333333",
        list_item_selected="#2a3f2a",
        scrollbar_bg="#2b2b2b",
        scrollbar_thumb="#555555",
    ),
}

CURRENT_THEME = "light"

# ============================================================================
#  数据库层  —  基于 Python 内置 sqlite3
# ============================================================================
class TaskDB:
    """SQLite 数据库封装，自动创建表与连接"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "task_notes.db")
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_table()

    def _init_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          TEXT PRIMARY KEY,
                text        TEXT NOT NULL,
                completed   INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        self.conn.commit()

    def add_task(self, text: str) -> str:
        tid = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO tasks (id, text) VALUES (?, ?)", (tid, text))
        self.conn.commit()
        return tid

    def delete_task(self, tid: str):
        self.conn.execute("DELETE FROM tasks WHERE id=?", (tid,))
        self.conn.commit()

    def delete_completed(self):
        self.conn.execute("DELETE FROM tasks WHERE completed=1")
        self.conn.commit()

    def delete_all(self):
        self.conn.execute("DELETE FROM tasks")
        self.conn.commit()

    def update_text(self, tid: str, text: str):
        self.conn.execute(
            "UPDATE tasks SET text=? WHERE id=?", (text, tid))
        self.conn.commit()

    def update_completed(self, tid: str, completed: bool):
        self.conn.execute(
            "UPDATE tasks SET completed=? WHERE id=?",
            (1 if completed else 0, tid))
        self.conn.commit()

    def get_all(self) -> list:
        cur = self.conn.execute(
            "SELECT id, text, completed, created_at "
            "FROM tasks ORDER BY created_at")
        return cur.fetchall()

    def close(self):
        self.conn.close()

# ============================================================================
#  ClickableLabel  —  双击发出编辑信号
# ============================================================================
class ClickableLabel(QLabel):
    """双击时发出 double_clicked 信号"""
    double_clicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


# ============================================================================
#  TaskWidget  —  单条任务控件
# ============================================================================
class TaskWidget(QWidget):
    """水平布局：复选框 | 可双击编辑的任务文字 | 删除按钮"""

    toggle_requested = pyqtSignal()
    edit_requested = pyqtSignal()

    def __init__(self, task_id: str, text: str,
                 completed: bool = False, parent=None):
        super().__init__(parent)
        self._task_id = task_id
        self._completed = completed
        self.setObjectName("TaskWidget")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 10, 8)
        layout.setSpacing(8)

        # ① 方形复选框
        self.checkbox = QCheckBox()
        self.checkbox.setObjectName("taskCheckbox")
        self.checkbox.setFixedSize(24, 24)
        self.checkbox.setChecked(completed)

        # ② 可双击编辑的文字标签
        self.label = ClickableLabel(text)
        self.label.setObjectName("taskLabel")
        self.label.setWordWrap(True)
        self.label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred)

        # ③ 删除按钮
        self.delete_btn = QPushButton("\u2715")
        self.delete_btn.setObjectName("taskDeleteBtn")
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setToolTip("删除此任务")

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label, stretch=1)
        layout.addWidget(self.delete_btn)

        self.checkbox.stateChanged.connect(self._on_toggle)
        self.label.double_clicked.connect(self.edit_requested.emit)

    def _on_toggle(self, state: int):
        self._completed = (state == Qt.Checked)
        self._update_style()
        self.toggle_requested.emit()

    def _update_style(self):
        if self._completed:
            self.label.setProperty("state", "done")
        else:
            self.label.setProperty("state", "normal")
        self.label.style().unpolish(self.label)
        self.label.style().polish(self.label)

    @property
    def task_id(self) -> str:
        return self._task_id

    @property
    def is_completed(self) -> bool:
        return self._completed

    @property
    def task_text(self) -> str:
        return self.label.text()

    def set_task_text(self, text: str):
        self.label.setText(text)

    def set_task_completed(self, completed: bool):
        self._completed = completed
        self.checkbox.setChecked(completed)
        self._update_style()

# ============================================================================
#  主窗口
# ============================================================================
class TaskStickyNote(QMainWindow):
    """便签主窗口 + 系统托盘 + 全部业务逻辑"""

    TITLE = "\U0001f4cb 任务便签"

    def __init__(self):
        super().__init__()
        self.db = TaskDB()
        self._current_filter = "all"
        self._all_records = []
        self._init_ui()
        self._init_tray()
        self._restore_geometry()
        self._load_from_db()
        self.apply_theme("light")
    # ========================  UI 搭建  ========================

    def _init_ui(self):
        self.setWindowTitle(self.TITLE)
        self.setMinimumSize(360, 440)
        self.resize(440, 600)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_title_bar())
        root.addWidget(self._build_filter_bar())
        root.addWidget(self._build_action_bar())

        self.task_list = QListWidget()
        self.task_list.setObjectName("taskList")
        self.task_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.task_list.setVerticalScrollMode(
            QListWidget.ScrollPerPixel)
        self.task_list.setSpacing(0)
        root.addWidget(self.task_list, stretch=1)
        self.task_list.installEventFilter(self)

        sep = QFrame()
        sep.setObjectName("bottomSep")
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        root.addWidget(sep)
        root.addWidget(self._build_input_bar())

    def _build_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("titleBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 12, 14, 10)

        self.title_label = QLabel("\U0001f4cb 任务列表")
        self.title_label.setObjectName("titleText")

        self.pin_check = QCheckBox("置顶")
        self.pin_check.setObjectName("pinCheck")
        self.pin_check.stateChanged.connect(self._toggle_pin)

        layout.addWidget(self.title_label, stretch=1)
        layout.addWidget(self.pin_check)
        return bar
    def _build_filter_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("filterBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(6)

        self.filter_btns = {}
        group = QButtonGroup(self)
        group.setExclusive(True)

        for key, lbl in [("all", "全部"), ("active", "待完成"),
                         ("completed", "已完成")]:
            btn = QPushButton(lbl)
            btn.setObjectName("filterBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked, k=key: self._set_filter(k))
            self.filter_btns[key] = btn
            group.addButton(btn)
            layout.addWidget(btn)

        self.filter_btns["all"].setChecked(True)
        layout.addStretch(1)
        return bar

    def _build_action_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("actionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 4, 14, 6)
        layout.setSpacing(8)

        lbl_theme = QLabel("主题:")
        lbl_theme.setObjectName("actionLabel")
        layout.addWidget(lbl_theme)

        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themeCombo")
        for key in ("light", "gray", "dark"):
            self.theme_combo.addItem(THEMES[key].name, key)
        self.theme_combo.currentIndexChanged.connect(
            self._on_theme_changed)
        layout.addWidget(self.theme_combo)

        layout.addStretch(1)

        self.clear_done_btn = QPushButton("清除已完成")
        self.clear_done_btn.setObjectName("actionBtn")
        self.clear_done_btn.setCursor(Qt.PointingHandCursor)
        self.clear_done_btn.clicked.connect(self._clear_completed)
        layout.addWidget(self.clear_done_btn)

        self.clear_all_btn = QPushButton("清空全部")
        self.clear_all_btn.setObjectName("actionBtn")
        self.clear_all_btn.setCursor(Qt.PointingHandCursor)
        self.clear_all_btn.clicked.connect(self._clear_all)
        layout.addWidget(self.clear_all_btn)

        return bar
    def _build_input_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("inputBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 10, 12, 14)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("taskInput")
        self.input_field.setPlaceholderText(
            "输入新任务，按回车添加\u2026")
        self.input_field.returnPressed.connect(self._add_task)

        add_btn = QPushButton("\uff0b")
        add_btn.setObjectName("addBtn")
        add_btn.setFixedSize(42, 42)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setToolTip("添加任务")
        add_btn.clicked.connect(self._add_task)

        layout.addWidget(self.input_field, stretch=1)
        layout.addWidget(add_btn)
        return bar

    def _set_window_icon(self, color: str = "#ffe082"):
        pm = QPixmap(64, 64)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(color))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(8, 4, 48, 48, 6, 6)
        p.setPen(QColor("#bdbdbd"))
        for y in (18, 28, 38):
            p.drawLine(20, y,
                       20 + (24 if y == 18 else 20 if y == 28 else 16),
                       y)
        p.end()
        self.setWindowIcon(QIcon(pm))
    # ========================  主题系统  ========================

    def apply_theme(self, theme_key: str):
        global CURRENT_THEME
        CURRENT_THEME = theme_key
        t = THEMES[theme_key]

        self._set_window_icon(t.tray_color)
        if hasattr(self, "tray"):
            self.tray.setIcon(self.windowIcon())

        style = f"""
        QMainWindow, QWidget {{
            background-color: {t.bg};
            color: {t.text};
        }}
        #titleBar {{
            background: {t.title_bg};
            border-bottom: 1px solid {t.border_light};
        }}
        #titleText {{
            font-size: 16px; font-weight: bold; color: {t.text};
            padding: 0;
        }}
        #pinCheck {{
            spacing: 4px; font-size: 12px; color: {t.text_secondary};
        }}
        #pinCheck::indicator {{
            width: 16px; height: 16px;
            border: 2px solid {t.checkbox_border};
            border-radius: 3px; background: {t.bg};
        }}
        #pinCheck::indicator:checked {{
            background: {t.accent}; border-color: {t.accent};
        }}
        #filterBar {{
            background: {t.bg};
            border-bottom: 1px solid {t.border_light};
        }}
        #filterBtn {{
            background: transparent;
            border: 1px solid {t.border};
            border-radius: 14px;
            padding: 4px 16px; font-size: 12px;
            color: {t.text_secondary};
        }}
        #filterBtn:hover {{
            background: {t.bg_alt}; color: {t.text};
        }}
        #filterBtn:checked {{
            background: {t.filter_active_bg};
            color: {t.filter_active_text};
            border-color: {t.filter_active_text};
        }}
        #actionBar {{
            background: {t.bg};
            border-bottom: 1px solid {t.border_light};
        }}
        #actionLabel {{
            font-size: 12px; color: {t.text_secondary};
        }}
        #themeCombo {{
            background: {t.input_bg};
            border: 1px solid {t.border};
            border-radius: 14px;
            padding: 3px 10px; font-size: 12px;
            color: {t.text}; min-width: 80px;
        }}
        #themeCombo:hover {{
            border-color: {t.accent};
        }}
        #themeCombo QAbstractItemView {{
            background: {t.card_bg};
            border: 1px solid {t.border};
            selection-background: {t.filter_active_bg};
            selection-color: {t.filter_active_text};
            color: {t.text};
        }}
        #actionBtn {{
            background: transparent;
            border: 1px solid {t.border};
            border-radius: 14px;
            padding: 4px 12px; font-size: 12px;
            color: {t.text_secondary};
        }}
        #actionBtn:hover {{
            border-color: {t.danger}; color: {t.danger};
            background: {t.danger_bg};
        }}
        #taskList {{
            border: none; background: {t.bg}; outline: none;
        }}
        #taskList::item:hover {{
            background: {t.list_item_hover};
        }}
        #taskList::item:selected {{
            background: {t.list_item_selected};
            color: {t.text};
        }}
        #taskList QScrollBar:vertical {{
            width: 6px; background: {t.scrollbar_bg};
        }}
        #taskList QScrollBar::handle:vertical {{
            background: {t.scrollbar_thumb};
            border-radius: 3px; min-height: 30px;
        }}
        #taskList QScrollBar::add-line:vertical,
        #taskList QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        #taskList QScrollBar::add-page:vertical,
        #taskList QScrollBar::sub-page:vertical {{
            background: none;
        }}
        #TaskWidget {{
            border-bottom: 1px solid {t.border_light};
            background: {t.bg};
        }}
        #taskCheckbox::indicator {{
            width: 20px; height: 20px;
            border: 2px solid {t.checkbox_border};
            border-radius: 4px; background: {t.bg};
        }}
        #taskCheckbox::indicator:checked {{
            background: {t.checkbox_checked_bg};
            border-color: {t.checkbox_checked_bg};
        }}
        #taskCheckbox::indicator:hover {{
            border-color: {t.accent};
        }}
        #taskLabel[state="normal"] {{
            font-size: 14px; color: {t.text};
            padding: 3px 0; background: transparent;
        }}
        #taskLabel[state="done"] {{
            font-size: 14px; color: {t.text_done};
            padding: 3px 0; background: transparent;
            text-decoration: line-through;
        }}
        #taskDeleteBtn {{
            background: transparent; border: none;
            color: {t.text_secondary};
            font-size: 16px; font-weight: bold;
            padding: 4px 8px; border-radius: 4px;
        }}
        #taskDeleteBtn:hover {{
            color: {t.danger}; background: {t.danger_bg};
        }}
        #bottomSep {{ color: {t.border_light}; }}
        #inputBar {{ background: {t.bg}; }}
        #taskInput {{
            border: 1px solid {t.border};
            border-radius: 10px;
            padding: 10px 14px; font-size: 14px;
            background: {t.input_bg}; color: {t.text};
        }}
        #taskInput:focus {{
            border-color: {t.accent};
            background: {t.input_focus_bg};
        }}
        #addBtn {{
            background: {t.accent}; color: #ffffff;
            border: none; border-radius: 10px;
            font-size: 20px; font-weight: bold;
        }}
        #addBtn:hover {{ background: {t.accent_hover}; }}
        #addBtn:pressed {{ background: {t.accent_pressed}; }}
        """
        QApplication.instance().setStyleSheet(style)

    def _on_theme_changed(self, idx: int):
        self.apply_theme(self.theme_combo.itemData(idx))
    # ========================  系统托盘  ========================

    def _init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._set_window_icon(THEMES[CURRENT_THEME].tray_color)
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.windowIcon())
        self.tray.setToolTip("任务便签")

        menu = QMenu()
        act_show = QAction("显示窗口", self)
        act_show.triggered.connect(self._show_window)
        menu.addAction(act_show)
        act_hide = QAction("隐藏窗口", self)
        act_hide.triggered.connect(self.hide)
        menu.addAction(act_hide)
        menu.addSeparator()
        act_quit = QAction("退出", self)
        act_quit.triggered.connect(self._quit_app)
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason: int):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_window()

    def _show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if hasattr(self, "tray") and self.tray.isVisible():
            self.hide()
            self.tray.showMessage(
                "任务便签",
                "已最小化到系统托盘，右键可退出",
                QSystemTrayIcon.Information, 2000)
            event.ignore()
        else:
            event.accept()

    def _quit_app(self):
        self._save_geometry()
        if hasattr(self, "tray"):
            self.tray.hide()
        self.db.close()
        QApplication.quit()
    # ========================  窗口记忆  ========================

    def _save_geometry(self):
        s = QSettings("TaskStickyNote", "TaskStickyNote")
        s.setValue("window_geometry", self.saveGeometry())
        s.setValue("window_state", self.saveState())
        s.setValue("theme", CURRENT_THEME)

    def _restore_geometry(self):
        s = QSettings("TaskStickyNote", "TaskStickyNote")
        geom = s.value("window_geometry")
        if geom is not None:
            self.restoreGeometry(geom)
        state = s.value("window_state")
        if state is not None:
            self.restoreState(state)
        saved = s.value("theme", "light")
        idx = self.theme_combo.findData(saved)
        if idx >= 0:
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentIndex(idx)
            self.theme_combo.blockSignals(False)
            self.apply_theme(saved)

    # ========================  数据库加载  ========================

    def _load_from_db(self):
        for row in self.db.get_all():
            self._add_task_widget(
                row["id"], row["text"], bool(row["completed"]))
    # ========================  核心业务  ========================

    def _add_task(self):
        text = self.input_field.text().strip()
        if not text:
            return
        tid = self.db.add_task(text)
        self._add_task_widget(tid, text, False)
        self.input_field.clear()
        self.input_field.setFocus()
        self._apply_filter()

    def _add_task_widget(self, tid: str, text: str, completed: bool):
        tw = TaskWidget(tid, text, completed)
        tw.delete_btn.clicked.connect(
            lambda checked, w=tw: self._remove_task(w))
        tw.edit_requested.connect(
            lambda w=tw: self._edit_task(w))
        tw.toggle_requested.connect(
            lambda w=tw: self._on_task_toggle(w))

        item = QListWidgetItem(self.task_list)
        item.setSizeHint(tw.sizeHint())
        item.setFlags(item.flags() | Qt.ItemIsSelectable)
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, tw)
        self._all_records.append((tw, item))

    def _remove_task(self, tw: TaskWidget):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除「{tw.task_text}」吗？\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.db.delete_task(tw.task_id)
        for i, (w, item) in enumerate(self._all_records):
            if w is tw:
                self._all_records.pop(i)
                self.task_list.takeItem(
                    self.task_list.row(item))
                break
        self._apply_filter()

    def _edit_task(self, tw: TaskWidget):
        text, ok = QInputDialog.getText(
            self, "编辑任务", "修改任务内容：",
            QLineEdit.Normal, tw.task_text)
        if ok and text.strip():
            text = text.strip()
            self.db.update_text(tw.task_id, text)
            tw.set_task_text(text)

    def _on_task_toggle(self, tw: TaskWidget):
        self.db.update_completed(tw.task_id, tw.is_completed)
        self._apply_filter()
    # ---- 筛选 ----
    def _set_filter(self, key: str):
        self._current_filter = key
        self._apply_filter()

    def _apply_filter(self):
        for tw, item in self._all_records:
            if self._current_filter == "all":
                item.setHidden(False)
            elif self._current_filter == "active":
                item.setHidden(tw.is_completed)
            else:
                item.setHidden(not tw.is_completed)
        total = len(self._all_records)
        done = sum(1 for tw, _ in self._all_records if tw.is_completed)
        self.title_label.setText(
            f"\U0001f4cb 任务列表  ({total} 项, {done} 已完成)")

    # ---- 清空 ----
    def _clear_completed(self):
        if not any(tw.is_completed for tw, _ in self._all_records):
            QMessageBox.information(self, "提示", "没有已完成的任务。")
            return
        reply = QMessageBox.question(
            self, "确认清除",
            "确定要清除所有已完成的任务吗？\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.db.delete_completed()
        for tw, item in list(self._all_records):
            if tw.is_completed:
                self.task_list.takeItem(
                    self.task_list.row(item))
                self._all_records.remove((tw, item))
        self._apply_filter()

    def _clear_all(self):
        if not self._all_records:
            QMessageBox.information(self, "提示", "任务列表已是空的。")
            return
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空全部任务吗？\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.db.delete_all()
        self.task_list.clear()
        self._all_records.clear()
        self._apply_filter()
    # ---- 置顶 ----
    def _toggle_pin(self, state: int):
        if state == Qt.Checked:
            self.setWindowFlags(
                self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    # ---- Delete 快捷键 ----
    def eventFilter(self, obj, event):
        if (obj is self.task_list
                and event.type() == QEvent.KeyPress
                and event.key() == Qt.Key_Delete):
            current = self.task_list.currentItem()
            if current:
                w = self.task_list.itemWidget(current)
                if w and hasattr(w, "task_id"):
                    self._remove_task(w)
                    return True
        return super().eventFilter(obj, event)

    # ---- 窗口缩放适配 ----
    def resizeEvent(self, event):
        super().resizeEvent(event)
        for tw, item in self._all_records:
            item.setSizeHint(tw.sizeHint())
        self._save_geometry()


# ============================================================================
#  程序入口
# ============================================================================
def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("TaskStickyNote")
    app.setOrganizationName("TaskStickyNote")
    app.setQuitOnLastWindowClosed(False)

    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = TaskStickyNote()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
