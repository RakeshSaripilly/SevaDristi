import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.qr_bridge import generate_signed_qr_payload

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SevaDristi"
    assert data["supported_locales_count"] == 12

def test_schemes_endpoint():
    res = client.get("/api/schemes")
    assert res.status_code == 200
    schemes = res.json()
    assert len(schemes) >= 3
    ids = [s["id"] for s in schemes]
    assert "epass_scholarship" in ids
    assert "aasara_pension" in ids
    assert "rythu_bharosa" in ids

def test_verify_preset_1_red():
    """
    Preset 1 RED: Multiple discrepancies (mismatch, expiry, blur)
    """
    res = client.post(
        "/api/verify",
        data={
            "scheme_id": "epass_scholarship",
            "demo_preset": "preset_1_red",
            "language": "te-IN"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["processing_mode"] == "demo"
    assert data["overall_status"] in ["NEEDS_REVIEW", "ACTION_REQUIRED"]
    # Check that Telugu advisory was generated
    adv_titles = [a["title"] for a in data["advisories"]]
    assert len(adv_titles) > 0
    # Check that surname mismatch was detected
    mismatch_found = any(fc["status"] == "RED_MISMATCH" for fc in data["field_comparisons"])
    assert mismatch_found is True
    # Check QR generated
    assert data["qr_available"] is True
    assert data["qr_payload"] is not None

def test_verify_preset_2_yellow():
    """
    Preset 2 YELLOW: Initial expansion and phonetic variation
    """
    res = client.post(
        "/api/verify",
        data={
            "scheme_id": "aasara_pension",
            "demo_preset": "preset_2_yellow",
            "language": "en-IN"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["overall_status"] == "NEEDS_REVIEW"
    # Initial expansion detected
    initial_exp_found = any(fc["status"] == "WARNING_INITIAL_EXPANSION" for fc in data["field_comparisons"])
    assert initial_exp_found is True

def test_verify_preset_3_green():
    """
    Preset 3 GREEN: Clean docs, no issues detected
    """
    res = client.post(
        "/api/verify",
        data={
            "scheme_id": "epass_scholarship",
            "demo_preset": "preset_3_green",
            "language": "en-IN"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["overall_status"] == "NO_ISSUES_DETECTED"
    assert len(data["quality_issues"]) == 0

def test_verify_preset_4_glare_and_seal():
    """
    Preset 4: Quality warnings (glare and seal)
    """
    res = client.post(
        "/api/verify",
        data={
            "scheme_id": "epass_scholarship",
            "demo_preset": "preset_4_glare_seal",
            "language": "hi-IN"
        }
    )
    assert res.status_code == 200
    data = res.json()
    q_codes = [q["code"] for q in data["quality_issues"]]
    assert "IMAGE_GLARE" in q_codes

def test_decode_qr_endpoint():
    token = generate_signed_qr_payload(
        session_id="ephem-999",
        scheme_id="epass_scholarship",
        overall_status="NO_ISSUES_DETECTED",
        verified_fields={"nam": "S******* RAKESH", "cnt": 3}
    )
    res = client.post("/api/decode-qr", json={"qr_payload": token})
    assert res.status_code == 200
    data = res.json()
    assert data["valid_signature"] is True
    assert data["not_expired"] is True
    assert data["issuer"] == "SevaDristi-v1"
    assert data["verified_fields"]["nam"] == "S******* RAKESH"

def test_decode_tampered_qr_endpoint():
    res = client.post("/api/decode-qr", json={"qr_payload": "tampered.token.data"})
    assert res.status_code == 200
    data = res.json()
    assert data["valid_signature"] is False
