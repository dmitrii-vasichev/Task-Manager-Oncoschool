"""
Seed script for demo data.

Usage:
    # Seed demo data
    python -m scripts.seed_demo

    # Clean up demo data
    python -m scripts.seed_demo --clean

Login credentials (dev mode, DEBUG=true):
    Admin:     telegram_id = 100001
    Moderator: telegram_id = 100002
    Member:    telegram_id = 100003
"""

import argparse
import asyncio
import random
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session, engine
from app.db.models import (
    AppSettings,
    DailyMetric,
    Department,
    GetCourseCredentials,
    Meeting,
    MeetingParticipant,
    MeetingSchedule,
    ReminderSettings,
    Task,
    TaskUpdate,
    TeamMember,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Marker: all demo UUIDs share this prefix for easy cleanup
DEMO_NS = uuid.UUID("00000000-de00-de00-de00-000000000000")

def _demo_id(n: int) -> uuid.UUID:
    """Generate a deterministic demo UUID."""
    return uuid.uuid5(DEMO_NS, str(n))


NOW = datetime.now()
TODAY = date.today()

# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

DEPARTMENTS = [
    {
        "id": _demo_id(1000),
        "name": "Онкология",
        "description": "Образовательные программы по клинической онкологии",
        "color": "#0D9488",
        "sort_order": 1,
    },
    {
        "id": _demo_id(1001),
        "name": "Маркетинг",
        "description": "Продвижение и коммуникации",
        "color": "#F97316",
        "sort_order": 2,
    },
    {
        "id": _demo_id(1002),
        "name": "Методология",
        "description": "Разработка учебных программ и контента",
        "color": "#8B5CF6",
        "sort_order": 3,
    },
    {
        "id": _demo_id(1003),
        "name": "Техническая поддержка",
        "description": "Поддержка платформы и инфраструктура",
        "color": "#3B82F6",
        "sort_order": 4,
    },
    {
        "id": _demo_id(1004),
        "name": "Администрация",
        "description": "Управление и координация",
        "color": "#EF4444",
        "sort_order": 5,
    },
]

# ---------------------------------------------------------------------------
# Team Members
# ---------------------------------------------------------------------------

MEMBERS = [
    # Admin
    {
        "id": _demo_id(2000),
        "telegram_id": 100001,
        "telegram_username": "demo_admin",
        "full_name": "Елена Соколова",
        "name_variants": ["Елена", "Лена", "Соколова"],
        "position": "Директор",
        "email": "sokolova@oncoschool.ru",
        "birthday": date(1985, 3, 15),
        "avatar_url": "https://i.pravatar.cc/150?img=49",
        "role": "admin",
        "department_id": _demo_id(1004),  # Администрация
    },
    # Moderators
    {
        "id": _demo_id(2001),
        "telegram_id": 100002,
        "telegram_username": "demo_moderator",
        "full_name": "Алексей Морозов",
        "name_variants": ["Алексей", "Лёша", "Морозов"],
        "position": "Руководитель проектов",
        "email": "morozov@oncoschool.ru",
        "birthday": date(1990, 7, 22),
        "avatar_url": "https://i.pravatar.cc/150?img=12",
        "role": "moderator",
        "department_id": _demo_id(1000),  # Онкология
    },
    {
        "id": _demo_id(2002),
        "telegram_id": 100010,
        "telegram_username": "demo_mod2",
        "full_name": "Ирина Кузнецова",
        "name_variants": ["Ирина", "Ира", "Кузнецова"],
        "position": "Координатор программ",
        "email": "kuznetsova@oncoschool.ru",
        "birthday": date(1988, 11, 3),
        "avatar_url": "https://i.pravatar.cc/150?img=45",
        "role": "moderator",
        "department_id": _demo_id(1002),  # Методология
    },
    # Members
    {
        "id": _demo_id(2003),
        "telegram_id": 100003,
        "telegram_username": "demo_member",
        "full_name": "Дмитрий Волков",
        "name_variants": ["Дмитрий", "Дима", "Волков"],
        "position": "Методист",
        "email": "volkov@oncoschool.ru",
        "birthday": date(1993, 5, 10),
        "avatar_url": "https://i.pravatar.cc/150?img=11",
        "role": "member",
        "department_id": _demo_id(1002),  # Методология
    },
    {
        "id": _demo_id(2004),
        "telegram_id": 100004,
        "telegram_username": "demo_m2",
        "full_name": "Анна Петрова",
        "name_variants": ["Анна", "Аня", "Петрова"],
        "position": "Маркетолог",
        "email": "petrova@oncoschool.ru",
        "birthday": date(1995, 1, 28),
        "avatar_url": "https://i.pravatar.cc/150?img=5",
        "role": "member",
        "department_id": _demo_id(1001),  # Маркетинг
    },
    {
        "id": _demo_id(2005),
        "telegram_id": 100005,
        "telegram_username": "demo_m3",
        "full_name": "Сергей Николаев",
        "name_variants": ["Сергей", "Серёжа", "Николаев"],
        "position": "Врач-онколог, лектор",
        "email": "nikolaev@oncoschool.ru",
        "birthday": date(1982, 9, 14),
        "avatar_url": "https://i.pravatar.cc/150?img=8",
        "role": "member",
        "department_id": _demo_id(1000),  # Онкология
    },
    {
        "id": _demo_id(2006),
        "telegram_id": 100006,
        "telegram_username": "demo_m4",
        "full_name": "Мария Козлова",
        "name_variants": ["Мария", "Маша", "Козлова"],
        "position": "SMM-менеджер",
        "email": "kozlova@oncoschool.ru",
        "birthday": date(1997, 4, 7),
        "avatar_url": "https://i.pravatar.cc/150?img=25",
        "role": "member",
        "department_id": _demo_id(1001),  # Маркетинг
    },
    {
        "id": _demo_id(2007),
        "telegram_id": 100007,
        "telegram_username": "demo_m5",
        "full_name": "Андрей Смирнов",
        "name_variants": ["Андрей", "Смирнов"],
        "position": "Разработчик",
        "email": "smirnov@oncoschool.ru",
        "birthday": date(1991, 12, 1),
        "avatar_url": "https://i.pravatar.cc/150?img=57",
        "role": "member",
        "department_id": _demo_id(1003),  # Тех. поддержка
    },
    {
        "id": _demo_id(2008),
        "telegram_id": 100008,
        "telegram_username": "demo_m6",
        "full_name": "Ольга Федорова",
        "name_variants": ["Ольга", "Оля", "Федорова"],
        "position": "Методист-куратор",
        "email": "fedorova@oncoschool.ru",
        "birthday": date(1994, 8, 19),
        "avatar_url": "https://i.pravatar.cc/150?img=44",
        "role": "member",
        "department_id": _demo_id(1002),  # Методология
    },
    {
        "id": _demo_id(2009),
        "telegram_id": 100009,
        "telegram_username": "demo_m7",
        "full_name": "Виктор Лебедев",
        "name_variants": ["Виктор", "Витя", "Лебедев"],
        "position": "Врач-радиолог, лектор",
        "email": "lebedev@oncoschool.ru",
        "birthday": date(1980, 6, 25),
        "avatar_url": "https://i.pravatar.cc/150?img=60",
        "role": "member",
        "department_id": _demo_id(1000),  # Онкология
    },
    {
        "id": _demo_id(2010),
        "telegram_id": 100011,
        "telegram_username": "demo_m8",
        "full_name": "Наталья Белова",
        "name_variants": ["Наталья", "Наташа", "Белова"],
        "position": "Бухгалтер",
        "email": "belova@oncoschool.ru",
        "birthday": date(1987, 2, 11),
        "avatar_url": "https://i.pravatar.cc/150?img=32",
        "role": "member",
        "department_id": _demo_id(1004),  # Администрация
    },
    {
        "id": _demo_id(2011),
        "telegram_id": 100012,
        "telegram_username": "demo_m9",
        "full_name": "Павел Егоров",
        "name_variants": ["Павел", "Паша", "Егоров"],
        "position": "Видеограф",
        "email": "egorov@oncoschool.ru",
        "birthday": date(1996, 10, 30),
        "avatar_url": "https://i.pravatar.cc/150?img=53",
        "role": "member",
        "department_id": _demo_id(1001),  # Маркетинг
    },
]

# Department heads (set after members are created)
DEPARTMENT_HEADS = {
    _demo_id(1000): _demo_id(2001),  # Онкология → Алексей Морозов
    _demo_id(1001): _demo_id(2004),  # Маркетинг → Анна Петрова
    _demo_id(1002): _demo_id(2002),  # Методология → Ирина Кузнецова
    _demo_id(1003): _demo_id(2007),  # Тех. поддержка → Андрей Смирнов
    _demo_id(1004): _demo_id(2000),  # Администрация → Елена Соколова
}

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def _tasks() -> list[dict]:
    """Generate tasks with dates relative to today."""
    return [
        # === NEW ===
        {
            "id": _demo_id(3000),
            "title": "Подготовить материалы для вебинара по иммунотерапии",
            "description": "Собрать актуальные клинические случаи и статистику для лекции 28 марта. Формат: презентация + раздаточные материалы.",
            "status": "new",
            "priority": "high",
            "assignee_id": _demo_id(2005),  # Николаев
            "created_by_id": _demo_id(2001),  # Морозов
            "source": "web",
            "deadline": TODAY + timedelta(days=5),
            "created_at": NOW - timedelta(days=1),
        },
        {
            "id": _demo_id(3001),
            "title": "Настроить рассылку для новых студентов потока",
            "description": "Создать welcome-серию из 3 писем для студентов нового потока.",
            "status": "new",
            "priority": "medium",
            "assignee_id": _demo_id(2006),  # Козлова
            "created_by_id": _demo_id(2004),  # Петрова
            "source": "text",
            "deadline": TODAY + timedelta(days=7),
            "created_at": NOW - timedelta(hours=12),
        },
        {
            "id": _demo_id(3002),
            "title": "Обновить раздел FAQ на сайте",
            "description": "Добавить вопросы про новую программу и обновить ответы по оплате.",
            "status": "new",
            "priority": "low",
            "assignee_id": _demo_id(2007),  # Смирнов
            "created_by_id": _demo_id(2002),  # Кузнецова
            "source": "summary",
            "deadline": TODAY + timedelta(days=14),
            "created_at": NOW - timedelta(hours=6),
        },
        {
            "id": _demo_id(3003),
            "title": "Провести аудит учебных видеозаписей",
            "description": "Проверить качество записей последних 10 вебинаров, отметить проблемные.",
            "status": "new",
            "priority": "medium",
            "assignee_id": _demo_id(2011),  # Егоров
            "created_by_id": _demo_id(2001),  # Морозов
            "source": "voice",
            "created_at": NOW - timedelta(hours=3),
        },
        # === IN PROGRESS ===
        {
            "id": _demo_id(3004),
            "title": "Разработать программу курса по таргетной терапии",
            "description": "Программа на 8 недель: модули, темы лекций, практические задания, список лекторов.",
            "status": "in_progress",
            "priority": "urgent",
            "assignee_id": _demo_id(2003),  # Волков
            "created_by_id": _demo_id(2002),  # Кузнецова
            "source": "web",
            "deadline": TODAY + timedelta(days=10),
            "created_at": NOW - timedelta(days=7),
        },
        {
            "id": _demo_id(3005),
            "title": "Смонтировать промо-ролик для нового курса",
            "description": "30-секундный ролик для Instagram и Telegram. Исходники в Google Drive.",
            "status": "in_progress",
            "priority": "high",
            "assignee_id": _demo_id(2011),  # Егоров
            "created_by_id": _demo_id(2004),  # Петрова
            "source": "text",
            "deadline": TODAY + timedelta(days=3),
            "created_at": NOW - timedelta(days=4),
        },
        {
            "id": _demo_id(3006),
            "title": "Исправить баг с отображением расписания",
            "description": "На мобильных устройствах расписание смещается вправо. Воспроизводится на iPhone 14.",
            "status": "in_progress",
            "priority": "high",
            "assignee_id": _demo_id(2007),  # Смирнов
            "created_by_id": _demo_id(2007),  # сам
            "source": "text",
            "deadline": TODAY + timedelta(days=1),
            "created_at": NOW - timedelta(days=2),
        },
        {
            "id": _demo_id(3007),
            "title": "Подготовить отчёт по результатам потока Q1",
            "description": "Статистика: количество студентов, завершаемость, средний балл, NPS.",
            "status": "in_progress",
            "priority": "medium",
            "assignee_id": _demo_id(2008),  # Федорова
            "created_by_id": _demo_id(2002),  # Кузнецова
            "source": "summary",
            "deadline": TODAY + timedelta(days=5),
            "created_at": NOW - timedelta(days=5),
        },
        {
            "id": _demo_id(3008),
            "title": "Запустить таргетированную рекламу в VK",
            "description": "Бюджет: 50 000 ₽. ЦА: онкологи 30-50 лет. Креативы готовы.",
            "status": "in_progress",
            "priority": "medium",
            "assignee_id": _demo_id(2004),  # Петрова
            "created_by_id": _demo_id(2000),  # Соколова
            "source": "voice",
            "deadline": TODAY + timedelta(days=2),
            "created_at": NOW - timedelta(days=3),
        },
        # === REVIEW ===
        {
            "id": _demo_id(3009),
            "title": "Написать статью для блога: 5 трендов в онкообразовании",
            "description": "SEO-оптимизированная статья, 1500-2000 слов. Ключевые слова согласованы.",
            "status": "review",
            "priority": "medium",
            "assignee_id": _demo_id(2006),  # Козлова
            "created_by_id": _demo_id(2004),  # Петрова
            "source": "text",
            "deadline": TODAY + timedelta(days=2),
            "created_at": NOW - timedelta(days=6),
        },
        {
            "id": _demo_id(3010),
            "title": "Обновить слайды лекции по химиотерапии",
            "description": "Добавить новые протоколы 2024 года, обновить статистику выживаемости.",
            "status": "review",
            "priority": "high",
            "assignee_id": _demo_id(2009),  # Лебедев
            "created_by_id": _demo_id(2001),  # Морозов
            "source": "summary",
            "deadline": TODAY - timedelta(days=1),  # overdue!
            "created_at": NOW - timedelta(days=8),
        },
        {
            "id": _demo_id(3011),
            "title": "Согласовать договор с новым лектором",
            "description": "Проф. Иванова, кафедра онкологии МГМУ. Условия обсудили на встрече.",
            "status": "review",
            "priority": "urgent",
            "assignee_id": _demo_id(2010),  # Белова
            "created_by_id": _demo_id(2000),  # Соколова
            "source": "voice",
            "deadline": TODAY,
            "created_at": NOW - timedelta(days=3),
        },
        # === DONE ===
        {
            "id": _demo_id(3012),
            "title": "Провести вебинар «Скрининг колоректального рака»",
            "description": "Лектор: Николаев С.А. Участников: 145. Запись загружена.",
            "status": "done",
            "priority": "high",
            "assignee_id": _demo_id(2005),  # Николаев
            "created_by_id": _demo_id(2001),  # Морозов
            "source": "text",
            "deadline": TODAY - timedelta(days=3),
            "completed_at": NOW - timedelta(days=3),
            "created_at": NOW - timedelta(days=14),
        },
        {
            "id": _demo_id(3013),
            "title": "Настроить интеграцию с GetCourse",
            "description": "API-ключ получен, синхронизация метрик настроена. Тестовый прогон OK.",
            "status": "done",
            "priority": "high",
            "assignee_id": _demo_id(2007),  # Смирнов
            "created_by_id": _demo_id(2000),  # Соколова
            "source": "web",
            "deadline": TODAY - timedelta(days=5),
            "completed_at": NOW - timedelta(days=6),
            "created_at": NOW - timedelta(days=15),
        },
        {
            "id": _demo_id(3014),
            "title": "Создать шаблоны email-рассылок",
            "description": "3 шаблона: welcome, напоминание о занятии, сертификат.",
            "status": "done",
            "priority": "medium",
            "assignee_id": _demo_id(2006),  # Козлова
            "created_by_id": _demo_id(2004),  # Петрова
            "source": "text",
            "completed_at": NOW - timedelta(days=2),
            "created_at": NOW - timedelta(days=10),
        },
        {
            "id": _demo_id(3015),
            "title": "Обновить программу курса по диагностике",
            "description": "Добавлены модули по ПЭТ-КТ и жидкостной биопсии.",
            "status": "done",
            "priority": "medium",
            "assignee_id": _demo_id(2003),  # Волков
            "created_by_id": _demo_id(2002),  # Кузнецова
            "source": "summary",
            "completed_at": NOW - timedelta(days=4),
            "created_at": NOW - timedelta(days=12),
        },
        {
            "id": _demo_id(3016),
            "title": "Организовать фотосессию для лекторов",
            "description": "Фото для сайта и соцсетей. Локация: офис, студия.",
            "status": "done",
            "priority": "low",
            "assignee_id": _demo_id(2011),  # Егоров
            "created_by_id": _demo_id(2004),  # Петрова
            "source": "voice",
            "completed_at": NOW - timedelta(days=7),
            "created_at": NOW - timedelta(days=20),
        },
        {
            "id": _demo_id(3017),
            "title": "Подготовить контент-план на апрель",
            "description": "Посты в Telegram (3/нед), статьи (2/мес), сторис (ежедневно).",
            "status": "done",
            "priority": "medium",
            "assignee_id": _demo_id(2006),  # Козлова
            "created_by_id": _demo_id(2004),  # Петрова
            "source": "web",
            "completed_at": NOW - timedelta(days=1),
            "created_at": NOW - timedelta(days=8),
        },
        # Overdue task (in_progress but past deadline)
        {
            "id": _demo_id(3018),
            "title": "Перевести методичку на английский язык",
            "description": "Методичка «Основы паллиативной помощи», 40 страниц.",
            "status": "in_progress",
            "priority": "medium",
            "assignee_id": _demo_id(2008),  # Федорова
            "created_by_id": _demo_id(2002),  # Кузнецова
            "source": "text",
            "deadline": TODAY - timedelta(days=3),  # overdue
            "created_at": NOW - timedelta(days=14),
        },
        # Unassigned tasks
        {
            "id": _demo_id(3019),
            "title": "Записать подкаст с профессором Козловым",
            "description": "Тема: новые подходы в лечении меланомы. 30-40 минут.",
            "status": "new",
            "priority": "medium",
            "assignee_id": None,
            "created_by_id": _demo_id(2001),  # Морозов
            "source": "voice",
            "created_at": NOW - timedelta(hours=8),
        },
        {
            "id": _demo_id(3020),
            "title": "Сделать инфографику по статистике рака в РФ",
            "description": "Данные Росстата 2024. Формат: карточки для Telegram.",
            "status": "new",
            "priority": "low",
            "assignee_id": None,
            "created_by_id": _demo_id(2004),  # Петрова
            "source": "web",
            "created_at": NOW - timedelta(days=2),
        },
        # Tasks with checklists
        {
            "id": _demo_id(3021),
            "title": "Подготовить конференцию «Онкология 2025»",
            "description": "Ежегодная конференция, 200+ участников.",
            "checklist": [
                {"id": "c1", "title": "Забронировать площадку", "is_completed": True},
                {"id": "c2", "title": "Утвердить список спикеров", "is_completed": True},
                {"id": "c3", "title": "Напечатать бейджи и раздатку", "is_completed": False},
                {"id": "c4", "title": "Протестировать онлайн-трансляцию", "is_completed": False},
                {"id": "c5", "title": "Отправить приглашения", "is_completed": True},
            ],
            "status": "in_progress",
            "priority": "urgent",
            "assignee_id": _demo_id(2001),  # Морозов
            "created_by_id": _demo_id(2000),  # Соколова
            "source": "web",
            "deadline": TODAY + timedelta(days=21),
            "created_at": NOW - timedelta(days=30),
        },
    ]


# ---------------------------------------------------------------------------
# Task Updates
# ---------------------------------------------------------------------------

def _task_updates() -> list[dict]:
    return [
        # Program for targeted therapy (in_progress)
        {
            "id": _demo_id(4000),
            "task_id": _demo_id(3004),
            "author_id": _demo_id(2003),
            "content": "Начал работу. Структура курса: 8 модулей по 2 лекции + практикум.",
            "update_type": "progress",
            "progress_percent": 20,
            "source": "web",
            "created_at": NOW - timedelta(days=6),
        },
        {
            "id": _demo_id(4001),
            "task_id": _demo_id(3004),
            "author_id": _demo_id(2003),
            "content": "Готовы модули 1-3. Ждём подтверждение от лекторов по модулям 4-6.",
            "update_type": "progress",
            "progress_percent": 45,
            "source": "telegram",
            "created_at": NOW - timedelta(days=3),
        },
        {
            "id": _demo_id(4002),
            "task_id": _demo_id(3004),
            "author_id": _demo_id(2002),
            "content": "Лектор по модулю 5 (радиотерапия) пока не подтвердил участие.",
            "update_type": "blocker",
            "source": "web",
            "created_at": NOW - timedelta(days=1),
        },
        # Promo video (in_progress)
        {
            "id": _demo_id(4003),
            "task_id": _demo_id(3005),
            "author_id": _demo_id(2011),
            "content": "Черновой монтаж готов, отправил на согласование.",
            "update_type": "progress",
            "progress_percent": 70,
            "source": "telegram",
            "created_at": NOW - timedelta(days=1),
        },
        # Bug fix (in_progress)
        {
            "id": _demo_id(4004),
            "task_id": _demo_id(3006),
            "author_id": _demo_id(2007),
            "content": "Нашёл причину: CSS grid не учитывает safe-area-inset на iOS.",
            "update_type": "comment",
            "source": "web",
            "created_at": NOW - timedelta(days=1),
        },
        {
            "id": _demo_id(4005),
            "task_id": _demo_id(3006),
            "author_id": _demo_id(2007),
            "content": "Фикс применён, тестирую на реальных устройствах.",
            "update_type": "progress",
            "progress_percent": 80,
            "source": "web",
            "created_at": NOW - timedelta(hours=4),
        },
        # Blog article (review)
        {
            "id": _demo_id(4006),
            "task_id": _demo_id(3009),
            "author_id": _demo_id(2006),
            "content": "Статья написана. 1800 слов, 5 трендов + инфографика.",
            "update_type": "status_change",
            "old_status": "in_progress",
            "new_status": "review",
            "source": "web",
            "created_at": NOW - timedelta(days=1),
        },
        # GetCourse integration (done)
        {
            "id": _demo_id(4007),
            "task_id": _demo_id(3013),
            "author_id": _demo_id(2007),
            "content": "Интеграция настроена: users, payments, orders синхронизируются ежедневно.",
            "update_type": "completion",
            "progress_percent": 100,
            "source": "web",
            "created_at": NOW - timedelta(days=6),
        },
        # Conference (in_progress, has checklist)
        {
            "id": _demo_id(4008),
            "task_id": _demo_id(3021),
            "author_id": _demo_id(2001),
            "content": "Площадка забронирована: конгресс-центр «Технополис», зал на 250 мест.",
            "update_type": "progress",
            "progress_percent": 30,
            "source": "telegram",
            "created_at": NOW - timedelta(days=20),
        },
        {
            "id": _demo_id(4009),
            "task_id": _demo_id(3021),
            "author_id": _demo_id(2001),
            "content": "Список из 12 спикеров утверждён. Приглашения отправлены.",
            "update_type": "progress",
            "progress_percent": 55,
            "source": "web",
            "created_at": NOW - timedelta(days=10),
        },
        # VK ads (in_progress)
        {
            "id": _demo_id(4010),
            "task_id": _demo_id(3008),
            "author_id": _demo_id(2004),
            "content": "Кампания запущена. CTR первого дня: 2.3%, что выше среднего.",
            "update_type": "progress",
            "progress_percent": 40,
            "source": "web",
            "created_at": NOW - timedelta(days=1),
        },
        # Content plan (done)
        {
            "id": _demo_id(4011),
            "task_id": _demo_id(3017),
            "author_id": _demo_id(2006),
            "content": "Контент-план утверждён. Темы расписаны на весь апрель.",
            "update_type": "completion",
            "progress_percent": 100,
            "source": "web",
            "created_at": NOW - timedelta(days=1),
        },
        # Translation (overdue)
        {
            "id": _demo_id(4012),
            "task_id": _demo_id(3018),
            "author_id": _demo_id(2008),
            "content": "Переведено 25 из 40 страниц. Медицинская терминология требует проверки нативным спикером.",
            "update_type": "progress",
            "progress_percent": 60,
            "source": "telegram",
            "created_at": NOW - timedelta(days=5),
        },
        {
            "id": _demo_id(4013),
            "task_id": _demo_id(3018),
            "author_id": _demo_id(2008),
            "content": "Не могу найти рецензента для медицинского английского. Нужна помощь.",
            "update_type": "blocker",
            "source": "web",
            "created_at": NOW - timedelta(days=2),
        },
    ]


# ---------------------------------------------------------------------------
# Meetings
# ---------------------------------------------------------------------------

def _meetings() -> list[dict]:
    return [
        # Completed meetings (past)
        {
            "id": _demo_id(5000),
            "title": "Еженедельная планёрка",
            "meeting_date": NOW - timedelta(days=7),
            "status": "completed",
            "duration_minutes": 45,
            "created_by_id": _demo_id(2001),
            "raw_summary": (
                "Обсудили статус текущих задач. Курс по таргетной терапии — "
                "в работе, 3 модуля готовы. Нужен лектор по радиотерапии. "
                "Промо-ролик на финальном этапе монтажа. "
                "Конференция: площадка забронирована, спикеры подтверждены."
            ),
            "parsed_summary": (
                "## Итоги планёрки\n\n"
                "### Статус задач\n"
                "- **Курс по таргетной терапии**: 3 из 8 модулей готовы, ищем лектора по радиотерапии\n"
                "- **Промо-ролик**: черновой монтаж готов, на согласовании\n"
                "- **Конференция «Онкология 2025»**: площадка и спикеры утверждены\n\n"
                "### Решения\n"
                "1. Морозов свяжется с проф. Сидоровой по лекции о радиотерапии\n"
                "2. Егоров доработает ролик к среде\n"
                "3. Петрова запустит VK-рекламу нового курса\n"
            ),
            "decisions": [
                "Морозов свяжется с проф. Сидоровой",
                "Егоров доработает ролик к среде",
                "Петрова запустит VK-рекламу",
            ],
            "created_at": NOW - timedelta(days=7),
        },
        {
            "id": _demo_id(5001),
            "title": "Разбор результатов потока Q1",
            "meeting_date": NOW - timedelta(days=14),
            "status": "completed",
            "duration_minutes": 60,
            "created_by_id": _demo_id(2002),
            "raw_summary": (
                "Поток Q1 завершён. 87 студентов из 102 получили сертификаты (85%). "
                "NPS = 72. Основные замечания: недостаточно практических кейсов "
                "в модуле по диагностике. Нужно обновить контент к следующему потоку."
            ),
            "parsed_summary": (
                "## Результаты потока Q1\n\n"
                "### Метрики\n"
                "- Студентов: 102 (зарегистрировано) → 87 (завершили) = **85%**\n"
                "- NPS: **72**\n"
                "- Средний балл: **4.2 / 5.0**\n\n"
                "### Выводы\n"
                "- Модуль по диагностике требует больше практических кейсов\n"
                "- Студенты просят больше интерактива (разборы случаев в прямом эфире)\n"
                "- Формат мини-тестов после каждой лекции оценён положительно\n"
            ),
            "decisions": [
                "Обновить модуль диагностики к потоку Q2",
                "Добавить live case discussions",
                "Сохранить формат мини-тестов",
            ],
            "created_at": NOW - timedelta(days=14),
        },
        {
            "id": _demo_id(5002),
            "title": "Стратегическая сессия: развитие на 2025",
            "meeting_date": NOW - timedelta(days=21),
            "status": "completed",
            "duration_minutes": 120,
            "created_by_id": _demo_id(2000),
            "parsed_summary": (
                "## Стратегия 2025\n\n"
                "### Приоритеты\n"
                "1. Запуск 3 новых курсов (таргетная терапия, паллиативная помощь, радиология)\n"
                "2. Рост аудитории: цель 500 студентов/квартал (текущий: ~100)\n"
                "3. Международное направление: перевод флагманского курса на английский\n\n"
                "### Бюджет\n"
                "- Маркетинг: +40% к текущему\n"
                "- Новые лекторы: 5 контрактов\n"
                "- Технологии: автоматизация отчётности и AI-ассистент\n"
            ),
            "decisions": [
                "Три новых курса в 2025",
                "Увеличить маркетинговый бюджет на 40%",
                "Начать перевод курса на английский",
            ],
            "created_at": NOW - timedelta(days=21),
        },
        # Upcoming meetings
        {
            "id": _demo_id(5003),
            "title": "Еженедельная планёрка",
            "meeting_date": NOW + timedelta(days=1),
            "status": "scheduled",
            "duration_minutes": 45,
            "created_by_id": _demo_id(2001),
            "zoom_join_url": "https://zoom.us/j/1234567890",
            "created_at": NOW - timedelta(hours=12),
        },
        {
            "id": _demo_id(5004),
            "title": "Обсуждение программы конференции",
            "meeting_date": NOW + timedelta(days=4),
            "status": "scheduled",
            "duration_minutes": 60,
            "created_by_id": _demo_id(2000),
            "zoom_join_url": "https://zoom.us/j/0987654321",
            "created_at": NOW - timedelta(days=1),
        },
    ]


MEETING_PARTICIPANTS = [
    # Planёrka (past)
    (_demo_id(5000), _demo_id(2000)),
    (_demo_id(5000), _demo_id(2001)),
    (_demo_id(5000), _demo_id(2002)),
    (_demo_id(5000), _demo_id(2003)),
    (_demo_id(5000), _demo_id(2004)),
    (_demo_id(5000), _demo_id(2005)),
    # Q1 review
    (_demo_id(5001), _demo_id(2000)),
    (_demo_id(5001), _demo_id(2001)),
    (_demo_id(5001), _demo_id(2002)),
    (_demo_id(5001), _demo_id(2008)),
    # Strategy
    (_demo_id(5002), _demo_id(2000)),
    (_demo_id(5002), _demo_id(2001)),
    (_demo_id(5002), _demo_id(2002)),
    (_demo_id(5002), _demo_id(2004)),
    # Upcoming planёrka
    (_demo_id(5003), _demo_id(2000)),
    (_demo_id(5003), _demo_id(2001)),
    (_demo_id(5003), _demo_id(2002)),
    (_demo_id(5003), _demo_id(2003)),
    (_demo_id(5003), _demo_id(2004)),
    (_demo_id(5003), _demo_id(2005)),
    (_demo_id(5003), _demo_id(2007)),
    # Conference discussion
    (_demo_id(5004), _demo_id(2000)),
    (_demo_id(5004), _demo_id(2001)),
    (_demo_id(5004), _demo_id(2011)),
]

# ---------------------------------------------------------------------------
# Meeting Schedules
# ---------------------------------------------------------------------------

MEETING_SCHEDULES = [
    {
        "id": _demo_id(6000),
        "title": "Еженедельная планёрка",
        "day_of_week": 1,  # Monday
        "time_utc": time(7, 0),  # 10:00 Moscow
        "timezone": "Europe/Moscow",
        "duration_minutes": 45,
        "recurrence": "weekly",
        "reminder_enabled": True,
        "reminder_offsets_minutes": [60, 0],
        "zoom_enabled": True,
        "is_active": True,
        "created_by_id": _demo_id(2001),
        "participant_ids": [
            _demo_id(2000), _demo_id(2001), _demo_id(2002),
            _demo_id(2003), _demo_id(2004), _demo_id(2005),
        ],
    },
    {
        "id": _demo_id(6001),
        "title": "Ежемесячный обзор результатов",
        "day_of_week": 5,  # Friday
        "time_utc": time(11, 0),  # 14:00 Moscow
        "timezone": "Europe/Moscow",
        "duration_minutes": 60,
        "recurrence": "monthly_last_workday",
        "reminder_enabled": True,
        "reminder_offsets_minutes": [1440, 60],
        "zoom_enabled": True,
        "is_active": True,
        "created_by_id": _demo_id(2000),
        "participant_ids": [
            _demo_id(2000), _demo_id(2001), _demo_id(2002),
            _demo_id(2004),
        ],
    },
]

# ---------------------------------------------------------------------------
# App Settings
# ---------------------------------------------------------------------------

APP_SETTINGS = [
    {
        "key": "ai_provider",
        "value": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
    },
]

# ---------------------------------------------------------------------------
# Daily Metrics (GetCourse reports)
# ---------------------------------------------------------------------------

def _daily_metrics() -> list[dict]:
    """Generate 60 days of realistic GetCourse metrics."""
    random.seed(42)  # Deterministic for reproducible screenshots
    metrics = []
    for days_ago in range(60):
        d = TODAY - timedelta(days=days_ago)
        # Weekend dip
        is_weekend = d.weekday() >= 5
        base_users = 35 if is_weekend else 52
        base_payments = 6 if is_weekend else 12
        base_orders = 4 if is_weekend else 9

        users = base_users + random.randint(-8, 12)
        payments_count = base_payments + random.randint(-3, 5)
        payments_sum = Decimal(payments_count * random.randint(1800, 2400))
        orders_count = base_orders + random.randint(-2, 4)
        orders_sum = Decimal(orders_count * random.randint(2000, 2800))

        metrics.append({
            "id": _demo_id(7000 + days_ago),
            "metric_date": d,
            "source": "getcourse",
            "users_count": max(users, 10),
            "payments_count": max(payments_count, 1),
            "payments_sum": payments_sum,
            "orders_count": max(orders_count, 1),
            "orders_sum": orders_sum,
            "collected_by_id": _demo_id(2000),  # admin
            "collected_at": NOW - timedelta(days=days_ago, hours=1),
        })
    return metrics


# ---------------------------------------------------------------------------
# Seed & Cleanup
# ---------------------------------------------------------------------------

async def seed(session: AsyncSession) -> None:
    """Insert all demo data."""

    # Check if demo data already exists
    existing = await session.execute(
        select(TeamMember).where(TeamMember.id == _demo_id(2000))
    )
    if existing.scalar_one_or_none():
        print("Demo data already exists. Run with --clean first.")
        return

    # 1. Departments (without heads first)
    for dept_data in DEPARTMENTS:
        dept = Department(**dept_data)
        session.add(dept)

    await session.flush()

    # 2. Team members
    for member_data in MEMBERS:
        member = TeamMember(**member_data)
        session.add(member)

    await session.flush()

    # 3. Set department heads
    for dept_id, head_id in DEPARTMENT_HEADS.items():
        dept = await session.get(Department, dept_id)
        if dept:
            dept.head_id = head_id

    await session.flush()

    # 4. Tasks (assign short_id starting from max existing + 1)
    max_sid_result = await session.execute(
        select(func.coalesce(func.max(Task.short_id), 0))
    )
    next_short_id = max_sid_result.scalar_one() + 1

    for i, task_data in enumerate(_tasks()):
        task_data = {**task_data}
        task_data.setdefault("checklist", [])
        task_data["short_id"] = next_short_id + i
        task = Task(**task_data)
        session.add(task)

    await session.flush()

    # 5. Task updates
    for update_data in _task_updates():
        update = TaskUpdate(**update_data)
        session.add(update)

    # 6. Meetings
    for meeting_data in _meetings():
        meeting_data = {**meeting_data}
        meeting_data.setdefault("decisions", [])
        meeting = Meeting(**meeting_data)
        session.add(meeting)

    await session.flush()

    # 7. Meeting participants
    for meeting_id, member_id in MEETING_PARTICIPANTS:
        session.add(MeetingParticipant(
            meeting_id=meeting_id,
            member_id=member_id,
        ))

    # 8. Meeting schedules
    for schedule_data in MEETING_SCHEDULES:
        schedule_data = {**schedule_data}
        # participant_ids is an ARRAY field, keep as-is
        schedule = MeetingSchedule(**schedule_data)
        session.add(schedule)

    # 9. App settings (upsert)
    for setting_data in APP_SETTINGS:
        existing_setting = await session.execute(
            select(AppSettings).where(AppSettings.key == setting_data["key"])
        )
        s = existing_setting.scalar_one_or_none()
        if s:
            s.value = setting_data["value"]
        else:
            session.add(AppSettings(**setting_data))

    # 10. GetCourse credentials (so Reports page shows data)
    existing_gc = await session.execute(
        select(GetCourseCredentials).where(GetCourseCredentials.id == 1)
    )
    if not existing_gc.scalar_one_or_none():
        session.add(GetCourseCredentials(
            id=1,
            base_url="https://oncoschool.getcourse.ru",
            api_key_encrypted="demo-fake-encrypted-key",
            updated_by_id=_demo_id(2000),
        ))

    # 11. Daily metrics (60 days of GetCourse data)
    for metric_data in _daily_metrics():
        session.add(DailyMetric(**metric_data))

    await session.commit()

    print("Demo data seeded successfully!")
    print()
    print("Login credentials (DEBUG=true required):")
    print("  Admin:     telegram_id = 100001 (Елена Соколова)")
    print("  Moderator: telegram_id = 100002 (Алексей Морозов)")
    print("  Member:    telegram_id = 100003 (Дмитрий Волков)")


async def clean(session: AsyncSession) -> None:
    """Remove all demo data."""
    demo_member_ids = [_demo_id(2000 + i) for i in range(12)]
    demo_task_ids = [_demo_id(3000 + i) for i in range(22)]
    demo_meeting_ids = [_demo_id(5000 + i) for i in range(5)]
    demo_dept_ids = [_demo_id(1000 + i) for i in range(5)]
    demo_schedule_ids = [_demo_id(6000 + i) for i in range(2)]
    demo_metric_ids = [_demo_id(7000 + i) for i in range(60)]

    # Delete in dependency order
    await session.execute(
        delete(DailyMetric).where(DailyMetric.id.in_(demo_metric_ids))
    )
    await session.execute(
        delete(GetCourseCredentials).where(GetCourseCredentials.id == 1)
    )
    await session.execute(
        delete(TaskUpdate).where(TaskUpdate.task_id.in_(demo_task_ids))
    )
    await session.execute(
        delete(MeetingParticipant).where(
            MeetingParticipant.meeting_id.in_(demo_meeting_ids)
        )
    )
    await session.execute(
        delete(Task).where(Task.id.in_(demo_task_ids))
    )
    await session.execute(
        delete(Meeting).where(Meeting.id.in_(demo_meeting_ids))
    )
    await session.execute(
        delete(MeetingSchedule).where(
            MeetingSchedule.id.in_(demo_schedule_ids)
        )
    )
    await session.execute(
        delete(ReminderSettings).where(
            ReminderSettings.member_id.in_(demo_member_ids)
        )
    )
    # Clear department heads before deleting members
    for dept_id in demo_dept_ids:
        dept = await session.get(Department, dept_id)
        if dept:
            dept.head_id = None
    await session.flush()

    # Clear member department_id before deleting departments
    for mid in demo_member_ids:
        member = await session.get(TeamMember, mid)
        if member:
            member.department_id = None
    await session.flush()

    await session.execute(
        delete(TeamMember).where(TeamMember.id.in_(demo_member_ids))
    )
    await session.execute(
        delete(Department).where(Department.id.in_(demo_dept_ids))
    )

    await session.commit()
    print("Demo data cleaned up.")


async def main(do_clean: bool = False) -> None:
    async with async_session() as session:
        if do_clean:
            await clean(session)
        else:
            await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed or clean demo data")
    parser.add_argument("--clean", action="store_true", help="Remove demo data")
    args = parser.parse_args()
    asyncio.run(main(do_clean=args.clean))
