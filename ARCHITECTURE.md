# Image Generation API - Architecture Documentation

## System Overview

This service provides a production-ready REST API for AI-powered image generation using Stable Diffusion models. The architecture is designed for high-performance GPU inference with dynamic model loading, real-time progress streaming, and comprehensive observability.

## Core Design Decisions

### 1. FastAPI Framework

**Choice Justification:**
- **Async Support**: Native async/await for non-blocking I/O operations during GPU inference
- **Automatic OpenAPI**: Self-documenting API with interactive Swagger UI at `/docs`
- **WebSocket Support**: Built-in WebSocket handling for real-time progress streaming
- **Type Safety**: Pydantic integration for request/response validation
- **Performance**: One of the fastest Python web frameworks (Starlette-based)

**Alternative Considered:**
- Flask: Lacks native async support and WebSocket capabilities
- Django: Too heavyweight for API-only service

### 2. Diffusers Library for Image Generation

**Choice Justification:**
- **Hugging Face Ecosystem**: Native integration with HF Hub for model downloads
- **Pipeline Abstraction**: High-level APIs for txt2img and img2img workflows
- **Model Flexibility**: Support for multiple Stable Diffusion versions (1.5, 2.1, XL)
- **LoRA Support**: Built-in adapter loading via `load_lora_weights()`
- **Optimization**: Automatic GPU memory management and dtype conversion

**Architecture:**

GenerationEngine
├── txt2img_pipe: AutoPipelineForText2Image
├── img2img_pipe: AutoPipelineForImage2Image
├── model_registry: Dict[str, str]  # Friendly name -> HF repo ID
└── loaded_loras: Dict[str, str]    # Path -> LoRA identifier


### 3. Authentication via Hugging Face Tokens

**Implementation:**
- OAuth2 Bearer token scheme with HF Hub API validation
- Read-only scope enforcement via `whoami()` API call
- Token passed in `Authorization: Bearer <token>` header
- Dependency injection pattern for token validation in all protected endpoints

**Security:**
- Tokens never stored server-side
- Validation on every request (stateless authentication)
- HTTP 401 responses for invalid/expired tokens

### 4. Caching Strategy

**Model Weight Caching:**
- **Location**: Named Docker volume `/models` (persistent across restarts)
- **Mechanism**: Diffusers `cache_dir` parameter points to `/models`
- **Benefits**: Zero warm-start times after initial download
- **Size**: ~6-12GB per SDXL model, ~4-6GB per SD 1.5/2.1 model

**Hugging Face Hub Caching:**
- **Location**: Named Docker volume `/cache/huggingface`
- **Contains**: Model metadata, tokenizers, config files
- **Shared**: Between all pipelines and models

**PyTorch Caching:**
- **Location**: `/root/.cache/torch` (ephemeral, container-specific)
- **Contains**: Compiled kernels, autograd cache

### 5. GPU Memory Management

**Optimization Techniques:**
- **FP16 Precision**: All models loaded with `torch_dtype=torch.float16` (halves VRAM usage)
- **Pipeline Sharing**: img2img pipeline created from txt2img via `from_pipe()` (shares weights)
- **Lazy Loading**: Models loaded on-demand via `/v1/models/load` endpoint
- **VRAM Monitoring**: `torch.cuda.max_memory_allocated()` tracked per request

**Expected VRAM Usage:**
- SDXL Base: ~6-8GB
- SD 2.1: ~4-5GB
- SD 1.5: ~3-4GB

### 6. Logging Architecture

**Structured JSON Logging:**
- **Library**: `python-json-logger` for machine-readable logs
- **Fields**: `timestamp`, `level`, `name`, `message`, custom context
- **Destination**: stdout (captured by Docker logging driver)

**Generation Metadata Logging:**
on
{
  "timestamp": 1704067200.0,
  "level": "INFO",
  "name": "app.core.generation",
  "message": "Generation finished",
  "prompt": "A beautiful sunset...",
  "seed": 42,
  "model_id": "sd-xl-base",
  "latency_ms": 8543.2,
  "vram_peak_mb": 7234.5,
  "nsfw_detected": false
}


### 7. WebSocket Streaming Architecture

**Progress Callback System:**
- Diffusers pipeline accepts `callback_on_step_end` parameter
- Callback invoked after each denoising step
- Progress calculated as `(step + 1) / total_steps`
- Async callback sends JSON message via WebSocket

**Message Protocol:**
on
// Progress update
{"type": "progress", "progress": 0.45, "step": 12}

// Final result
{"type": "result", "data": {"image_b64": "...", "seed": 42, ...}}

// Error
{"type": "error", "message": "CUDA out of memory"}


### 8. LoRA Adapter System

**Implementation:**
- **Loading**: `pipeline.load_lora_weights(hf_path)` downloads and merges weights
- **Scaling**: `cross_attention_kwargs={"scale": 0.8}` controls adapter strength
- **Unloading**: `pipeline.unload_lora_weights()` removes adapter from memory
- **Caching**: Loaded LoRAs tracked in `GenerationEngine.loaded_loras` dict

**Endpoints:**
- `POST /v1/loras/load`: Pre-load LoRA for faster generation
- `POST /v1/loras/unload`: Remove LoRA from memory
- `GET /v1/loras/list`: Show currently loaded adapters

## Dependency Justification

### Core Dependencies

| Package | Version | Purpose | Alternatives Considered |
|---------|---------|---------|------------------------|
| `fastapi` | Latest | REST API framework | Flask (no async), Django (heavyweight) |
| `uvicorn` | Latest | ASGI server | Hypercorn (less mature) |
| `diffusers` | Latest | Stable Diffusion pipelines | Manual PyTorch impl (too complex) |
| `transformers` | Latest | Required by diffusers | N/A (dependency) |
| `torch` | Latest | GPU inference | TensorFlow (less SD support) |
| `huggingface-hub` | Latest | Model downloads + auth | Manual HTTP (reinventing wheel) |
| `pydantic` | Latest | Request validation | Marshmallow (less FastAPI integration) |
| `python-json-logger` | Latest | Structured logging | Manual JSON formatting |
| `pillow` | Latest | Image processing | OpenCV (overkill) |
| `accelerate` | Latest | Multi-GPU support (future) | N/A |
| `safetensors` | Latest | Secure model loading | pickle (security risk) |

### Optional Dependencies

| Package | Purpose |
|---------|---------|
| `reflex` | Web UI (bonus feature) |
| `httpx` | Testing async API calls |

## Performance Characteristics

**Target Hardware:** NVIDIA A10G (24GB VRAM)

| Operation | Target Latency | Notes |
|-----------|---------------|-------|
| Model Loading | <30s | First-time download |
| Model Switching | <5s | Cached weights |
| txt2img (25 steps) | <10s | SDXL, 1024x1024 |
| txt2img (25 steps) | <5s | SD 1.5, 512x512 |
| LoRA Loading | <3s | Cached weights |

## Deployment Architecture


┌─────────────────────────────────────────┐
│ Docker Container (nvidia runtime)       │
│                                         │
│  ┌────────────┐      ┌──────────────┐  │
│  │  FastAPI   │◄────►│ Generation   │  │
│  │  :8000     │      │ Engine       │  │
│  └────────────┘      └──────┬───────┘  │
│                             │          │
│                             ▼          │
│  ┌─────────────────────────────────┐  │
│  │  NVIDIA CUDA Runtime            │  │
│  │  - PyTorch 2.1                  │  │
│  │  - CUDA 12.1                    │  │
│  │  - cuDNN 8                      │  │
│  └─────────────────────────────────┘  │
│                                         │
│  Volumes:                              │
│  - /models (persistent)                │
│  - /cache/huggingface (persistent)     │
│  - /logs (persistent)                  │
└─────────────────────────────────────────┘


## Future Enhancements

1. **Multi-GPU Support**: Distribute inference across multiple GPUs using `accelerate`
2. **Request Queuing**: Redis-based job queue for handling burst traffic
3. **Output Caching**: Cache generated images keyed by (prompt, seed, params)
4. **Batch Generation**: Process multiple prompts in single inference pass
5. **ControlNet Support**: Add pose/depth conditioning endpoints
6. **Quantization**: INT8 quantization for 2x throughput improvement

## References

- [Diffusers Documentation](https://huggingface.co/docs/diffusers)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hugging Face Hub API](https://huggingface.co/docs/huggingface_hub)
- [Stable Diffusion Paper](https://arxiv.org/abs/2112.10752)
