from fastapi import FastAPI
from app.api.v1 import router as v1_router

app = FastAPI(
    title="Reports Service",
    description="User reports and reviews service",
    version="1.0.0"
)

app.include_router(v1_router)
