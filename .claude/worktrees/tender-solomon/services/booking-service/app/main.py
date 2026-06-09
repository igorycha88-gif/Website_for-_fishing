from fastapi import FastAPI
from app.api.v1 import router as v1_router

app = FastAPI(
    title="Booking Service",
    description="Booking service for fishing places",
    version="1.0.0"
)

app.include_router(v1_router)
