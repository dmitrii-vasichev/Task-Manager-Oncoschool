# Hint Inventory (P0 baseline)

Дата: 2026-02-24
Статус: Draft v1

Колонки:
- `hint_id`: стабильный идентификатор подсказки.
- `route`: экран.
- `ui_anchor`: где в UI показываем.
- `trigger`: условие показа.
- `role_scope`: для каких ролей.
- `hint_type`: `Orientation | Permission | Validation | Action-impact | State | Cross-link`.
- `priority`: `P0 | P1 | P2`.
- `copy`: текущая формулировка.
- `status`: `planned | in_progress | done`.

| hint_id | route | ui_anchor | trigger | role_scope | hint_type | priority | copy | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dashboard.scope_switch.orientation | `/` | Переключатель `Мои/Отдел` | Первый вход на Dashboard | all | Orientation | P0 | Переключатель `Мои/Отдел` меняет источник задач и встреч в блоках ниже. | planned |
| dashboard.no_departments.member | `/` | Блок выбора отдела | Нет доступных отделов | member | Permission | P0 | У вас нет доступного отдела, поэтому показываются только личные задачи. | planned |
| dashboard.overdue.priority | `/` | Блок `Просроченные` | Есть просроченные задачи | all | Action-impact | P0 | Просроченные задачи требуют приоритета: откройте карточку и обновите статус/дедлайн. | planned |
| dashboard.stale.tasks | `/` | Блок `Не обновлялись` | Есть stale-задачи (>3 дней без апдейта) | all | State | P0 | Задача без апдейта >3 дней попадает в этот блок. Добавьте обновление в карточке задачи. | planned |
| dashboard.unassigned.tasks | `/` | Блок `Ожидают назначения` | Есть задачи без исполнителя | moderator,admin | Cross-link | P0 | Эти задачи без исполнителя. Назначьте ответственного в карточке задачи. | planned |
| task_detail.status_transitions | `/tasks/[id]` | Панель переходов статуса | Открытие блока смены статуса | all | Orientation | P0 | Доступные переходы статуса зависят от текущего статуса задачи. | planned |
| task_detail.reminder.no_assignee | `/tasks/[id]` | Блок `Напоминание` | У задачи нет исполнителя | all | Validation | P0 | Напоминание доступно только для задач с назначенным исполнителем. | planned |
| task_detail.reminder.timezone_future | `/tasks/[id]` | Кнопка сохранения напоминания | Валидация при сохранении напоминания | all | Validation | P0 | Время задаётся в МСК и должно быть в будущем. | planned |
| task_detail.edit.permissions | `/tasks/[id]` | Поля описания/дедлайна/приоритета | Пользователь без прав пытается редактировать | member | Permission | P0 | Часть полей доступна автору задачи и модератору. | planned |
| task_detail.delete.irreversible | `/tasks/[id]` | Confirm dialog удаления | Нажатие удаления | moderator,admin | Action-impact | P0 | Удаление без восстановления. Убедитесь, что в задаче нет критичных договорённостей. | planned |
| meeting_detail.transcript.zoom_pending | `/meetings/[id]` | `TranscriptTab` state без transcript | Нет transcript, но есть Zoom meeting id | moderator,admin | State | P0 | После завершения встречи транскрипт подтянется из Zoom автоматически; можно запросить вручную. | planned |
| meeting_detail.ai_parse.provider | `/meetings/[id]` | Кнопка `Обработать через AI` | Запуск AI parse | moderator,admin | Action-impact | P0 | AI-парсинг использует текущие настройки провайдера из `Settings`. | planned |
| meeting_detail.summary.apply_effect | `/meetings/[id]` | Кнопка применения summary | Подтверждение применения summary | moderator,admin | Action-impact | P0 | После применения будут созданы задачи и уведомления по встрече. | planned |
| meeting_detail.tasks.empty_crosslink | `/meetings/[id]` | Вкладка `Tasks` пустая | Нет задач встречи | moderator,admin | Cross-link | P0 | Обработайте транскрипцию через AI, чтобы автоматически создать задачи из встречи. | planned |
| meeting_detail.participants.impact | `/meetings/[id]` | Блок участников | Изменение участников | moderator,admin | Action-impact | P0 | Список участников влияет на упоминания и уведомления по расписанию. | planned |
| team.member_create.name_variants | `/team` | Модал создания участника | Открытие формы создания | moderator,admin | Orientation | P0 | `Варианты имени` нужны для более точного AI-матчинга в summary. | planned |
| team.role_change.admin_only | `/team` | Поле выбора роли | Изменение роли недоступно | moderator | Permission | P0 | Менять роли может только администратор. | planned |
| team.deactivate.strategy | `/team` | Confirm dialog деактивации | Подтверждение деактивации | moderator,admin | Action-impact | P0 | Перед деактивацией выберите, что делать с незавершенными задачами: снять исполнителя или переназначить. | planned |
| team.department.delete_blocked | `/team` | Удаление отдела | В отделе есть участники | moderator,admin | Validation | P0 | Отдел нельзя удалить, пока в нём есть участники. | planned |
| broadcasts.caption_limit_with_image | `/broadcasts` | Блок ввода сообщения | Выбрана картинка | moderator,admin | Validation | P0 | С изображением Telegram ограничивает подпись 1024 символами. | planned |
| broadcasts.failed_status_debug | `/broadcasts` | История рассылок | Статус рассылки `failed` | moderator,admin | State | P0 | Откройте ошибку и проверьте корректность цели/формат HTML/длину сообщения. | planned |
| broadcasts.schedule_timezone | `/broadcasts` | Блок планирования | Указание времени отправки | moderator,admin | Validation | P0 | Отправка планируется в МСК, проверьте дату и время перед подтверждением. | planned |
| broadcasts.no_targets_crosslink | `/broadcasts` | Блок выбора групп | Нет Telegram-групп | moderator,admin | Cross-link | P0 | Добавьте цели в `Settings -> Telegram-группы` (admin). | planned |

