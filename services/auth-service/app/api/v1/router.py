from fastapi import APIRouter
from app.endpoints import auth, users, maps

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(maps.router, prefix="/maps", tags=["maps"])
