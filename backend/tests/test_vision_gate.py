import io
import cv2
import numpy as np
import pytest
from backend.services.vision_gate import (
    compute_blur_score,
    compute_glare_ratio,
    auto_crop_document,
    detect_seal_and_signature_heuristics,
    analyze_document_image
)

def create_synthetic_image(sharp: bool = True, glare: bool = False, seal: bool = False) -> bytes:
    """
    Creates a synthetic image in-memory for deterministic testing.
    """
    # Create white document canvas (400x600)
    img = np.ones((600, 400, 3), dtype=np.uint8) * 240
    
    # Draw simulated black text lines
    for y in range(80, 500, 40):
        cv2.putText(img, "TELANGANA MEESEVA APPLICATION FORM", (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1)

    if not sharp:
        # Apply heavy Gaussian blur
        img = cv2.GaussianBlur(img, (25, 25), 0)

    if glare:
        # Create severe overexposed hotspot in center (V=255, S=0)
        cv2.circle(img, (200, 300), 80, (255, 255, 255), -1)

    if seal:
        # Draw circular purple/blue stamp in lower right
        cv2.circle(img, (320, 520), 40, (180, 50, 100), 3)
        cv2.putText(img, "SEAL", (305, 525), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 50, 100), 1)

    is_success, buffer = cv2.imencode(".jpg", img)
    return buffer.tobytes()

def test_sharp_vs_blurred_image():
    sharp_bytes = create_synthetic_image(sharp=True)
    blurred_bytes = create_synthetic_image(sharp=False)

    sharp_res = analyze_document_image(sharp_bytes, blur_threshold=110.0)
    blurred_res = analyze_document_image(blurred_bytes, blur_threshold=110.0)

    assert sharp_res["blur_score"] > 110.0
    assert sharp_res["is_blurred"] is False

    assert blurred_res["blur_score"] < 110.0
    assert blurred_res["is_blurred"] is True

def test_glare_detection():
    clean_bytes = create_synthetic_image(glare=False)
    glare_bytes = create_synthetic_image(glare=True)

    clean_res = analyze_document_image(clean_bytes, glare_threshold=0.08)
    glare_res = analyze_document_image(glare_bytes, glare_threshold=0.08)

    assert clean_res["has_glare"] is False
    assert clean_res["glare_ratio"] < 0.08

    assert glare_res["has_glare"] is True
    assert glare_res["glare_ratio"] >= 0.08

def test_seal_heuristic():
    no_seal_bytes = create_synthetic_image(seal=False)
    seal_bytes = create_synthetic_image(seal=True)

    no_seal_res = analyze_document_image(no_seal_bytes)
    seal_res = analyze_document_image(seal_bytes)

    assert seal_res["possible_seal_detected"] is True
    assert "heuristic" in seal_res["seal_signature_limitations"].lower()

def test_invalid_image_bytes():
    with pytest.raises(ValueError):
        analyze_document_image(b"not_an_image_data")
