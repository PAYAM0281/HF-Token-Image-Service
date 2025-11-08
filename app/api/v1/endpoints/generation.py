import logging
from fastapi import APIRouter, Depends, HTTPException
from app.api import deps
from app.api.v1 import models
from app.core.generation import engine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/txt2img", response_model=models.GenerationResponse)
async def txt2img(
    request: models.Txt2ImgRequest, current_user: dict = Depends(deps.get_current_user)
):
    """Handles Text-to-Image generation."""
    logger.info(
        f"Received txt2img request for model {request.model_id} from user {current_user.get('name')}"
    )
    try:
        response = await engine.generate_txt2img(request)
        return response
    except Exception as e:
        logger.exception("Failed to generate image")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/img2img", response_model=models.GenerationResponse)
async def img2img(
    request: models.Img2ImgRequest, current_user: dict = Depends(deps.get_current_user)
):
    """Handles Image-to-Image generation."""
    logger.info(
        f"Received img2img request for model {request.model_id} from user {current_user.get('name')}"
    )
    try:
        response = await engine.generate_img2img(request)
        return response
    except Exception as e:
        logger.exception("Failed to generate image")
        raise HTTPException(status_code=500, detail=str(e))