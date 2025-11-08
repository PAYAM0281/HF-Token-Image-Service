from fastapi import APIRouter
from app.api.v1.endpoints import generation, streaming, models, loras

api_router = APIRouter()
api_router.include_router(generation.router, prefix="/generate", tags=["generation"])
api_router.include_router(streaming.router, prefix="/stream", tags=["streaming"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(loras.router, prefix="/loras", tags=["loras"])