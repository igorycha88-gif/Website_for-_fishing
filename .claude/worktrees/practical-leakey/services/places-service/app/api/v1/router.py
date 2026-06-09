from fastapi import APIRouter
from app.api.v1.endpoints import places

router = APIRouter()

router.include_router(places.router, tags=["places"])

@router.get("/")
async def root():
    return {"service": "places", "status": "ok"}
