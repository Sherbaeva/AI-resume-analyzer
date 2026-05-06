"""Skill taxonomy repository."""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_taxonomy import SkillTaxonomy


class TaxonomyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self,
        q: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SkillTaxonomy]:
        stmt = select(SkillTaxonomy)
        if q:
            stmt = stmt.where(SkillTaxonomy.name.ilike(f"%{q}%"))
        if category:
            stmt = stmt.where(SkillTaxonomy.category == category)
        if is_active is not None:
            stmt = stmt.where(SkillTaxonomy.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit).order_by(SkillTaxonomy.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, skill_id: int) -> Optional[SkillTaxonomy]:
        result = await self.db.execute(
            select(SkillTaxonomy).where(SkillTaxonomy.id == skill_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[SkillTaxonomy]:
        result = await self.db.execute(
            select(SkillTaxonomy).where(SkillTaxonomy.name == name)
        )
        return result.scalar_one_or_none()

    async def create(
        self, name: str, category: Optional[str], aliases: list,
        created_by_id: Optional[int] = None,
    ) -> SkillTaxonomy:
        skill = SkillTaxonomy(
            name=name, category=category, aliases=aliases,
            created_by_id=created_by_id, updated_by_id=created_by_id,
        )
        self.db.add(skill)
        await self.db.flush()
        await self.db.refresh(skill)
        return skill

    async def update(self, skill: SkillTaxonomy, updated_by_id: int, **kwargs) -> SkillTaxonomy:
        for k, v in kwargs.items():
            setattr(skill, k, v)
        skill.updated_by_id = updated_by_id
        await self.db.flush()
        await self.db.refresh(skill)
        return skill
