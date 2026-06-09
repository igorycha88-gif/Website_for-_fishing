from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.admin import (
    UserStatsResponse,
    AdminUserListResponse,
    AdminUserListItem,
    CheckAccessResponse
)

router = APIRouter()


@router.get("/check-access", response_model=CheckAccessResponse)
async def check_admin_access(current_user: dict = Depends(get_current_user)):
    has_access = current_user["role"] == "admin"
    return CheckAccessResponse(
        has_access=has_access,
        user_id=current_user.get("user_id") if has_access else None,
        email=current_user.get("email") if has_access else None,
        role=current_user.get("role") if has_access else None
    )


@router.get("/dashboard/stats", response_model=UserStatsResponse)
async def get_dashboard_stats(
    admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    verified_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_verified == True)
    )
    verified_users = verified_users_result.scalar() or 0

    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar() or 0

    admin_count_result = await db.execute(
        select(func.count(User.id)).where(User.role == "admin")
    )
    admin_count = admin_count_result.scalar() or 0

    moderator_count_result = await db.execute(
        select(func.count(User.id)).where(User.role == "moderator")
    )
    moderator_count = moderator_count_result.scalar() or 0

    return UserStatsResponse(
        total_users=total_users,
        verified_users=verified_users,
        active_users=active_users,
        admin_count=admin_count,
        moderator_count=moderator_count
    )


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None, description="Filter by role: user, moderator, admin"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by email or username"),
    admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).order_by(User.created_at.desc())

    if role:
        query = query.where(User.role == role)

    if is_verified is not None:
        query = query.where(User.is_verified == is_verified)

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_pattern)) | (User.username.ilike(search_pattern))
        )

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    user_items = [
        AdminUserListItem(
            id=str(user.id),
            email=user.email,
            username=user.username,
            role=user.role,
            is_verified=user.is_verified,
            is_active=user.is_active,
            created_at=user.created_at
        )
        for user in users
    ]

    return AdminUserListResponse(
        users=user_items,
        total=total,
        page=page,
        page_size=page_size
    )
