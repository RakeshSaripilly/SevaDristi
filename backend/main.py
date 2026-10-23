from __future__ import annotations
import os
import sys
import time
import uuid
import json
import shutil
import logging
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import cv2
from backend.api.verify import router as verify_router, rule_engine
from backend.api.qr import router as qr_router
from backend.services.ocr_extractor import HAS_PYTESSERACT
from backend.services.qr_bridge import get_signing_secret, DEMO_MODE
from backend.services.cache import session_cache
from backend.services.metrics import REQUEST_LATENCY, get_metrics_payload
from backend.db.database import init_db

# -------------------------------------------------------------
# Structured JSON Logging Setup
# -------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
root_logger = logging.getLogger()
root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
root_logger.handlers = [handler]

logger = logging.getLogger("sevadristi")

# -------------------------------------------------------------
# Sentry Instrumentation Placeholder
# -------------------------------------------------------------
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.05,
            environment=os.getenv("ENVIRONMENT", "production")
        )
        logger.info("Sentry monitoring initialized successfully.")
    except Exception as e:
        logger.warning(f"Sentry SDK initialization failed: {e}")

# -------------------------------------------------------------
# Rate Limiting (SlowAPI)
# -------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

# -------------------------------------------------------------
# Application Lifespan
# -------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SevaDristi production application...")
    await init_db()
    yield
    logger.info("Shutting down SevaDristi application...")

app = FastAPI(
    title="SevaDristi Pre-Verification API",
    description="Offline-capable, multilingual pre-verification assistant for Telangana MeeSeva & CSC centres.",
    version="2026.1.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# -------------------------------------------------------------
# Security & Request Context Middlewares
# -------------------------------------------------------------
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

@app.middleware("http")
async def security_and_observability_middleware(request: Request, call_next: Callable):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()

    # Pass request_id via state
    request.state.request_id = request_id

    response = await call_next(request)

    duration = time.time() - start_time
    # Record Prometheus request latency
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=str(response.status_code)
    ).observe(duration)

    # Attach security headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "frame-ancestors 'none';"
    )

    return response

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True, extra={"request_id": req_id})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please contact the MeeSeva IT administrator.",
            "request_id": req_id
        }
    )

# -------------------------------------------------------------
# Routers
# -------------------------------------------------------------
app.include_router(verify_router)
app.include_router(qr_router)

# -------------------------------------------------------------
# Metrics & Health Endpoints
# -------------------------------------------------------------
@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint for scraping."""
    content, content_type = get_metrics_payload()
    return Response(content=content, media_type=content_type)

@app.get("/api/health")
async def health_check():
    """Detailed multi-subsystem production health check."""
    # Check OpenCV functionality
    cv2_status = True
    try:
        test_mat = cv2.Laplacian(cv2.UMat(10, 10, cv2.CV_8U), cv2.CV_64F)
    except Exception:
        cv2_status = False

    # Check signing key configuration
    qr_secret_status = False
    try:
        secret = get_signing_secret()
        qr_secret_status = bool(secret)
    except Exception:
        qr_secret_status = False

    # Check storage disk space
    disk_usage = shutil.disk_usage(".")
    disk_free_gb = round(disk_usage.free / (1024 ** 3), 2)

    # Check redis connectivity
    redis_alive = session_cache.is_redis_connected()

    healthy = cv2_status and (qr_secret_status or DEMO_MODE) and (disk_free_gb > 0.5)

    return {
        "status": "healthy" if healthy else "degraded",
        "service": "SevaDristi",
        "version": "2026.1.0",
        "demo_mode": DEMO_MODE,
        "checks": {
            "ocr_available": HAS_PYTESSERACT,
            "ocr_engine_available": HAS_PYTESSERACT,
            "ocr_engine_type": "Tesseract (pytesseract)" if HAS_PYTESSERACT else "Unavailable",
            "cv2_available": cv2_status,
            "opencv_cv2_active": cv2_status,
            "qr_secret_configured": qr_secret_status,
            "redis_cache_connected": redis_alive,
            "disk_free_gb": disk_free_gb,
            "disk_space_ok": disk_free_gb > 0.5
        },
        "schemes_configured_count": len(rule_engine.schemes_by_id),
        "privacy_mode": "Zero-Disk In-Memory Processing",
        "supported_locales_count": 12
    }

@app.get("/api/schemes")
async def list_schemes():
    return rule_engine.config.get("schemes", [])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
