from pydantic import BaseModel
from typing import Optional


class MessageResponse(BaseModel):
    message: str


class EmailVerificationResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 1800


class LogoutResponse(BaseModel):
    message: str = "Successfully logged out"
