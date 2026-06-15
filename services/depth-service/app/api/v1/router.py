from fastapi import APIRouter

from app.api.v1.endpoints import depth, tiles, areas, labels

router = APIRouter()
router.include_router(depth.router)
router.include_router(tiles.router)
router.include_router(areas.router)
router.include_router(labels.router)
