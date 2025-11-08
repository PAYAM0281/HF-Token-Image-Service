import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.api import deps
from app.core.generation import engine
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class LoraRequest(BaseModel):
    lora_path: str


@router.get("/list", response_model=list[str])
async def get_loras(current_user: dict = Depends(deps.get_current_user)):
    """Returns a list of loaded LoRAs."""
    return engine.get_loaded_loras()


@router.post("/load", status_code=status.HTTP_202_ACCEPTED)
async def load_lora(
    request: LoraRequest, current_user: dict = Depends(deps.get_current_user)
):
    """Loads a LoRA into memory."""
    logger.info(
        f"Received request to load LoRA {request.lora_path} from user {current_user.get('name')}"
    )
    try:
        await engine.load_lora(request.lora_path)
        return {"message": f"LoRA {request.lora_path} loaded successfully."}
    except ValueError as e:
        logger.exception(e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to load LoRA {request.lora_path}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unload", status_code=status.HTTP_200_OK)
async def unload_lora(
    request: LoraRequest, current_user: dict = Depends(deps.get_current_user)
):
    """Unloads a LoRA from memory."""
    logger.info(
        f"Received request to unload LoRA {request.lora_path} from user {current_user.get('name')}"
    )
    try:
        await engine.unload_lora(request.lora_path)
        return {"message": f"LoRA {request.lora_path} unloaded successfully."}
    except ValueError as e:
        logger.exception(e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to unload LoRA {request.lora_path}")
        raise HTTPException(status_code=500, detail=str(e))