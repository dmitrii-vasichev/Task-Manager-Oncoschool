from __future__ import annotations

NORMAL_URGENCY = "normal"
URGENT_URGENCY = "urgent"
TASK_URGENCY_VALUES = (NORMAL_URGENCY, URGENT_URGENCY)

URGENT_ALIASES = {
    "urgent",
    "high",
    "срочно",
    "срочный",
    "срочная",
    "важно",
    "важный",
    "важная",
    "критично",
    "высокий",
    "высокая",
}

NORMAL_ALIASES = {
    "normal",
    "medium",
    "low",
    "обычная",
    "обычный",
    "обычно",
    "не срочно",
    "несрочно",
    "средний",
    "средняя",
    "низкий",
    "низкая",
}

TASK_URGENCY_LABELS = {
    NORMAL_URGENCY: "Обычная",
    URGENT_URGENCY: "Срочная",
}


def normalize_task_urgency(value: str | None, default: str = NORMAL_URGENCY) -> str:
    normalized_default = URGENT_URGENCY if default == URGENT_URGENCY else NORMAL_URGENCY
    if value is None:
        return normalized_default

    normalized = " ".join(str(value).strip().lower().split())
    if not normalized:
        return normalized_default
    if normalized in URGENT_ALIASES:
        return URGENT_URGENCY
    if normalized in NORMAL_ALIASES:
        return NORMAL_URGENCY
    return normalized_default


def is_task_urgent(value: str | None) -> bool:
    return normalize_task_urgency(value) == URGENT_URGENCY


def task_urgency_rank(value: str | None) -> int:
    return 1 if is_task_urgent(value) else 0
