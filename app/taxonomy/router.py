"""Skill taxonomy API — read for hr+admin, write for admin only."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit
from app.auth.dependencies import CurrentUser, require_permission
from app.core.database import get_db
from app.repositories.taxonomy_repo import TaxonomyRepository
from app.taxonomy.schemas import SkillCreate, SkillOut, SkillUpdate

router = APIRouter(prefix="/taxonomy/skills", tags=["Taxonomy"])
_read = require_permission("taxonomy.read")
_manage = require_permission("taxonomy.manage")


@router.get("", response_model=list[SkillOut], dependencies=[_read])
async def list_skills(
    q: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    return await TaxonomyRepository(db).list(q=q, category=category, is_active=is_active, skip=skip, limit=limit)


@router.get("/{skill_id}", response_model=SkillOut, dependencies=[_read])
async def get_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    skill = await TaxonomyRepository(db).get_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("", response_model=SkillOut, status_code=201, dependencies=[_manage])
async def create_skill(
    body: SkillCreate,
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    repo = TaxonomyRepository(db)
    if await repo.get_by_name(body.name):
        raise HTTPException(status_code=409, detail="Skill name already exists")

    skill = await repo.create(
        name=body.name, category=body.category,
        aliases=body.aliases, created_by_id=current_user.id,
    )
    await write_audit(
        db, action="taxonomy.create", entity_type="skill_taxonomy", entity_id=skill.id,
        meta={"name": skill.name}, actor_user_id=current_user.id,
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(skill)
    return skill


@router.patch("/{skill_id}", response_model=SkillOut, dependencies=[_manage])
async def update_skill(
    skill_id: int,
    body: SkillUpdate,
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    repo = TaxonomyRepository(db)
    skill = await repo.get_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    skill = await repo.update(skill, updated_by_id=current_user.id, **updates)
    await write_audit(
        db, action="taxonomy.update", entity_type="skill_taxonomy", entity_id=skill_id,
        meta=updates, actor_user_id=current_user.id,
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    return skill


@router.delete("/{skill_id}", status_code=204, dependencies=[_manage])
async def delete_skill(
    skill_id: int,
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    repo = TaxonomyRepository(db)
    skill = await repo.get_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    await repo.update(skill, updated_by_id=current_user.id, is_active=False)
    await write_audit(
        db, action="taxonomy.delete", entity_type="skill_taxonomy", entity_id=skill_id,
        actor_user_id=current_user.id,
        ip=request.client.host if request.client else None,
    )
    await db.commit()
