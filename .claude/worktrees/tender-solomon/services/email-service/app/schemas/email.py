from pydantic import BaseModel, EmailStr
from typing import Literal


class EmailSendRequest(BaseModel):
    to_email: EmailStr
    verification_code: str
    username: str


class EmailSendResponse(BaseModel):
    success: bool
    message: str


class GenerateCodeResponse(BaseModel):
    code: str


class ErrorResponse(BaseModel):
    error: dict
