from fastapi import APIRouter

from app.api.v1.endpoints import depth, tiles

router = APIRouter()
router.include_router(depth.router)
router.include_router(tiles.router)
