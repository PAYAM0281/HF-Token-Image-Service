import base64
import io
import logging
import time
from typing import Optional, TypedDict, Callable, Any
import torch
from diffusers import AutoPipelineForImage2Image, AutoPipelineForText2Image
from PIL import Image
from app.api.v1.models import GenerationResponse, Img2ImgRequest, Txt2ImgRequest
from app.core.config import settings
import asyncio

logger = logging.getLogger(__name__)


class PipelineResult(TypedDict):
    image_b64: str
    generation_time: float
    nsfw_content_detected: bool


class GenerationEngine:
    def __init__(self):
        self.txt2img_pipe = None
        self.img2img_pipe = None
        self.current_model_id: Optional[str] = None
        self.model_registry = {
            "sd-xl-base": "stabilityai/stable-diffusion-xl-base-1.0",
            "sd-2-1": "stabilityai/stable-diffusion-2-1",
            "sd-1-5": "runwayml/stable-diffusion-v1-5",
        }
        self.loaded_loras: dict[str, str] = {}

    def load_model(self, model_id: str):
        resolved_model_id = self.model_registry.get(model_id, model_id)
        if (
            resolved_model_id == self.current_model_id
            and self.txt2img_pipe
            and self.img2img_pipe
        ):
            logger.info(f"Model {resolved_model_id} is already loaded.")
            return
        logger.info(f"Loading model: {resolved_model_id}")
        self.txt2img_pipe = AutoPipelineForText2Image.from_pretrained(
            resolved_model_id,
            torch_dtype=torch.float16,
            variant="fp16",
            cache_dir=settings.MODEL_CACHE_DIR,
        ).to("cuda")
        self.img2img_pipe = AutoPipelineForImage2Image.from_pipe(self.txt2img_pipe).to(
            "cuda"
        )
        self.current_model_id = resolved_model_id
        self.loaded_loras = {}
        logger.info(f"Model {resolved_model_id} loaded successfully.")

    async def load_lora(self, lora_path: str):
        if not self.txt2img_pipe:
            raise RuntimeError("Cannot load LoRA: no base model is loaded.")
        logger.info(f"Loading LoRA: {lora_path}")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self.txt2img_pipe.load_lora_weights(lora_path)
        )
        self.loaded_loras[lora_path] = lora_path
        logger.info(f"LoRA {lora_path} loaded successfully.")

    def unload_lora(self, lora_path: str):
        if not self.txt2img_pipe:
            raise RuntimeError("Cannot unload LoRA: no base model is loaded.")
        if lora_path not in self.loaded_loras:
            raise ValueError(f"LoRA {lora_path} is not currently loaded.")
        logger.info(f"Unloading LoRA: {lora_path}")
        self.txt2img_pipe.unload_lora_weights()
        del self.loaded_loras[lora_path]
        if self.loaded_loras:
            for path in self.loaded_loras:
                self.txt2img_pipe.load_lora_weights(path)
        logger.info(f"LoRA {lora_path} unloaded successfully.")

    def get_loaded_loras(self) -> list[str]:
        return list(self.loaded_loras.keys())

    def _get_generator(self, seed: int) -> torch.Generator:
        if seed == -1:
            seed = torch.randint(0, 2**32 - 1, (1,)).item()
        return torch.Generator(device="cuda").manual_seed(seed)

    async def _run_pipeline(
        self, pipeline, callback: Callable | None = None, **kwargs
    ) -> PipelineResult:
        prompt = kwargs.get("prompt", "")
        lora_scale = kwargs.pop("lora_scale", None)
        start_time = time.time()
        torch.cuda.reset_peak_memory_stats()
        try:
            pipeline_kwargs = kwargs.copy()
            if lora_scale is not None:
                pipeline_kwargs["cross_attention_kwargs"] = {"scale": lora_scale}
            if callback:

                async def callback_wrapper(step, timestep, latents):
                    await callback(step, timestep, latents)

                pipeline_kwargs["callback_on_step_end"] = callback_wrapper
                pipeline_kwargs["callback_on_step_end_tensor_inputs"] = ["latents"]
            logger.info(f'Starting generation for prompt: "{prompt[:80]}..."')
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: pipeline(**pipeline_kwargs).images[0]
            )
            generation_time = time.time() - start_time
            vram_peak = torch.cuda.max_memory_allocated() / 1024**2
            logger.info(
                f"Generation finished in {generation_time:.2f}s. Peak VRAM used: {vram_peak:.2f} MB."
            )
            nsfw_content_detected = False
            buffered = io.BytesIO()
            result.save(buffered, format="PNG")
            image_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return {
                "image_b64": image_b64,
                "generation_time": generation_time,
                "nsfw_content_detected": nsfw_content_detected,
            }
        except Exception as e:
            logger.exception("Error during pipeline execution")
            raise e

    async def generate_txt2img(
        self, request: Txt2ImgRequest, callback: Callable | None = None
    ) -> GenerationResponse:
        self.load_model(request.model_id)
        if request.lora_path and request.lora_path not in self.loaded_loras:
            await self.load_lora(request.lora_path)
        generator = self._get_generator(request.seed)
        actual_seed = generator.seed()
        pipeline_args = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "num_inference_steps": request.num_inference_steps,
            "guidance_scale": request.guidance_scale,
            "width": request.width,
            "height": request.height,
            "generator": generator,
            "lora_scale": request.lora_scale,
        }
        if self.txt2img_pipe is not None:
            result = await self._run_pipeline(
                self.txt2img_pipe, callback, **pipeline_args
            )
            return GenerationResponse(
                image_b64=result["image_b64"],
                seed=actual_seed,
                model_id=request.model_id,
                generation_time=result["generation_time"],
                nsfw_content_detected=result["nsfw_content_detected"],
            )
        else:
            raise RuntimeError("Text-to-Image pipeline not initialized")

    async def generate_img2img(
        self, request: Img2ImgRequest, callback: Callable | None = None
    ) -> GenerationResponse:
        self.load_model(request.model_id)
        if request.lora_path and request.lora_path not in self.loaded_loras:
            await self.load_lora(request.lora_path)
        init_image_bytes = base64.b64decode(request.image_b64)
        init_image = Image.open(io.BytesIO(init_image_bytes)).convert("RGB")
        generator = self._get_generator(request.seed)
        actual_seed = generator.seed()
        pipeline_args = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "image": init_image,
            "strength": request.strength,
            "num_inference_steps": request.num_inference_steps,
            "guidance_scale": request.guidance_scale,
            "generator": generator,
            "lora_scale": request.lora_scale,
        }
        if self.img2img_pipe is not None:
            result = await self._run_pipeline(
                self.img2img_pipe, callback, **pipeline_args
            )
            return GenerationResponse(
                image_b64=result["image_b64"],
                seed=actual_seed,
                model_id=request.model_id,
                generation_time=result["generation_time"],
                nsfw_content_detected=result["nsfw_content_detected"],
            )
        else:
            raise RuntimeError("Image-to-Image pipeline not initialized")


engine = GenerationEngine()
engine.load_model(settings.DEFAULT_MODEL_ID)