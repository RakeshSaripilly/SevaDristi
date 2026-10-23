import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.qr_bridge import (
    generate_signed_qr_payload,
    verify_and_decode_qr_payload,
    get_signing_secret
)
from backend.services.privacy import validate_image_file, mask_aadhaar_string

client = TestClient(app)

def test_deep_health_endpoint():
    """Verify production deep health check returns system component health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "checks" in data
    checks = data["checks"]
    assert "ocr_available" in checks
    assert "cv2_available" in checks
    assert checks["cv2_available"] is True
    assert "qr_secret_configured" in checks
    assert "disk_space_ok" in checks
    assert checks["disk_space_ok"] is True

def test_prometheus_metrics_endpoint():
    """Verify /metrics returns Prometheus formatted exposition."""
    response = client.get("/metrics")
    assert response.status_code == 200
    text = response.text
    assert "sevadristi_verifications_total" in text or "python_gc_objects_collected_total" in text or "process_cpu_seconds_total" in text

def test_qr_bridge_key_rotation(monkeypatch):
    """Verify seamless key rotation using old key verification fallback."""
    primary_secret = "primary_secret_key_111111111111111111111111111111111111111111111111"
    old_secret = "old_secret_key_222222222222222222222222222222222222222222222222"

    monkeypatch.setenv("SEVADRISTI_QR_SECRET", old_secret)
    monkeypatch.delenv("SEVADRISTI_QR_SECRET_OLD", raising=False)
    
    # Generate token signed with old key
    old_token = generate_signed_qr_payload(
        session_id="test-rot-001",
        scheme_id="ts_kalyana_lakshmi",
        overall_status="READY",
        verified_fields={"nam": "R* S*", "aadhaar": "XXXX-XXXX-1234"},
        warnings=[]
    )

    # Now rotate: primary secret is new, old secret is kept in SEVADRISTI_QR_SECRET_OLD
    monkeypatch.setenv("SEVADRISTI_QR_SECRET", primary_secret)
    monkeypatch.setenv("SEVADRISTI_QR_SECRET_OLD", old_secret)

    # Decoding should succeed through old key fallback
    decoded = verify_and_decode_qr_payload(old_token)
    assert decoded["valid_signature"] is True
    assert decoded["not_expired"] is True
    assert decoded["scheme_id"] == "ts_kalyana_lakshmi"
    assert decoded["verified_fields"]["aadhaar"] == "XXXX-XXXX-1234"

def test_privacy_file_signature_validation():
    """Verify Pillow image signature verification passes valid images and rejects junk."""
    from PIL import Image
    import io

    # Valid PNG in-memory
    valid_buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color="blue")
    img.save(valid_buf, format="PNG")
    valid_bytes = valid_buf.getvalue()

    is_valid, msg = validate_image_file(valid_bytes)
    assert is_valid is True

    # Invalid junk bytes
    junk_bytes = b"NOT_AN_IMAGE_FILE_HEADER_DATA"
    is_valid_junk, err_junk = validate_image_file(junk_bytes)
    assert is_valid_junk is False
    assert "Invalid" in err_junk

def test_production_gate_requires_real_files(monkeypatch):
    """Verify production /api/verify strictly requires real file uploads and ignores synthetic preset queries."""
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("SEVADRISTI_QR_SECRET", "prod_secret_333333333333333333333333333333333333333333333333")

    response = client.post(
        "/api/verify",
        data={
            "scheme_id": "ts_kalyana_lakshmi",
            "demo_preset": "preset_3_green"
        }
    )
    assert response.status_code == 400
    assert "No document images provided" in response.json()["detail"]
