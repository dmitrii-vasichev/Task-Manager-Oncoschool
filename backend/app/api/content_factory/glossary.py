"""GET /api/content-factory/glossary."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.content_factory.deps import require_cf_access
from app.db.models import TeamMember
from app.services.content_factory.glossary import get_terms

router = APIRouter(tags=["content-factory"])


class GlossaryTermResponse(BaseModel):
    term: str
    definition: str
    display_order: int


@router.get("/glossary", response_model=list[GlossaryTermResponse])
async def get_glossary(
    member: TeamMember = Depends(require_cf_access),
) -> list[GlossaryTermResponse]:
    return [GlossaryTermResponse(**t) for t in get_terms()]
