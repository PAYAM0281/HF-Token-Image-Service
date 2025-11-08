import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.api import deps
from app.core.generation import engine
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class LoadModelRequest(BaseModel):
    model_id: str


@router.get("/", response_model=list[str])
async def get_models():
    """Returns a list of available models."""
    return list(engine.model_registry.keys())


@router.post("/load", status_code=status.HTTP_200_OK)
async def load_model(
    request: LoadModelRequest, current_user: dict = Depends(deps.get_current_user)
):
    """Loads a model into memory."""
    logger.info(
        f"Received request to load model {request.model_id} from user {current_user.get('name')}"
    )
    try:
        engine.load_model(request.model_id)
        return {"message": f"Model {request.model_id} loaded successfully."}
    except Exception as e:
        logger.exception(f"Failed to load model {request.model_id}")
        raise HTTPException(status_code=500, detail=str(e))