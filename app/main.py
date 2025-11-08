from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()
app = FastAPI(
    title="Image Generation REST API Service",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.API_V1_STR)