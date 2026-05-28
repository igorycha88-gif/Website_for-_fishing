from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserStatsResponse(BaseModel):
    total_users: int
    verified_users: int
    active_users: int
    admin_count: int
    moderator_count: int


class UserRoleEnum(str, Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class AdminUserListItem(BaseModel):
    id: str
    email: str
    username: str
    role: UserRoleEnum
    is_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    users: List[AdminUserListItem]
    total: int
    page: int
    page_size: int


class CheckAccessResponse(BaseModel):
    has_access: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
