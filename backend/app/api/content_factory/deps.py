"""FastAPI dependencies for Content Factory access control."""

from fastapi import Depends, HTTPException, status

from app.api.auth import get_current_user
from app.db.models import TeamMember
from app.services.permission_service import PermissionService


async def require_cf_access(
    member: TeamMember = Depends(get_current_user),
) -> TeamMember:
    """Require has_content_factory_access flag (or admin role)."""
    if not PermissionService.can_access_content_factory(member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к Content Factory",
        )
    return member


async def require_cf_admin(
    member: TeamMember = Depends(get_current_user),
) -> TeamMember:
    """Require admin role for reference-table edits."""
    if not PermissionService.can_edit_cf_reference_tables(member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор может редактировать справочники Content Factory",
        )
    return member
