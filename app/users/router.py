"""Users CRUD API — admin only."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit
from app.auth.dependencies import require_permission
from app.core.database import get_db
from app.models.user import UserRole
from app.rbac.service import get_effective_permissions
from app.repositories.permission_repo import PermissionRepository
from app.repositories.user_repo import UserRepository
from app.users.schemas import (
    PermissionOut, PermissionsSetRequest, UserCreate, UserOut, UserUpdate
)

router = APIRouter(prefix="/users", tags=["Users"])
_admin = require_permission("users.manage")


def _user_to_out(user) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
        permissions=sorted(get_effective_permissions(user)),
    )


@router.post("", response_model=UserOut, status_code=201, dependencies=[_admin])
async def create_user(
    body: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    if await repo.get_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    try:
        role = UserRole(body.role)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid role: {body.role}")

    user = await repo.create(email=body.email, password=body.password, role=role)
    await write_audit(
        db, action="users.create", entity_type="user", entity_id=user.id,
        meta={"email": user.email, "role": user.role.value},
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(user)
    return _user_to_out(user)


@router.get("", response_model=list[UserOut], dependencies=[_admin])
async def list_users(
    skip: int = 0, limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    users = await repo.list_all(skip=skip, limit=limit)
    return [_user_to_out(u) for u in users]


@router.get("/{user_id}", response_model=UserOut, dependencies=[_admin])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_out(user)


@router.patch("/{user_id}", response_model=UserOut, dependencies=[_admin])
async def update_user(
    user_id: int,
    body: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates: dict = {k: v for k, v in body.model_dump().items() if v is not None}
    if "role" in updates:
        try:
            updates["role"] = UserRole(updates["role"])
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid role: {updates['role']}")

    user = await repo.update(user, **updates)
    await write_audit(
        db, action="users.update", entity_type="user", entity_id=user.id,
        meta=updates if "password" not in updates else {**{k: v for k, v in updates.items() if k != "password"}, "password": "***"},
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    return _user_to_out(user)


@router.delete("/{user_id}", status_code=204, dependencies=[_admin])
async def deactivate_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await repo.update(user, is_active=False)
    await write_audit(
        db, action="users.deactivate", entity_type="user", entity_id=user_id,
        ip=request.client.host if request.client else None,
    )
    await db.commit()


@router.get("/{user_id}/permissions", response_model=list[PermissionOut], dependencies=[_admin])
async def get_user_permissions(user_id: int, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    if not await repo.get_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    perms = await repo.get_permissions(user_id)
    return [PermissionOut(id=p.id, code=p.code, description=p.description) for p in perms]


@router.put("/{user_id}/permissions", status_code=200, dependencies=[_admin])
async def set_user_permissions(
    user_id: int,
    body: PermissionsSetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    repo = UserRepository(db)
    if not await repo.get_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    perm_repo = PermissionRepository(db)
    perms = await perm_repo.get_by_codes(body.permission_codes)
    found_codes = {p.code for p in perms}
    missing = set(body.permission_codes) - found_codes
    if missing:
        raise HTTPException(status_code=422, detail=f"Unknown permission codes: {missing}")

    perm_ids = [p.id for p in perms]
    await repo.set_permissions(user_id, perm_ids)
    await write_audit(
        db, action="users.permissions_update", entity_type="user", entity_id=user_id,
        meta={"permissions": body.permission_codes},
        ip=request.client.host if request.client else None,
    )
    await db.commit()
    return {"user_id": user_id, "permissions": body.permission_codes}
