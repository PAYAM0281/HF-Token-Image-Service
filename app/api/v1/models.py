from pydantic import BaseModel, Field
from typing import Optional


class Txt2ImgRequest(BaseModel):
    prompt: str = Field(..., description="The main text prompt for image generation.")
    negative_prompt: Optional[str] = Field(
        None, description="Prompt describing what to avoid."
    )
    model_id: str = Field(
        "stabilityai/stable-diffusion-xl-base-1.0",
        description="The model to use for generation.",
    )
    num_inference_steps: int = Field(
        25, ge=1, le=100, description="Number of diffusion steps."
    )
    guidance_scale: float = Field(
        7.5, ge=1.0, le=20.0, description="Guidance scale for prompt adherence."
    )
    seed: int = Field(-1, description="Seed for reproducibility. -1 for random.")
    height: int = Field(1024, ge=512, le=1024, description="Image height in pixels.")
    width: int = Field(1024, ge=512, le=1024, description="Image width in pixels.")
    lora_path: Optional[str] = Field(None, description="Path to LoRA adapter.")
    lora_scale: Optional[float] = Field(
        0.8, ge=0.0, le=2.0, description="Scale for LoRA weights."
    )


class Img2ImgRequest(Txt2ImgRequest):
    image_b64: str = Field(..., description="Base64 encoded initial image.")
    strength: float = Field(
        0.8, ge=0.0, le=1.0, description="Strength of the initial image's influence."
    )


class GenerationResponse(BaseModel):
    image_b64: str
    seed: int
    model_id: str
    generation_time: float
    nsfw_content_detected: bool