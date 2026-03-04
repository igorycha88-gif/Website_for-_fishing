from fastapi import APIRouter
from app.endpoints import regions_router, weather_router
from app.endpoints.forecast import router as forecast_router
from app.endpoints.custom_fish import router as custom_fish_router

router = APIRouter()
router.include_router(regions_router)
router.include_router(weather_router)
router.include_router(forecast_router)
router.include_router(custom_fish_router)
