from __future__ import annotations
import os
import io
import json
import base64
import hmac
import hashlib
import time
from typing import Dict, Any, Optional
import qrcode

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
DEFAULT_DEMO_SECRET = "sevadristi_hackathon_demo_secret_key_2026"

def get_signing_secret() -> str:
    """
    Retrieves the primary active signing secret.
    In production (DEMO_MODE=false), fails closed if secret is missing or insecure.
    """
    secret = os.getenv("SEVADRISTI_QR_SECRET")
    if not secret:
        if not DEMO_MODE:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: "
                "SEVADRISTI_QR_SECRET must be securely provided via environment or secrets manager in production."
            )
        return DEFAULT_DEMO_SECRET
    return secret

def get_rotated_old_secret() -> Optional[str]:
    """Retrieves previous signing secret during zero-downtime key rotation windows."""
    return os.getenv("SEVADRISTI_QR_SECRET_OLD")

EXPIRY_SECONDS_DEFAULT = 7 * 24 * 3600  # 7 days

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def base64url_decode(data_str: str) -> bytes:
    padding = "=" * (4 - (len(data_str) % 4)) if len(data_str) % 4 != 0 else ""
    return base64.urlsafe_b64decode(data_str + padding)

def sign_payload(payload_bytes: bytes, secret: Optional[str] = None) -> str:
    """
    Computes HMAC-SHA256 signature and returns base64url string.
    """
    active_secret = secret or get_signing_secret()
    sig = hmac.new(active_secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return base64url_encode(sig)

def generate_signed_qr_payload(
    session_id: str,
    scheme_id: str,
    overall_status: str,
    verified_fields: Dict[str, Any],
    warnings: Optional[list] = None,
    expiry_seconds: int = EXPIRY_SECONDS_DEFAULT,
    secret: Optional[str] = None
) -> str:
    """
    Constructs and signs a privacy-preserving pre-verification token.
    Format: <base64url_payload>.<base64url_signature>
    """
    now = int(time.time())
    exp = now + expiry_seconds

    payload = {
        "v": "1.0",
        "iss": "SevaDristi-v1",
        "sid": session_id,
        "sch": scheme_id,
        "st": overall_status,
        "iat": now,
        "exp": exp,
        "f": verified_fields,
        "w": warnings or []
    }

    raw_json = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode("utf-8")
    b64_payload = base64url_encode(raw_json)
    signature = sign_payload(b64_payload.encode("utf-8"), secret)
    return f"{b64_payload}.{signature}"

def verify_and_decode_qr_payload(
    qr_token: str,
    secret: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validates token structure, HMAC-SHA256 signature, expiry, and issuer.
    Supports key rotation: verifies against active key first, then fallback old key.
    """
    parts = qr_token.strip().split(".")
    if len(parts) != 2:
        return {
            "valid_signature": False,
            "not_expired": False,
            "verification_scope": "NONE",
            "warnings": ["Malformed token structure: expected payload.signature"]
        }

    b64_payload, signature_claimed = parts
    payload_bytes = b64_payload.encode("utf-8")

    primary_secret = secret or get_signing_secret()
    expected_sig = sign_payload(payload_bytes, primary_secret)

    signature_valid = hmac.compare_digest(signature_claimed, expected_sig)
    key_rotated_note = None

    # Check rotated previous key if primary signature mismatch
    if not signature_valid and not secret:
        old_secret = get_rotated_old_secret()
        if old_secret:
            expected_old_sig = sign_payload(payload_bytes, old_secret)
            if hmac.compare_digest(signature_claimed, expected_old_sig):
                signature_valid = True
                key_rotated_note = "Token verified using previous rotated secret key."

    if not signature_valid:
        return {
            "valid_signature": False,
            "not_expired": False,
            "verification_scope": "NONE",
            "warnings": ["Signature verification failed: Payload was altered or signed with an unknown key."]
        }

    try:
        raw_json = base64url_decode(b64_payload).decode("utf-8")
        payload = json.loads(raw_json)
    except Exception as e:
        return {
            "valid_signature": False,
            "not_expired": False,
            "verification_scope": "NONE",
            "warnings": [f"Malformed payload data: {str(e)}"]
        }

    now = int(time.time())
    exp = payload.get("exp", 0)
    not_expired = exp > now

    warnings = list(payload.get("w", []))
    if key_rotated_note:
        warnings.append(key_rotated_note)

    if not not_expired:
        warnings.append("Token has expired.")

    if payload.get("iss") != "SevaDristi-v1":
        warnings.append(f"Unrecognized issuer '{payload.get('iss')}'.")

    return {
        "valid_signature": True,
        "not_expired": not_expired,
        "issuer": payload.get("iss"),
        "scheme_id": payload.get("sch"),
        "session_ref": payload.get("sid"),
        "pre_verification_status": payload.get("st"),
        "verified_fields": payload.get("f", {}),
        "verification_scope": "Pre-verification summary: quality checked, name reconciled, validity checked.",
        "issued_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(payload.get("iat", 0))),
        "expires_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(exp)),
        "warnings": warnings
    }

def generate_qr_image_data_url(payload_str: str) -> str:
    """
    Renders QR code into in-memory PNG and returns base64 data URL.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(payload_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"
