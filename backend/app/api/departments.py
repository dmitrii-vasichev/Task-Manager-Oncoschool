import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, require_moderator
from app.db.database import get_session
from app.db.models import TeamMember
from app.db.repositories import DepartmentRepository
from app.db.schemas import DepartmentCreate, DepartmentResponse, DepartmentUpdate

router = APIRouter(prefix="/departments", tags=["departments"])
dept_repo = DepartmentRepository()


@router.get("", response_model=list[DepartmentResponse])
async def list_departments(
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all active departments."""
    departments = await dept_repo.get_all(session)
    return departments


@router.get("/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    dept_id: uuid.UUID,
    member: TeamMember = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get department by ID."""
    dept = await dept_repo.get_by_id(session, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Отдел не найден")
    return dept


@router.post("", response_model=DepartmentResponse, status_code=201)
async def create_department(
    data: DepartmentCreate,
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Create a new department. Moderator+ only."""
    dept = await dept_repo.create(
        session,
        name=data.name,
        description=data.description,
        head_id=data.head_id,
        color=data.color,
        sort_order=data.sort_order,
    )
    await session.commit()
    return dept


@router.patch("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: uuid.UUID,
    data: DepartmentUpdate,
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Update department. Moderator+ only."""
    dept = await dept_repo.get_by_id(session, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Отдел не найден")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    updated = await dept_repo.update(session, dept_id, **update_data)
    await session.commit()
    return updated


@router.delete("/{dept_id}", status_code=204)
async def delete_department(
    dept_id: uuid.UUID,
    member: TeamMember = Depends(require_moderator),
    session: AsyncSession = Depends(get_session),
):
    """Delete department. Moderator+ only. Fails if department has members."""
    dept = await dept_repo.get_by_id(session, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Отдел не найден")

    # Check if department has members
    stmt = select(func.count()).select_from(TeamMember).where(
        TeamMember.department_id == dept_id
    )
    result = await session.execute(stmt)
    count = result.scalar_one()
    if count > 0:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить отдел с участниками. Сначала переместите их в другой отдел",
        )

    await dept_repo.delete(session, dept_id)
    await session.commit()
