from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.db.models import TeamMember
from app.services.permission_service import PermissionService


class IsModeratorFilter(BaseFilter):
    """Фильтр: пропускает admin и moderator."""

    async def __call__(self, message: Message, member: TeamMember) -> bool:
        return PermissionService.is_moderator(member)


class IsAdminFilter(BaseFilter):
    """Фильтр: пропускает только admin."""

    async def __call__(self, message: Message, member: TeamMember) -> bool:
        return PermissionService.is_admin(member)
