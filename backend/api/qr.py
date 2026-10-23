from __future__ import annotations
from fastapi import APIRouter
from backend.models.schemas import DecodeQRRequest, DecodedQRResponse
from backend.services.qr_bridge import verify_and_decode_qr_payload
from backend.services.metrics import QR_OPERATIONS_TOTAL

router = APIRouter(prefix="/api", tags=["QR"])

@router.post("/decode-qr", response_model=DecodedQRResponse)
async def decode_qr_endpoint(request: DecodeQRRequest):
    """
    Decodes an HMAC-SHA256 signed Pre-Verification Summary QR token.
    Validates token structure, signature cryptographic integrity, issuer, and expiry.
    """
    result = verify_and_decode_qr_payload(request.qr_payload)
    status_label = "valid" if (result.get("valid_signature") and result.get("not_expired")) else "invalid"
    QR_OPERATIONS_TOTAL.labels(operation="decode", status=status_label).inc()
    return DecodedQRResponse(**result)
