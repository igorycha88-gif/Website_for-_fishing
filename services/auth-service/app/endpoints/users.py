from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.schemas.auth import UserResponse, UserUpdate, PasswordUpdate
from app.crud.user import UserCRUD

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    logger.debug("Get current user request")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        logger.warning("Get current user failed: invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token"},
        )

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Get current user failed: missing sub claim in token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token"},
        )

    user_crud = UserCRUD(db)
    user = await user_crud.get_by_id(user_id)

    if not user:
        logger.warning("Get current user failed: user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    logger.info("Get current user successful", user_id=user_id)
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    logger.debug("Update current user request")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        logger.warning("Update current user failed: invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token"},
        )

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Update current user failed: missing sub claim in token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token"},
        )

    user_crud = UserCRUD(db)
    user = await user_crud.get_by_id(user_id)

    if not user:
        logger.warning("Update current user failed: user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    update_data = user_update.model_dump(exclude_unset=True)

    logger.info(
        "Updating user profile",
        user_id=user_id,
        fields=list(update_data.keys()),
    )

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    logger.info("User profile updated successfully", user_id=user_id)
    return UserResponse.model_validate(user)


@router.patch("/me/password")
async def change_password(
    password_update: PasswordUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import verify_password, get_password_hash

    logger.debug("Change password request")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        logger.warning("Change password failed: invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token"},
        )

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Change password failed: missing sub claim in token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token"},
        )

    user_crud = UserCRUD(db)
    user = await user_crud.get_by_id(user_id)

    if not user:
        logger.warning("Change password failed: user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    if not verify_password(password_update.current_password, str(user.password_hash)):
        logger.warning("Change password failed: incorrect current password", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PASSWORD", "message": "Incorrect current password"},
        )

    user.password_hash = get_password_hash(password_update.new_password)
    await db.commit()

    logger.info("Password changed successfully", user_id=user_id)
    return {"message": "Password updated successfully"}
