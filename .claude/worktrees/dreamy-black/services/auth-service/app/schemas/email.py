from pydantic import BaseModel
from typing import Optional


class MessageResponse(BaseModel):
    message: str


class EmailVerificationResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
