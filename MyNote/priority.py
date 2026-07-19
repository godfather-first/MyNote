"""Priority definitions used by data, UI, and tests."""

PRIORITY_OPTIONS = (
    {
        "value": 0,
        "label": "普通",
        "description": "日常任务，按计划处理。",
        "color": (0.28, 0.43, 0.63, 1),
    },
    {
        "value": 1,
        "label": "重要",
        "description": "需要优先关注，避免拖延。",
        "color": (0.84, 0.50, 0.12, 1),
    },
    {
        "value": 2,
        "label": "急迫",
        "description": "临近截止或影响关键事项，应尽快完成。",
        "color": (0.74, 0.15, 0.16, 1),
    },
)

PRIORITY_VALUES = {item["label"]: item["value"] for item in PRIORITY_OPTIONS}
PRIORITY_LABELS = {item["value"]: item["label"] for item in PRIORITY_OPTIONS}


def clamp_priority(value: int | str | None) -> int:
    """Return one of the supported priority values."""

    if isinstance(value, str):
        if value in PRIORITY_VALUES:
            return PRIORITY_VALUES[value]
        try:
            value = int(value)
        except ValueError:
            return 0
    try:
        value = int(value if value is not None else 0)
    except (TypeError, ValueError):
        return 0
    return value if value in PRIORITY_LABELS else 0


def priority_label(value: int | str | None) -> str:
    return PRIORITY_LABELS[clamp_priority(value)]


def priority_option(value: int | str | None) -> dict:
    priority_value = clamp_priority(value)
    for item in PRIORITY_OPTIONS:
        if item["value"] == priority_value:
            return item
    return PRIORITY_OPTIONS[0]
