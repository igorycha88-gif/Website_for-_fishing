from app.endpoints.fish_types import router as fish_types_router
from app.endpoints.equipment_types import router as equipment_types_router
from app.endpoints.places import router as places_router
from app.endpoints.favorites import router as favorites_router

__all__ = [
    "fish_types_router",
    "equipment_types_router",
    "places_router",
    "favorites_router",
]
