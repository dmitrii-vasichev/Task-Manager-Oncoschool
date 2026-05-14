"""Static glossary for Content Factory UI tooltips.

Single source of truth for term definitions consumed by the frontend
via GET /api/content-factory/glossary. Edit this file + redeploy to
update definitions. Phase 1 keeps this in code (variant A); a future
phase may promote to a DB-backed editable resource.
"""

from typing import TypedDict


class GlossaryTerm(TypedDict):
    term: str
    definition: str
    display_order: int


_TERMS: list[GlossaryTerm] = [
    {
        "term": "Bundle",
        "definition": (
            "Контейнер смысла для одного эфира / темы / обязательства. "
            "Один Bundle объединяет все публикации, которые работают на "
            "одну цель (например, анонсы и follow-up'ы вокруг эфира)."
        ),
        "display_order": 10,
    },
    {
        "term": "Publication",
        "definition": (
            "Один пост на одной площадке (TG / VK / email / Max / ...). "
            "Имеет собственный текст, статус, согласования и метрики. "
            "Несколько публикаций группируются в Bundle."
        ),
        "display_order": 20,
    },
    {
        "term": "Sibling publication",
        "definition": (
            "Публикации одного Bundle на разных площадках. Не клоны — "
            "у каждой свой текст и метрики, но один смысл."
        ),
        "display_order": 30,
    },
    {
        "term": "Funnel template",
        "definition": (
            "Шаблон Bundle с предустановленным набором публикаций "
            "(например, «Воронка эфира»: анонс T-7, button T-3, push T-1h, "
            "live T0, follow-up T+1, digest T+3)."
        ),
        "display_order": 40,
    },
    {
        "term": "Window",
        "definition": (
            "Окно времени, за которое снят метрический снапшот: 3h, 24h, "
            "72h, 7d, final, custom. Позволяет сравнивать публикации в "
            "одинаковых временных рамках."
        ),
        "display_order": 50,
    },
    {
        "term": "Confidence",
        "definition": (
            "Уровень доверия к источнику метрики. high — API/провайдер, "
            "medium — TGStat / парсер, low — ручной ввод."
        ),
        "display_order": 60,
    },
    {
        "term": "Segment role: target",
        "definition": (
            "Сегмент, которому публикация адресована."
        ),
        "display_order": 70,
    },
    {
        "term": "Segment role: exclusion",
        "definition": (
            "Сегмент, который явно исключён из рассылки этой публикации "
            "(например, уже зарегистрированные на эфир)."
        ),
        "display_order": 80,
    },
    {
        "term": "Segment role: control",
        "definition": (
            "Контрольная группа, не получающая публикацию — для замера "
            "эффекта против фона."
        ),
        "display_order": 90,
    },
    {
        "term": "Segment snapshot",
        "definition": (
            "Зафиксированный размер сегмента на момент использования. "
            "Сохраняет данные о том, на сколько человек ушла рассылка, "
            "даже если сегмент потом изменился в GetCourse."
        ),
        "display_order": 100,
    },
    {
        "term": "Retro",
        "definition": (
            "Структурированная ретроспектива (weekly / monthly / по Bundle): "
            "что зашло (best by objective), что сломалось, выводы, решения, "
            "следующие шаги. Привязывается к публикациям/бандлам."
        ),
        "display_order": 110,
    },
    {
        "term": "Approval event",
        "definition": (
            "Шаг согласования публикации: drafted → reviewed → factchecked "
            "→ doctor_approved → scheduled → published. Каждый шаг "
            "создаёт версию для аудита."
        ),
        "display_order": 120,
    },
]


def get_terms() -> list[GlossaryTerm]:
    """Return all glossary terms in display order."""
    return sorted(_TERMS, key=lambda t: t["display_order"])
