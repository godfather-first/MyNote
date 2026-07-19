"""Priority definitions shared by data models, forms, and tests."""

PRIORITY_OPTIONS = (
    {
        "value": 0,
        "label": "普通",
        "description": "日常任务，按计划处理。",
        "color": (0.32, 0.46, 0.62, 1),
    },
    {
        "value": 1,
        "label": "重要",
        "description": "需要优先关注，避免拖延。",
        "color": (0.86, 0.53, 0.12, 1),
    },
    {
        "value": 2,
        "label": "急迫",
        "description": "临近截止或影响关键事项，应尽快完成。",
        "color": (0.76, 0.16, 0.18, 1),
    },
)

PRIORITY_VALUES = {item["label"]: item["value"] for item in PRIORITY_OPTIONS}
PRIORITY_LABELS = {item["value"]: item["label"] for item in PRIORITY_OPTIONS}


def priority_label(value: int) -> str:
    return PRIORITY_LABELS.get(value, "普通")


def priority_option(label: str) -> dict:
    for item in PRIORITY_OPTIONS:
        if item["label"] == label:
            return item
    return PRIORITY_OPTIONS[0]
