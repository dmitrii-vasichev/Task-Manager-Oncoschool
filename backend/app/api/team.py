import io
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import get_current_user, require_moderator
from app.db.database import get_session
from app.db.models import Department, TeamMember
from app.db.repositories import DepartmentRepository, TeamMemberRepository
from app.db.schemas import TeamMemberCreate, TeamMemberResponse, TeamMemberUpdate
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/team", tags=["team"])
member_repo = TeamMemberRepository()
dept_repo = DepartmentRepository()

AVATAR_DIR = Path(__file__).resolve().parents[2] / "static" / "avatars"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB


@router.get("/tree")
async def get_team_tree(
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get team organized by departments."""
    # Fetch departments with members eager-loaded
    stmt = (
        select(Department)
        .options(selectinload(Department.members))
        .where(Department.is_active.is_(True))
        .order_by(Department.sort_order, Department.name)
    )
    result = await session.execute(stmt)
    departments = list(result.scalars().all())

    # Fetch all active members
    all_members = await member_repo.get_all_active(session)
    assigned_ids = set()
    for dept in departments:
        for m in dept.members:
            if m.is_active:
                assigned_ids.add(m.id)

    unassigned = [m for m in all_members if m.id not in assigned_ids]

    def member_to_dict(m: TeamMember) -> dict:
        return {
            "id": str(m.id),
            "telegram_id": m.telegram_id,
            "telegram_username": m.telegram_username,
            "full_name": m.full_name,
            "name_variants": m.name_variants,
            "department_id": str(m.department_id) if m.department_id else None,
            "position": m.position,
            "email": m.email,
            "birthday": m.birthday.isoformat() if m.birthday else None,
            "avatar_url": m.avatar_url,
            "role": m.role,
            "is_active": m.is_active,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
        }

    def dept_to_dict(d: Department) -> dict:
        active_members = sorted(
            [m for m in d.members if m.is_active],
            key=lambda m: m.full_name,
        )
        return {
            "id": str(d.id),
            "name": d.name,
            "description": d.description,
            "head_id": str(d.head_id) if d.head_id else None,
            "color": d.color,
            "sort_order": d.sort_order,
            "is_active": d.is_active,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "members": [member_to_dict(m) for m in active_members],
        }

    return {
        "departments": [dept_to_dict(d) for d in departments],
        "unassigned": sorted(
            [member_to_dict(m) for m in unassigned],
            key=lambda m: m["full_name"],
        ),
    }


@router.get("", response_model=list[TeamMemberResponse])
async def list_team(
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all active team members."""
    members = await member_repo.get_all_active(session)
    return members


@router.post("", response_model=TeamMemberResponse, status_code=201)
async def create_team_member(
    data: TeamMemberCreate,
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Create a new team member. Admin can set any role, moderator — only moderator/member."""
    # Admin role can only be assigned by admin
    if data.role == "admin" and not PermissionService.is_admin(member):
        raise HTTPException(
            status_code=403,
            detail="Только администратор может создавать администраторов",
        )

    # Check telegram_id uniqueness if provided
    if data.telegram_id is not None:
        existing = await member_repo.get_by_telegram_id(session, data.telegram_id)
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Участник с таким Telegram ID уже существует",
            )

    create_data = data.model_dump(exclude_unset=True)
    new_member = await member_repo.create(session, **create_data)
    await session.commit()
    await session.refresh(new_member)
    return new_member


@router.get("/{member_id}", response_model=TeamMemberResponse)
async def get_team_member(
    member_id: uuid.UUID,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get team member details."""
    target = await member_repo.get_by_id(session, member_id)
    if not target:
        raise HTTPException(status_code=404, detail="Участник не найден")
    return target


@router.patch("/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: uuid.UUID,
    data: TeamMemberUpdate,
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Update team member. Moderator+ only."""
    target = await member_repo.get_by_id(session, member_id)
    if not target:
        raise HTTPException(status_code=404, detail="Участник не найден")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    # Role change requires admin
    if "role" in update_data and update_data["role"] != target.role:
        if not PermissionService.can_manage_roles(member):
            raise HTTPException(
                status_code=403,
                detail="Только администратор может менять роли",
            )

    updated = await member_repo.update(session, member_id, **update_data)
    await session.commit()
    return updated


@router.post("/{member_id}/avatar")
async def upload_avatar(
    member_id: uuid.UUID,
    file: UploadFile = File(...),
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Upload avatar for a team member. Moderator+ only."""
    target = await member_repo.get_by_id(session, member_id)
    if not target:
        raise HTTPException(status_code=404, detail="Участник не найден")

    # Validate content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Допустимые форматы: JPEG, PNG, WebP",
        )

    # Read and validate size
    contents = await file.read()
    if len(contents) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Максимальный размер файла: 2 МБ",
        )

    # Process with Pillow: resize to 256x256, convert to WebP
    img = Image.open(io.BytesIO(contents))
    img = img.convert("RGB")
    img.thumbnail((256, 256))

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    avatar_filename = f"{member_id}.webp"
    avatar_path = AVATAR_DIR / avatar_filename
    img.save(avatar_path, format="WEBP", quality=85)

    # Update member
    avatar_url = f"/static/avatars/{avatar_filename}"
    await member_repo.update(session, member_id, avatar_url=avatar_url)
    await session.commit()

    return {"avatar_url": avatar_url}


@router.delete("/{member_id}/avatar")
async def delete_avatar(
    member_id: uuid.UUID,
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Delete avatar for a team member. Moderator+ only."""
    target = await member_repo.get_by_id(session, member_id)
    if not target:
        raise HTTPException(status_code=404, detail="Участник не найден")

    # Delete file if exists
    avatar_path = AVATAR_DIR / f"{member_id}.webp"
    if avatar_path.exists():
        avatar_path.unlink()

    # Clear avatar_url
    await member_repo.update(session, member_id, avatar_url=None)
    await session.commit()

    return {"avatar_url": None}
