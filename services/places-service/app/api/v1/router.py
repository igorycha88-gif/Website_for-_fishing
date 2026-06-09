from fastapi import APIRouter
from app.endpoints import fish_types, equipment_types, places, favorites

router = APIRouter()

router.include_router(fish_types.router)
router.include_router(equipment_types.router)
router.include_router(places.router)
router.include_router(favorites.router)
