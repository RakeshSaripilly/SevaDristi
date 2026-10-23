import json
import io
import pytest
from PIL import Image, ImageDraw, ImageFilter
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.qr_bridge import generate_signed_qr_payload

client = TestClient(app)

def _create_mock_image(sharp: bool = True, text: str = "SAMPLE GOVT DOCUMENT") -> bytes:
    """Helper to generate an in-memory test PNG byte stream."""
    img = Image.new("RGB", (400, 300), color=(250, 250, 250))
    d = ImageDraw.Draw(img)
    # Add contrasting lines and text for sharpness
    for i in range(10, 290, 20):
        d.line([(10, i), (390, i)], fill=(40, 40, 40), width=2)
    d.text((30, 50), text, fill=(0, 0, 0))
    d.text((30, 100), "TELANGANA GOVT CERTIFICATE", fill=(0, 0, 0))
    
    if not sharp:
        # Apply heavy blur to drop Laplacian variance below 110
        img = img.filter(ImageFilter.GaussianBlur(radius=15))
        
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
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

def test_verify_real_upload_matching_docs():
    """Verify production flow with real uploaded files and name editing."""
    img1_bytes = _create_mock_image(sharp=True, text="AADHAAR SARIPILLY RAKESH")
    img2_bytes = _create_mock_image(sharp=True, text="INCOME SARIPALLY RAKESH")

    files = [
        ("documents", ("aadhaar.png", img1_bytes, "image/png")),
        ("documents", ("income.png", img2_bytes, "image/png")),
    ]
    data = {
        "scheme_id": "epass_scholarship",
        "language": "te-IN",
        "doc_type_hints": json.dumps(["IDENTITY_CARD", "INCOME_CERT"]),
        "user_edited_names": json.dumps({
            "IDENTITY_CARD": "SARIPILLY RAKESH",
            "INCOME_CERT": "SARIPALLY RAKESH"
        })
    }

    res = client.post("/api/verify", files=files, data=data)
    assert res.status_code == 200
    body = res.json()
    assert body["processing_mode"] == "real"
    assert len(body["documents"]) == 2
    # Verify both documents have real quality metrics
    for doc in body["documents"]:
        assert "blur_score" in doc
        assert "glare_ratio" in doc
        assert doc["is_blurred"] is False
    # Verify reconciliation ran on real names
    assert len(body["field_comparisons"]) > 0
    comp = body["field_comparisons"][0]
    assert comp["status"] in ["EXACT_MATCH", "WARNING_PHONETIC_VARIATION", "WARNING_SIMILAR", "YELLOW_REVIEW"]
    # Check QR generated
    assert body["qr_available"] is True
    assert body["qr_payload"] is not None

def test_verify_real_upload_blurry_detection():
    """Verify that Laplacian blur detection flags low sharpness on real blurry uploads."""
    blurry_bytes = _create_mock_image(sharp=False, text="BLURRY DOC")

    files = [
        ("documents", ("blurry_doc.png", blurry_bytes, "image/png")),
    ]
    data = {
        "scheme_id": "epass_scholarship",
        "language": "te-IN",
        "doc_type_hints": json.dumps(["IDENTITY_CARD"])
    }

    res = client.post("/api/verify", files=files, data=data)
    assert res.status_code == 200
    body = res.json()
    assert len(body["documents"]) == 1
    doc = body["documents"][0]
    assert doc["is_blurred"] is True
    assert doc["blur_score"] < 110
    # Should produce blur advisory
    blur_advisories = [a for a in body["advisories"] if "BLUR" in a.get("title", "").upper() or "ఫోటో" in a.get("title", "")]
    assert len(blur_advisories) > 0 or any("BLUR" in q.get("code", "") for q in body["quality_issues"])

def test_verify_rejects_empty_upload():
    """Production endpoint must strictly reject calls with zero document uploads."""
    res = client.post(
        "/api/verify",
        data={"scheme_id": "epass_scholarship", "language": "en-IN"}
    )
    assert res.status_code == 400
    assert "No document images provided" in res.json()["detail"]

def test_extract_single_doc_endpoint():
    """Verify quick single doc quality and name extraction endpoint."""
    img_bytes = _create_mock_image(sharp=True, text="AADHAAR SARIPILLY RAKESH")
    files = {"document": ("doc.png", img_bytes, "image/png")}
    data = {"doc_type_hint": "IDENTITY_CARD"}

    res = client.post("/api/extract-name-only", files=files, data=data)
    assert res.status_code == 200
    body = res.json()
    assert body["doc_type"] == "IDENTITY_CARD"
    assert "quality" in body
    assert body["quality"]["is_blurry"] is False
    assert "corners" in body["quality"]

def test_clear_session_endpoint():
    """Verify privacy endpoint to purge ephemeral session data."""
    res = client.post("/api/clear-session", data={"session_id": "sess-test-888"})
    assert res.status_code == 200
    body = res.json()
    assert body["session_id"] == "sess-test-888"

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
