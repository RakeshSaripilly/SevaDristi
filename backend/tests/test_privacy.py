import io
from PIL import Image
import pytest
from backend.services.privacy import mask_aadhaar_string, mask_name_privacy, redact_image_region

def test_aadhaar_string_masking():
    """
    Ensures 12-digit Aadhaar patterns are masked to XXXX-XXXX-1234.
    """
    raw_spaced = "My Aadhaar is 5432 1098 7654 for verification."
    masked_spaced = mask_aadhaar_string(raw_spaced)
    assert "5432 1098" not in masked_spaced
    assert "XXXX-XXXX-7654" in masked_spaced

    raw_hyphen = "ID: 1234-5678-9012"
    masked_hyphen = mask_aadhaar_string(raw_hyphen)
    assert "1234" not in masked_hyphen
    assert "XXXX-XXXX-9012" in masked_hyphen

    raw_nospace = "Card number 987654321098 on back."
    masked_nospace = mask_aadhaar_string(raw_nospace)
    assert "987654321098" not in masked_nospace
    assert "XXXX-XXXX-1098" in masked_nospace

def test_name_masking_for_summary_qr():
    """
    Partially masks name for privacy in QR payloads.
    """
    masked = mask_name_privacy("SARIPILLY RAKESH")
    assert masked.endswith("RAKESH")
    assert "*" in masked
    assert "SARIPILLY" not in masked

def test_in_memory_redaction():
    """
    Verifies that redaction produces a valid image in-memory without saving to disk.
    """
    # Create simple in-memory test image
    img = Image.new("RGB", (300, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    orig_bytes = buf.getvalue()

    redacted_bytes = redact_image_region(orig_bytes)
    assert len(redacted_bytes) > 0
    # Can be reopened and checked
    reopened = Image.open(io.BytesIO(redacted_bytes))
    assert reopened.size == (300, 200)
