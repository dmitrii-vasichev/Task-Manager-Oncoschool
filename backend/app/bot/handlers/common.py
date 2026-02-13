from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models import TeamMember
from app.db.repositories import TeamMemberRepository
from app.services.permission_service import PermissionService

router = Router()

VALID_ROLES = ("admin", "moderator", "member")


@router.message(Command("start"))
async def cmd_start(message: Message, member: TeamMember) -> None:
    if PermissionService.is_admin(member):
        role_emoji, role_text = "\U0001f451", "Администратор"
    elif PermissionService.is_moderator(member):
        role_emoji, role_text = "\U0001f6e1\ufe0f", "Модератор"
    else:
        role_emoji, role_text = "\U0001f464", "Участник"

    await message.answer(
        f"Привет, {member.full_name}! Я бот-задачник Онкошколы.\n"
        f"Твоя роль: {role_emoji} {role_text}\n\n"
        f"/help — список команд"
    )


@router.message(Command("help"))
async def cmd_help(message: Message, member: TeamMember) -> None:
    is_mod = PermissionService.is_moderator(member)
    is_adm = PermissionService.is_admin(member)

    common_commands = (
        "<b>Команды:</b>\n\n"
        "/tasks — мои задачи\n"
        "/all — все задачи команды\n"
        "/new &lt;текст&gt; — создать задачу себе\n"
        "/done &lt;id&gt; — завершить задачу\n"
        "/update &lt;id&gt; &lt;текст&gt; — промежуточный апдейт\n"
        "/status &lt;id&gt; &lt;статус&gt; — изменить статус\n"
        "\U0001f3a4 Голосовое сообщение — создать задачу голосом\n"
        "/nextmeeting — следующая встреча\n"
        "/myreminder — мои настройки напоминаний"
    )

    text = common_commands

    if is_mod:
        mod_commands = (
            "\n\n<b>\U0001f6e1\ufe0f Модератор:</b>\n\n"
            "/assign @username &lt;текст&gt; — назначить задачу\n"
            "/meetings — предстоящие и прошедшие встречи\n"
            "/team — управление командой\n"
            "/subscribe — подписки на уведомления\n"
            "/stats — статистика"
        )
        text += mod_commands

    if is_adm:
        admin_commands = (
            "\n\n<b>\U0001f451 Администрирование:</b>\n\n"
            "/setrole @username admin|moderator|member — изменить роль\n"
            "/aimodel — текущая AI-модель\n"
            "/reminders — настройки напоминаний\n"
            "\u2699\ufe0f Настройки AI, напоминания — через веб-интерфейс"
        )
        text += admin_commands

    await message.answer(text, parse_mode="HTML")


@router.message(Command("setrole"))
async def cmd_setrole(
    message: Message,
    member: TeamMember,
    session_maker: async_sessionmaker,
) -> None:
    if not PermissionService.is_admin(member):
        await message.answer("\u26d4 Только администратор может менять роли.")
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "\u2753 Использование: /setrole @username роль\n"
            "Роли: admin, moderator, member"
        )
        return

    username = args[1].lstrip("@")
    new_role = args[2].lower().strip()

    if new_role not in VALID_ROLES:
        await message.answer(
            f"\u274c Неверная роль: <code>{new_role}</code>\n"
            f"Допустимые: admin, moderator, member",
            parse_mode="HTML",
        )
        return

    member_repo = TeamMemberRepository()
    async with session_maker() as session:
        async with session.begin():
            target = await member_repo.get_by_telegram_username(session, username)
            if not target:
                await message.answer(f"\u274c Участник @{username} не найден.")
                return

            if target.role == new_role:
                await message.answer(
                    f"Роль @{username} уже <b>{new_role}</b>.",
                    parse_mode="HTML",
                )
                return

            old_role = target.role
            target.role = new_role

    role_labels = {"admin": "\U0001f451 Администратор", "moderator": "\U0001f6e1\ufe0f Модератор", "member": "\U0001f464 Участник"}
    await message.answer(
        f"\u2705 Роль @{username} изменена:\n"
        f"{role_labels.get(old_role, old_role)} → {role_labels.get(new_role, new_role)}",
    )
