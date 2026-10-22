from __future__ import annotations
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.verify import router as verify_router, rule_engine
from backend.api.qr import router as qr_router
from backend.services.ocr_extractor import HAS_PYTESSERACT

# Configure logging with sanitization
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SevaDristi")

app = FastAPI(
    title="SevaDristi Pre-Verification API",
    description="Offline-capable, multilingual pre-verification assistant for Telangana MeeSeva / CSC service applications.",
    version="2026.1.0"
)

# CORS configured for local development Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(verify_router)
app.include_router(qr_router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SevaDristi",
        "ocr_engine_available": HAS_PYTESSERACT,
        "ocr_engine_type": "Tesseract (pytesseract)" if HAS_PYTESSERACT else "Synthetic/Demo Fixtures Only",
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
