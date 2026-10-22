from __future__ import annotations
from fastapi import APIRouter
from backend.models.schemas import DecodeQRRequest, DecodedQRResponse
from backend.services.qr_bridge import verify_and_decode_qr_payload

router = APIRouter(prefix="/api", tags=["QR"])

@router.post("/decode-qr", response_model=DecodedQRResponse)
async def decode_qr_endpoint(request: DecodeQRRequest):
    """
    Decodes an HMAC-SHA256 signed Pre-Verification Summary QR token.
    Validates token structure, signature cryptographic integrity, issuer, and expiry.
    """
    result = verify_and_decode_qr_payload(request.qr_payload)
    return DecodedQRResponse(**result)
