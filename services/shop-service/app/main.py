from fastapi import FastAPI
from app.api.v1 import router as v1_router

app = FastAPI(
    title="Shop Service",
    description="Online shop for fishing equipment",
    version="1.0.0",
)

app.include_router(v1_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "shop-service", "version": "1.0.0"}
