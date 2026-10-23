# Production Multi-Stage Dockerfile for SevaDristi Backend
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools and C compiler for dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final minimal production runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime dependencies including OpenCV headless libs, Tesseract with Telugu & Hindi language packs, and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-tel \
    tesseract-ocr-hin \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Create non-root user for principle of least privilege
RUN useradd -u 10001 -m -s /bin/bash appuser

# Copy application files
COPY backend /app/backend

# Set proper permissions
RUN chown -R appuser:appuser /app

USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    DEMO_MODE=false \
    LOG_LEVEL=INFO

EXPOSE 8000

# Container Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production server command with Gunicorn Uvicorn workers
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "backend.main:app"]
