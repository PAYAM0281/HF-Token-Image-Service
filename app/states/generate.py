import reflex as rx
import asyncio
import json
import httpx
import logging

logger = logging.getLogger(__name__)


class ImageGenState(rx.State):
    prompt: str = "A beautiful sunset over a mountain range"
    negative_prompt: str = "blurry, low quality, unrealistic"
    model_id: str = "sd-xl-base"
    num_inference_steps: int = 25
    guidance_scale: float = 7.5
    seed: int = -1
    height: int = 1024
    width: int = 1024
    strength: float = 0.8
    lora_path: str = ""
    lora_scale: float = 0.8

    @rx.event
    def set_num_inference_steps(self, value: str):
        self.num_inference_steps = int(value)

    @rx.event
    def set_guidance_scale(self, value: str):
        self.guidance_scale = float(value)

    @rx.event
    def set_width(self, value: str):
        self.width = int(value) if int(value) % 8 == 0 else int(value) // 8 * 8

    @rx.event
    def set_height(self, value: str):
        self.height = int(value) if int(value) % 8 == 0 else int(value) // 8 * 8

    @rx.event
    def set_lora_scale(self, value: str):
        self.lora_scale = float(value)

    is_generating: bool = False
    progress: float = 0.0
    generated_image: str = "/placeholder.svg"
    available_models: list[str] = ["sd-xl-base", "sd-2-1", "sd-1-5"]
    available_loras: list[str] = [""]

    @rx.event
    async def get_available_loras(self):
        self.available_loras = [
            "",
            "latent-consistency/lcm-lora-sdxl",
            "ostris/ikea-instructions-style-lora-sdxl",
            "nerijs/pixel-art-xl",
        ]

    @rx.var
    def progress_percent_str(self) -> str:
        return f"{self.progress * 100:.0f}%"

    @rx.event
    async def start_generation(self):
        from app.states.token import HuggingFaceTokenState

        token_state = await self.get_state(HuggingFaceTokenState)
        params = {
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "model_id": self.model_id,
            "num_inference_steps": self.num_inference_steps,
            "guidance_scale": self.guidance_scale,
            "seed": self.seed,
            "height": self.height,
            "width": self.width,
            "token": token_state.token,
            "lora_path": self.lora_path,
            "lora_scale": self.lora_scale,
        }
        return rx.call_script(f"startGeneration({json.dumps(params)})")

    @rx.event
    def on_generation_start(self, data: dict):
        self.is_generating = True
        self.progress = 0
        self.generated_image = "/placeholder.svg"

    @rx.event
    def on_generation_progress(self, data: dict):
        self.progress = data.get("progress", self.progress)

    @rx.event
    def on_generation_result(self, data: dict):
        self.generated_image = f"data:image/png;base64,{data['data']['image_b64']}"
        self.is_generating = False

    @rx.event
    def on_generation_error(self, data: dict):
        logger.error(f"Generation failed: {data}")
        self.is_generating = False