# Multi-stage Dockerfile for Image Generation API
# Target: <4GB compressed image with CUDA support

FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime as builder

WORKDIR /tmp

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Runtime Stage
# ============================================
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY ./app /app/app
COPY ./assets /app/assets
COPY rxconfig.py /app/
COPY apt-packages.txt /app/

# Set Python path
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Configure cache directories
ENV HF_HOME=/cache/huggingface
ENV TORCH_HOME=/root/.cache/torch
ENV MODEL_CACHE_DIR=/models
ENV LOG_DIR=/logs

# Create necessary directories
RUN mkdir -p /cache/huggingface /models /logs

# Expose ports (FastAPI + Reflex)
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (runs both FastAPI and Reflex)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & reflex run --env prod"]
