import time
import pytest
from backend.services.qr_bridge import (
    generate_signed_qr_payload,
    verify_and_decode_qr_payload,
    generate_qr_image_data_url
)

def test_valid_qr_generation_and_decoding():
    token = generate_signed_qr_payload(
        session_id="ephem-1234",
        scheme_id="epass_scholarship",
        overall_status="NO_ISSUES_DETECTED",
        verified_fields={"nam": "S******* RAKESH", "dob_yr": "2001", "cnt": 3},
        warnings=[]
    )
    assert "." in token
    decoded = verify_and_decode_qr_payload(token)
    assert decoded["valid_signature"] is True
    assert decoded["not_expired"] is True
    assert decoded["scheme_id"] == "epass_scholarship"
    assert decoded["verified_fields"]["nam"] == "S******* RAKESH"

def test_tampered_payload_rejected():
    token = generate_signed_qr_payload(
        session_id="ephem-1234",
        scheme_id="epass_scholarship",
        overall_status="NO_ISSUES_DETECTED",
        verified_fields={"nam": "S******* RAKESH"}
    )
    b64_payload, sig = token.split(".")
    # Tamper with payload string
    tampered_payload = b64_payload[:-2] + "ab"
    tampered_token = f"{tampered_payload}.{sig}"
    
    decoded = verify_and_decode_qr_payload(tampered_token)
    assert decoded["valid_signature"] is False
    assert "altered" in decoded["warnings"][0].lower()

def test_wrong_signing_key_rejected():
    token = generate_signed_qr_payload(
        session_id="ephem-1234",
        scheme_id="epass_scholarship",
        overall_status="NO_ISSUES_DETECTED",
        verified_fields={},
        secret="secret_key_A"
    )
    decoded = verify_and_decode_qr_payload(token, secret="secret_key_B")
    assert decoded["valid_signature"] is False

def test_expired_token():
    # Token with negative expiry duration
    token = generate_signed_qr_payload(
        session_id="ephem-1234",
        scheme_id="epass_scholarship",
        overall_status="NO_ISSUES_DETECTED",
        verified_fields={},
        expiry_seconds=-100
    )
    decoded = verify_and_decode_qr_payload(token)
    assert decoded["valid_signature"] is True
    assert decoded["not_expired"] is False
    assert any("expired" in w.lower() for w in decoded["warnings"])

def test_qr_image_generation():
    token = generate_signed_qr_payload(
        session_id="ephem-test",
        scheme_id="epass_scholarship",
        overall_status="NO_ISSUES_DETECTED",
        verified_fields={}
    )
    img_url = generate_qr_image_data_url(token)
    assert img_url.startswith("data:image/png;base64,")
    assert len(img_url) > 100
