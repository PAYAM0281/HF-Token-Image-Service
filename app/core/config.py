import os
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from typing import Union


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []
    LOG_LEVEL: str = "INFO"
    DEFAULT_MODEL_ID: str = "stabilityai/stable-diffusion-xl-base-1.0"
    HF_HOME: str = os.getenv("HF_HOME", "/root/.cache/huggingface")
    TORCH_HOME: str = os.getenv("TORCH_HOME", "/root/.cache/torch")
    MODEL_CACHE_DIR: str = os.getenv("MODEL_CACHE_DIR", "/models")
    LOG_DIR: str = os.getenv("LOG_DIR", "/logs")

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()