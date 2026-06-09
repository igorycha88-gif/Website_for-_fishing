from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.security import get_password_hash, create_access_token, decode_access_token
from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import RegisterRequest, VerifyEmailRequest, UserResponse, LoginRequest
from app.schemas.email import EmailVerificationResponse, MessageResponse
from app.crud.user import UserCRUD
from app.core.security import verify_password
from app.crud.email_verification_code import EmailVerificationCodeCRUD

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=MessageResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user_crud = UserCRUD(db)
    
    existing_email = await user_crud.get_by_email(request.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMAIL_ALREADY_EXISTS",
                "message": "Email already registered",
                "details": {"email": request.email}
            }
        )
    
    existing_username = await user_crud.get_by_username(request.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "USERNAME_ALREADY_EXISTS",
                "message": "Username already taken",
                "details": {"username": request.username}
            }
        )
    
    password_hash = get_password_hash(request.password)
    user = await user_crud.create(
        email=request.email,
        username=request.username,
        password_hash=password_hash
    )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.EMAIL_SERVICE_URL}/api/v1/email/generate-code",
                timeout=10.0
            )
            code = response.json()["code"]
            
            await client.post(
                f"{settings.EMAIL_SERVICE_URL}/api/v1/email/send",
                json={
                    "to_email": request.email,
                    "verification_code": code,
                    "username": request.username
                },
                timeout=30.0
            )
        
        email_crud = EmailVerificationCodeCRUD(db)
        await email_crud.create(request.email, code, 15)
        
        return MessageResponse(message="Registration successful. Please check your email for verification code.")
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "EMAIL_SEND_FAILED",
                "message": "Failed to send verification email",
                "details": {"error": str(e)}
            }
        )


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(request: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    email_crud = EmailVerificationCodeCRUD(db)
    user_crud = UserCRUD(db)
    
    verification_code = await email_crud.get_valid_code(request.email, request.code)
    
    if not verification_code:
        existing_code = await email_crud.get_by_email(request.email)
        await email_crud.increment_attempts(request.email)
        attempts = existing_code.attempts + 1 if existing_code else 3
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_OR_EXPIRED_CODE",
                "message": "Invalid or expired verification code",
                "details": {"remaining_attempts": max(0, 3 - attempts)}
            }
        )
    
    user = await user_crud.verify_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "User not found",
                "details": {"email": request.email}
            }
        )
    
    await email_crud.delete_by_email(request.email)
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return EmailVerificationResponse(
        success=True,
        message="Email verified successfully",
        access_token=access_token
    )


@router.post("/login", response_model=EmailVerificationResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user_crud = UserCRUD(db)
    
    user = await user_crud.get_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password"
            }
        )
    
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password"
            }
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Please verify your email first"
            }
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return EmailVerificationResponse(
        success=True,
        message="Login successful",
        access_token=access_token
    )


@router.get("/users/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_crud = UserCRUD(db)
    user = await user_crud.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        is_verified=user.is_verified
    )
