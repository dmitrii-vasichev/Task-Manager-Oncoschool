# Telegram Mini App — План реализации

> **Цель:** Заменить взаимодействие через слэш-команды на полноценное веб-приложение (Mini App) внутри Telegram, сохранив при этом обратную совместимость с командами бота.

## Контекст

### Текущее состояние
- Взаимодействие с задачами через `/tasks`, `/new`, `/done`, `/status`, `/update` — неудобно для ~20 человек
- Есть полноценный веб-интерфейс (Next.js 14) с Kanban-доской, но он существует отдельно от Telegram
- Авторизация в вебе через Telegram Login Widget (redirect)
- Бот работает в polling-режиме (aiogram 3.x), API — FastAPI

### Что даёт Mini App
- **Мгновенный доступ** к задачам из Telegram без переключения контекста
- **Нативная авторизация** через initData (без Telegram Login Widget redirect)
- **Haptic feedback, тема Telegram, кнопка назад** — нативный UX
- **Одна кодовая база** — Mini App = облегчённая версия существующего Next.js фронтенда

### Архитектурное решение

**Mini App как отдельное Next.js-приложение** в папке `mini-app/` рядом с `frontend/`.

Причины:
1. **Разный UX:** десктопный веб ≠ мобильный Telegram (другая навигация, другие приоритеты экранов)
2. **Telegram SDK зависимости:** `@tma.js/sdk-react`, CSS-переменные Telegram, viewport-хуки — загрязняют основной фронтенд
3. **Независимый деплой:** Mini App на отдельном домене/субдомене (Vercel), основной фронт не затрагивается
4. **Переиспользование:** API-клиент, типы, утилиты можно шарить через общую папку `shared/`

**Бэкенд:** новый эндпоинт `/api/auth/mini-app` для валидации initData + выдачи JWT. Остальные API-эндпоинты переиспользуются как есть.

---

## Стек Mini App

| Слой | Технология | Почему |
|------|-----------|--------|
| Фреймворк | Next.js 14 (App Router) | Единообразие со стеком, SSR не нужен — можно `output: 'export'` для статики |
| Язык | TypeScript | Единообразие |
| UI | Tailwind CSS + Telegram CSS-переменные | Нативный вид внутри Telegram |
| Telegram SDK | `@tma.js/sdk-react` | React-хуки для initData, viewport, theme, back button |
| Состояние | React Context + TanStack Query | Кеширование API, оптимистичные обновления |
| Деплой | Vercel (отдельный проект) | HTTPS обязателен для Mini App |

---

## Экраны Mini App

### Основные (MVP)
1. **Мои задачи** (главный экран) — список с фильтрами по статусу, свайп-действия
2. **Детали задачи** — полная информация, timeline обновлений, смена статуса, добавление апдейта
3. **Создание задачи** — форма с заголовком, приоритетом, дедлайном, назначением
4. **Все задачи** (для moderator/admin) — командный обзор

### Дополнительные (пост-MVP)
5. **Dashboard** — краткая сводка (мои задачи, просроченные, ближайшие дедлайны)
6. **Встречи** — список предстоящих, ссылки на Zoom

---

## Структура файлов

```
Task_Manager_Oncoschool/
├── backend/                    # Существующий бэкенд (+ новый эндпоинт auth)
├── frontend/                   # Существующий десктопный веб-интерфейс
├── mini-app/                   # НОВОЕ: Telegram Mini App
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx              # TelegramProvider, QueryProvider
│   │   │   ├── page.tsx                # Redirect → /tasks
│   │   │   ├── tasks/
│   │   │   │   ├── page.tsx            # Мои задачи (список)
│   │   │   │   ├── [id]/page.tsx       # Детали задачи
│   │   │   │   └── new/page.tsx        # Создание задачи
│   │   │   └── all/page.tsx            # Все задачи (moderator)
│   │   ├── components/
│   │   │   ├── TaskCard.tsx
│   │   │   ├── TaskStatusBadge.tsx
│   │   │   ├── PriorityBadge.tsx
│   │   │   ├── TaskForm.tsx
│   │   │   ├── UpdateTimeline.tsx
│   │   │   ├── BottomNav.tsx           # Нижняя навигация
│   │   │   ├── StatusAction.tsx        # Быстрая смена статуса
│   │   │   └── EmptyState.tsx
│   │   ├── lib/
│   │   │   ├── api.ts                  # API-клиент (адаптация из frontend/)
│   │   │   ├── telegram.ts             # Telegram SDK обёртки
│   │   │   ├── types.ts                # Типы (копия/импорт из frontend/)
│   │   │   └── auth.ts                 # initData → JWT логика
│   │   ├── hooks/
│   │   │   ├── useTelegram.ts          # Хук для Telegram WebApp
│   │   │   ├── useAuth.ts             # Авторизация через initData
│   │   │   └── useTasks.ts            # TanStack Query хуки для задач
│   │   └── providers/
│   │       ├── TelegramProvider.tsx    # Инициализация SDK
│   │       ├── AuthProvider.tsx        # Контекст авторизации
│   │       └── QueryProvider.tsx       # TanStack Query
│   ├── public/
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   ├── package.json
│   └── tsconfig.json
└── MINI_APP_PLAN.md            # Этот файл
```

---

## Фазы реализации

---

### Фаза MA1: Backend — Auth endpoint для Mini App + BotFather настройка

**Цель:** Создать эндпоинт валидации initData и настроить бота для запуска Mini App.

**Промпт для Claude Code:**

```
Прочитай MINI_APP_PLAN.md, секцию «Фаза MA1».

## Задача

Добавить новый эндпоинт авторизации для Telegram Mini App и обновить бота.

## Шаги

### 1. Новый эндпоинт POST /api/auth/mini-app

Файл: `backend/app/api/auth.py`

Добавь эндпоинт `POST /api/auth/mini-app` который:
- Принимает JSON `{ "init_data": "<raw initData string>" }`
- Валидирует подпись initData используя `aiogram.utils.web_app.safe_parse_webapp_init_data(bot_token, init_data)` — это встроенная утилита aiogram 3.x
- Извлекает `user.id` (telegram_id) из распарсенных данных
- Ищет TeamMember по telegram_id в БД
- Если не найден или не активен → 403
- Если найден → генерирует JWT (через существующий `create_access_token`) и возвращает `TokenResponse`
- Обновляет telegram_username если изменился (как в существующем `/api/auth/telegram`)

Сигнатура ответа такая же как у `/api/auth/telegram`:
```python
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    member_id: str
    role: str
```

### 2. Кнопка Menu Button в боте

Файл: `backend/app/bot/handlers/common.py`

Добавь inline-кнопку «📋 Открыть задачи» с `WebAppInfo(url=...)` в ответ на `/start`.
URL берётся из новой env-переменной `MINI_APP_URL` (по умолчанию пустая строка — если пустая, кнопку не показываем).

Файл: `backend/app/config.py`
Добавь: `MINI_APP_URL: str = ""`

### 3. Команда /app

Файл: `backend/app/bot/handlers/common.py`

Добавь команду `/app` которая отправляет inline-кнопку с WebAppInfo для открытия Mini App.
Если MINI_APP_URL пустой — сообщение "Mini App не настроен".

### 4. НЕ ТРОГАЙ существующие эндпоинты

Все остальные API-эндпоинты остаются без изменений. Mini App будет использовать те же `/api/tasks`, `/api/team` и т.д. с JWT-токеном.

## Проверка

- POST /api/auth/mini-app с невалидным init_data → 401
- POST /api/auth/mini-app с валидным init_data → JWT + member_id + role
- /app в боте показывает кнопку открытия Mini App
- /start показывает кнопку "Открыть задачи" (если MINI_APP_URL задан)
```

---

### Фаза MA2: Mini App каркас — проект, Telegram SDK, авторизация

**Цель:** Создать проект Mini App с инициализацией Telegram SDK и автоматической авторизацией.

**Промпт для Claude Code:**

```
Прочитай MINI_APP_PLAN.md, секцию «Фаза MA2».

## Задача

Создать новый Next.js проект для Telegram Mini App с авторизацией через initData.

## Шаги

### 1. Инициализация проекта

Создай директорию `mini-app/` в корне проекта. Инициализируй Next.js 14:

```bash
cd mini-app
npx create-next-app@14 . --typescript --tailwind --eslint --app --src-dir --no-import-alias
```

Установи зависимости:
```bash
npm install @tma.js/sdk-react @tanstack/react-query
```

### 2. Tailwind с Telegram CSS-переменными

Файл: `mini-app/tailwind.config.ts`

Настрой цвета через CSS-переменные Telegram:
```typescript
colors: {
  tg: {
    bg: 'var(--tg-theme-bg-color, #ffffff)',
    text: 'var(--tg-theme-text-color, #000000)',
    hint: 'var(--tg-theme-hint-color, #999999)',
    link: 'var(--tg-theme-link-color, #2481cc)',
    button: 'var(--tg-theme-button-color, #2481cc)',
    'button-text': 'var(--tg-theme-button-text-color, #ffffff)',
    'secondary-bg': 'var(--tg-theme-secondary-bg-color, #f0f0f0)',
    'header-bg': 'var(--tg-theme-header-bg-color, #ffffff)',
    'section-bg': 'var(--tg-theme-section-bg-color, #ffffff)',
    'accent': 'var(--tg-theme-accent-text-color, #2481cc)',
    'destructive': 'var(--tg-theme-destructive-text-color, #ff3b30)',
    'subtitle': 'var(--tg-theme-subtitle-text-color, #999999)',
    'section-header': 'var(--tg-theme-section-header-text-color, #6d6d72)',
    separator: 'var(--tg-theme-section-separator-color, #c8c7cc)',
  }
}
```

### 3. Telegram Provider

Файл: `mini-app/src/providers/TelegramProvider.tsx`

Создай React-контекст с инициализацией @tma.js/sdk-react:
- Вызвать `init()` из SDK
- Обработать случай когда приложение открыто НЕ в Telegram (fallback для разработки)
- Предоставить в контексте: initDataRaw, user, colorScheme, viewportHeight
- Вызвать `miniApp.ready()` после инициализации
- Настроить Back Button: `backButton.show()` на внутренних страницах, `backButton.hide()` на главной

### 4. Auth Provider

Файл: `mini-app/src/providers/AuthProvider.tsx`

При монтировании:
1. Получить `initDataRaw` из Telegram SDK
2. Отправить POST на `${API_URL}/api/auth/mini-app` с `{ init_data: initDataRaw }`
3. Сохранить JWT в памяти (НЕ localStorage — Mini App живёт в WebView)
4. Предоставить в контексте: `token`, `member`, `isLoading`, `error`

Fallback для разработки вне Telegram:
- Если `initDataRaw` пустой и `process.env.NEXT_PUBLIC_DEBUG === 'true'` → использовать dev-login по Telegram ID

### 5. API-клиент

Файл: `mini-app/src/lib/api.ts`

Адаптированная версия из `frontend/src/lib/api.ts`:
- Убрать localStorage для токена (хранить в памяти)
- Добавить метод `loginMiniApp(initData: string): Promise<LoginResponse>`
- Убрать метод `loginWithTelegram` (не нужен в Mini App)
- Все остальные методы — скопировать как есть

### 6. Types

Файл: `mini-app/src/lib/types.ts`

Скопировать нужные типы из `frontend/src/lib/types.ts`:
- Task, TaskCreateRequest, TaskEditRequest, TaskUpdate, TaskUpdateCreateRequest
- TeamMember, PaginatedResponse
- LoginResponse

### 7. Layout

Файл: `mini-app/src/app/layout.tsx`

```tsx
// TelegramProvider → AuthProvider → QueryProvider → children
// global.css с Tailwind + Telegram CSS переменные
// viewport: width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no
```

### 8. Главная страница (заглушка)

Файл: `mini-app/src/app/page.tsx`

Показать имя пользователя из auth-контекста и его роль. Кнопка "Мои задачи" (пока ссылка).

### 9. Env

Файл: `mini-app/.env.local.example`
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DEBUG=true
```

## Проверка

- `cd mini-app && npm run dev` запускается без ошибок
- В обычном браузере: показывает fallback "Откройте в Telegram" (или dev-login в debug-режиме)
- Цвета Tailwind используют Telegram CSS-переменные
- AuthProvider получает JWT через /api/auth/mini-app
```

---

### Фаза MA3: Экран «Мои задачи» — список, фильтры, навигация

**Цель:** Главный экран Mini App — список задач текущего пользователя с фильтрацией и навигацией.

**Промпт для Claude Code:**

```
Прочитай MINI_APP_PLAN.md, секцию «Фаза MA3».

## Задача

Реализовать экран "Мои задачи" — основной экран Mini App.

## Шаги

### 1. TanStack Query хуки

Файл: `mini-app/src/hooks/useTasks.ts`

```typescript
// useMyTasks() — GET /api/tasks?assignee_id={currentUser.id}&status=new,in_progress,review
// useAllTasks() — GET /api/tasks (для moderator)
// useTask(shortId) — GET /api/tasks/{shortId}
// useCreateTask() — POST /api/tasks
// useUpdateTaskStatus(shortId) — PATCH /api/tasks/{shortId}
// useCreateTaskUpdate(shortId) — POST /api/tasks/{shortId}/updates
```

Используй `@tanstack/react-query` с `queryClient` из QueryProvider.
Invalidate `['tasks']` при мутациях.

### 2. Компонент TaskCard

Файл: `mini-app/src/components/TaskCard.tsx`

Компактная карточка задачи для мобильного:
- Заголовок (обрезанный до 2 строк)
- Иконки приоритета: 🔴 urgent, ⚡ high, 🔵 medium, ⚪ low
- Статус-бейдж (цветной)
- Дедлайн (если есть, красный если просрочен)
- Иконка 🎤 если source === "voice"
- Short ID (#42)
- Клик → переход на /tasks/{shortId}

Стили: используй tg-* цвета из Tailwind. Карточка — `bg-tg-section-bg`, текст — `text-tg-text`, hint — `text-tg-hint`.

### 3. Фильтры по статусу

Файл: `mini-app/src/components/StatusFilter.tsx`

Горизонтальная полоска чипов-фильтров:
- Все | Новые | В работе | Ревью
- Активный чип — bg-tg-button, text-tg-button-text
- Неактивный — bg-tg-secondary-bg, text-tg-hint
- Используй haptic feedback при переключении: `hapticFeedback.selectionChanged()`

### 4. Нижняя навигация

Файл: `mini-app/src/components/BottomNav.tsx`

Фиксированная нижняя панель:
- 📋 Мои задачи (активная по умолчанию)
- 📊 Все задачи (только для moderator/admin)
- ➕ Создать (большая кнопка по центру)

Используй `safe-area-inset-bottom` для отступа снизу (iPhone).

### 5. Страница "Мои задачи"

Файл: `mini-app/src/app/tasks/page.tsx`

- StatusFilter сверху
- Список TaskCard
- Pull-to-refresh (через overscroll + refetch)
- Если задач нет — EmptyState с иллюстрацией
- Группировка: "Просроченные" (красный заголовок) → "Сегодня" → "Остальные"
- Skeleton-загрузка при первом рендере
- `miniApp.ready()` после загрузки данных

### 6. Страница "Все задачи"

Файл: `mini-app/src/app/all/page.tsx`

Аналогично "Мои задачи", но:
- Показывает все задачи команды
- В каждой карточке добавлено имя исполнителя
- Доступна только moderator/admin (redirect на /tasks если member)

## Дизайн-гайдлайны

- Минимализм, чистые линии, как нативное Telegram-приложение
- Скругления: 12px для карточек
- Отступы: 16px по бокам
- Шрифт: system font stack (Telegram подставит нативный)
- Анимации: subtle transitions 150ms для фильтров, карточек
- Haptic feedback на все интерактивные действия

## Проверка

- Список задач загружается через API с JWT
- Фильтры по статусу работают
- Карточки кликабельны (переход на детали — пока 404)
- Нижняя навигация переключает экраны
- Haptic feedback при нажатиях
```

---

### Фаза MA4: Детали задачи + смена статуса + создание задачи

**Цель:** Экран детальной информации о задаче, быстрые действия со статусом и форма создания.

**Промпт для Claude Code:**

```
Прочитай MINI_APP_PLAN.md, секцию «Фаза MA4».

## Задача

Реализовать экран деталей задачи, быстрые действия и форму создания.

## Шаги

### 1. Страница деталей задачи

Файл: `mini-app/src/app/tasks/[id]/page.tsx`

Показывает:
- Заголовок задачи
- Статус (цветной бейдж)
- Приоритет
- Исполнитель (имя + аватар)
- Создатель
- Дедлайн
- Описание (если есть)
- Дата создания

**Кнопки быстрых действий** (горизонтальный ряд):
- ▶️ В работу (если new)
- 👀 Ревью (если in_progress)
- ✅ Готово (всегда, кроме done/cancelled)
- 📝 Апдейт (открывает форму)

При смене статуса:
- Optimistic update через TanStack Query
- Haptic feedback: `hapticFeedback.notificationOccurred('success')`
- Анимация смены бейджа

**Для moderator:**
- ❌ Отменить
- 🔄 Переназначить (bottom sheet со списком команды)

### 2. Timeline обновлений

Файл: `mini-app/src/components/UpdateTimeline.tsx`

Под деталями задачи — timeline всех обновлений:
- Иконка типа обновления (progress, status_change, blocker, comment, completion)
- Автор + время
- Текст обновления
- Прогресс % (если есть)
- Сортировка: новые сверху

### 3. Форма добавления апдейта

Bottom sheet (slide up) с:
- Текстовое поле (textarea, auto-resize)
- Тип: progress / comment / blocker (сегментированный контрол)
- Прогресс % (slider, только для типа progress)
- Кнопка "Отправить" — MainButton Telegram

Используй `mainButton` из Telegram SDK:
```typescript
mainButton.setText('Отправить');
mainButton.show();
mainButton.onClick(() => submitUpdate());
// После отправки: mainButton.hide()
```

### 4. Back Button

На страницах деталей:
```typescript
backButton.show();
backButton.onClick(() => router.back());
// При уходе со страницы: backButton.hide()
```

### 5. Страница создания задачи

Файл: `mini-app/src/app/tasks/new/page.tsx`

Форма:
- Заголовок (обязательный input)
- Описание (textarea, опционально)
- Приоритет (4 кнопки: low/medium/high/urgent)
- Дедлайн (native date picker)
- Назначить (dropdown со списком участников — только для moderator)

Отправка через MainButton:
```typescript
mainButton.setText('Создать задачу');
mainButton.enable();
mainButton.onClick(() => createTask());
```

После успешного создания:
- `hapticFeedback.notificationOccurred('success')`
- Redirect на /tasks
- Invalidate query cache

### 6. Переназначение (moderator)

Компонент `ReassignSheet.tsx` — bottom sheet:
- Список участников команды (из GET /api/team)
- Аватар + имя
- Поиск по имени
- При выборе → PATCH /api/tasks/{id} с новым assignee_id

## Проверка

- Детали задачи загружаются по short_id
- Смена статуса работает с оптимистичным обновлением
- Timeline обновлений отображается
- Форма добавления апдейта через bottom sheet
- MainButton Telegram используется для отправки
- Back Button работает на всех внутренних страницах
- Создание задачи работает
- Haptic feedback на всех действиях
```

---

### Фаза MA5: Интеграция с ботом + полировка + деплой

**Цель:** Связать Mini App с ботом, отполировать UI, задеплоить.

**Промпт для Claude Code:**

```
Прочитай MINI_APP_PLAN.md, секцию «Фаза MA5».

## Задача

Финальная интеграция, полировка UI и деплой Mini App.

## Шаги

### 1. Menu Button бота

Файл: `backend/app/main.py`

При старте бота, если `MINI_APP_URL` задан, установить Menu Button:
```python
from aiogram.types import MenuButtonWebApp, WebAppInfo

if settings.MINI_APP_URL:
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="📋 Задачи",
            web_app=WebAppInfo(url=settings.MINI_APP_URL)
        )
    )
```

Это добавит кнопку слева от поля ввода в чате с ботом.

### 2. Inline-кнопки с Mini App в уведомлениях

Файл: `backend/app/services/notification_service.py`

При отправке уведомлений о задачах (created, assigned, status_changed) — добавить inline-кнопку "Открыть задачу" с WebAppInfo:
```python
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

if settings.MINI_APP_URL:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📋 Открыть задачу",
            web_app=WebAppInfo(url=f"{settings.MINI_APP_URL}/tasks/{task.short_id}")
        )
    ]])
```

Это позволит открыть конкретную задачу прямо из уведомления.

### 3. Полировка UI Mini App

#### 3.1 Loading states
- Skeleton для списка задач (3 заглушки карточек)
- Spinner для деталей задачи
- Disabled MainButton во время отправки

#### 3.2 Error states
- Ошибка сети → retry кнопка
- 403 → "У вас нет доступа"
- Общая ошибка → toast внизу экрана

#### 3.3 Pull to refresh
Простая реализация через overscroll:
- При свайпе вниз на верхней позиции → refetch queries
- Показать индикатор загрузки

#### 3.4 Transitions
- Переходы между страницами: slide-in-right / slide-out-left
- Появление bottom sheet: slide-up с backdrop
- Смена статуса: цветовой переход на бейдже

#### 3.5 Empty states
- Нет задач: иконка + текст "Нет активных задач 🎉"
- Ошибка загрузки: иконка + кнопка "Повторить"

#### 3.6 Safe areas
```css
padding-bottom: env(safe-area-inset-bottom);
padding-top: env(safe-area-inset-top);
```

### 4. CORS — добавить домен Mini App

Файл: `backend/app/config.py`

Добавить `MINI_APP_URL` в CORS_ORIGINS если он задан:
```python
@property
def all_cors_origins(self) -> list[str]:
    origins = list(self.CORS_ORIGINS)
    if self.MINI_APP_URL:
        origins.append(self.MINI_APP_URL)
    return origins
```

И использовать `all_cors_origins` в `main.py`.

### 5. Деплой Mini App на Vercel

Файл: `mini-app/vercel.json`
```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "installCommand": "npm install"
}
```

Инструкции:
1. Создать новый проект на Vercel, указать `mini-app/` как root
2. Установить env: `NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app`
3. Задеплоить → получить URL (например https://oncoschool-mini.vercel.app)
4. Прописать URL в .env бэкенда: `MINI_APP_URL=https://oncoschool-mini.vercel.app`
5. Через @BotFather: `/setmenubutton` → Web App URL

### 6. Обновить CLAUDE.md

Добавь в CLAUDE.md:
- Секцию про Mini App в "Обзор"
- Чеклист фаз MA1-MA5
- Запуск: `cd mini-app && npm run dev`

## Проверка

- Menu Button в чате с ботом открывает Mini App
- Уведомления о задачах содержат кнопку "Открыть задачу"
- Mini App работает в Telegram (мобильном и десктопном)
- Авторизация автоматическая через initData
- Все CRUD-операции с задачами работают
- Haptic feedback, Back Button, MainButton — всё нативное
- Тема Telegram (light/dark) поддерживается
- Safe areas на iPhone корректны
- Деплой на Vercel + HTTPS
```

---

## Чеклист прогресса

| Фаза | Описание | Статус |
|------|----------|--------|
| MA1 | Backend auth endpoint + /app команда | [ ] |
| MA2 | Mini App каркас + Telegram SDK + авторизация | [ ] |
| MA3 | Экран "Мои задачи" + фильтры + навигация | [ ] |
| MA4 | Детали задачи + действия + создание | [ ] |
| MA5 | Интеграция с ботом + полировка + деплой | [ ] |

---

## Важные нюансы

### Безопасность
- initData валидируется через HMAC-SHA256 на бэкенде (aiogram built-in)
- JWT токен хранится только в памяти WebView (не localStorage)
- Mini App URL должен быть HTTPS

### Совместимость
- Слэш-команды бота остаются работоспособными (обратная совместимость)
- Веб-интерфейс (frontend/) не затрагивается
- API-эндпоинты не меняются (кроме добавления нового auth)

### Telegram SDK ключевые API
- `miniApp.ready()` — сообщить Telegram что приложение загружено
- `mainButton` — нативная кнопка внизу экрана
- `backButton` — кнопка "Назад" в header Telegram
- `hapticFeedback` — вибрация при действиях
- `themeParams` — CSS-переменные темы (автоматически)
- `viewport` — размеры и safe areas
- `initDataRaw` — строка для авторизации на бэкенде

### Что НЕ входит в MVP
- Голосовые задачи (остаются через бот)
- Управление расписанием встреч (через веб)
- Управление командой (через веб)
- Настройки AI-провайдера (через веб)
- Аналитика (через веб)
- Push-уведомления Mini App (используем обычные Telegram-уведомления)
