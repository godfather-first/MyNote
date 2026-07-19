from kivy.uix.popup import Popup

from priority import PRIORITY_OPTIONS, PRIORITY_VALUES
from ui_components import PriorityPicker, build_priority_popup_content


def test_priority_values_cover_required_labels():
    assert PRIORITY_VALUES == {"普通": 0, "重要": 1, "急迫": 2}
    assert [item["label"] for item in PRIORITY_OPTIONS] == ["普通", "重要", "急迫"]


def test_priority_popup_option_buttons_trigger_every_priority():
    selected_labels = []
    closed = []

    content = build_priority_popup_content(
        selected_label="普通",
        on_select=lambda label, *_args: selected_labels.append(label),
        on_close=lambda *_args: closed.append(True),
    )

    assert len(content.priority_option_buttons) == 3
    for button in content.priority_option_buttons:
        button.dispatch("on_release")

    assert selected_labels == ["普通", "重要", "急迫"]
    content.children[0].dispatch("on_release")
    assert closed == [True]


def test_priority_picker_popup_opens_for_each_priority(monkeypatch):
    opened_titles = []

    def fake_open(self, *_args, **_kwargs):
        opened_titles.append(self.title)

    monkeypatch.setattr(Popup, "open", fake_open)
    picker = PriorityPicker()

    for label in ("普通", "重要", "急迫"):
        picker.set_priority(label)
        popup = picker.open_popup()
        assert popup.title == "任务优先级"
        assert len(popup.content.priority_option_buttons) == 3

    assert opened_titles == ["任务优先级", "任务优先级", "任务优先级"]
