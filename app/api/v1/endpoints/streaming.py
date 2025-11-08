import asyncio
import json
import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.api import deps
from app.api.v1.models import Txt2ImgRequest, Img2ImgRequest
from app.core.generation import engine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/generate/txt2img")
async def stream_txt2img(websocket: WebSocket, token: str | None = None):
    await websocket.accept(subprotocols=["access_token", token or ""])
    try:
        user = await deps.get_current_user(token)
        logger.info(f"WebSocket connection established for user {user.get('name')}")
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)
            request = Txt2ImgRequest(**request_data)
            logger.info(f"Starting txt2img generation for {user.get('name')}")

            async def progress_callback(step: int, timestep: float, latents):
                progress = (step + 1) / request.num_inference_steps
                await websocket.send_json(
                    {"type": "progress", "progress": progress, "step": step + 1}
                )

            try:
                response = await engine.generate_txt2img(
                    request, callback=progress_callback
                )
                await websocket.send_json({"type": "result", "data": response.dict()})
                logger.info(f"Finished txt2img generation for {user.get('name')}")
            except Exception as e:
                logger.exception("Error during streaming generation")
                await websocket.send_json({"type": "error", "message": str(e)})
    except WebSocketDisconnect as e:
        logger.exception(f"WebSocket disconnected: {e}")
    except Exception as e:
        logger.exception("WebSocket error")
        if not websocket.client_state.value == 3:
            await websocket.close(code=1011, reason=str(e))