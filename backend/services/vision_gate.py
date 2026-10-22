from __future__ import annotations
import io
import base64
from typing import Dict, Any, Tuple, Optional
import cv2
import numpy as np
from PIL import Image

BLUR_THRESHOLD_DEFAULT = 110.0
GLARE_THRESHOLD_DEFAULT = 0.08

def compute_blur_score(image_bgr: np.ndarray) -> float:
    """
    Computes variance of the Laplacian as a proxy for image sharpness.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    score = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(round(score, 2))

def compute_glare_ratio(image_bgr: np.ndarray) -> float:
    """
    Computes ratio of overexposed/reflective pixels in HSV color space:
    V > 245 and S < 25.
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    glare_mask = (v > 245) & (s < 25)
    ratio = np.count_nonzero(glare_mask) / (image_bgr.shape[0] * image_bgr.shape[1])
    return float(round(ratio, 4))

def order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_w = max(int(width_a), int(width_b))

    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_h = max(int(height_a), int(height_b))

    dst = np.array([
        [0, 0],
        [max_w - 1, 0],
        [max_w - 1, max_h - 1],
        [0, max_h - 1]
    ], dtype="float32")

    m = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, m, (max_w, max_h))
    return warped

def auto_crop_document(image_bgr: np.ndarray) -> Tuple[np.ndarray, bool, str]:
    """
    Attempts to locate document boundary contour and apply perspective crop.
    Returns: (processed_image, crop_applied, note)
    """
    orig_h, orig_w = image_bgr.shape[:2]
    # Resize for robust contour detection
    ratio = orig_h / 500.0
    small = cv2.resize(image_bgr, (int(orig_w / ratio), 500))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    doc_cnt = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and cv2.contourArea(c) > (small.shape[0] * small.shape[1] * 0.20):
            doc_cnt = approx
            break

    if doc_cnt is not None:
        pts = doc_cnt.reshape(4, 2) * ratio
        warped = four_point_transform(image_bgr, pts)
        return warped, True, "Document boundary detected and perspective corrected."
    
    return image_bgr, False, "Document boundary not confidently distinguished; retained original frame."

def detect_seal_and_signature_heuristics(image_bgr: np.ndarray) -> Dict[str, Any]:
    """
    Heuristic check for colored circular stamps (purple/blue/red ink) and
    handwritten signature-like high-frequency stroke regions.
    Does NOT assert legal authenticity.
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # Blue / violet ink stamp detection (typical MeeSeva/Tahsildar stamps)
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([140, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    # Red ink stamp detection
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 70, 50])
    upper_red2 = np.array([180, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

    stamp_mask = mask_blue | mask_red
    stamp_pixel_ratio = np.count_nonzero(stamp_mask) / (image_bgr.shape[0] * image_bgr.shape[1])
    possible_seal = stamp_pixel_ratio > 0.003

    # Signature heuristic: dark stroke clusters in bottom third of document
    h_doc = image_bgr.shape[0]
    bottom_crop = image_bgr[int(h_doc * 0.65):, :]
    if bottom_crop.size > 0:
        gray_bottom = cv2.cvtColor(bottom_crop, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray_bottom, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        sig_candidates = [
            c for c in contours 
            if 30 < cv2.contourArea(c) < 5000 and 1.5 < (cv2.boundingRect(c)[2] / max(1, cv2.boundingRect(c)[3])) < 10.0
        ]
        possible_signature = len(sig_candidates) >= 1
    else:
        possible_signature = False

    return {
        "possible_seal_detected": bool(possible_seal),
        "possible_signature_detected": bool(possible_signature),
        "confidence": float(round(min(0.85, 0.5 + (0.35 if possible_seal else 0.0) + (0.15 if possible_signature else 0.0)), 2)),
        "method": "color_contour_stroke_heuristic",
        "limitations": "Automated heuristic only. Does not verify legal authenticity or officer identity."
    }

def image_to_base64_data_url(image_bgr: np.ndarray, max_dim: int = 800) -> str:
    """
    Converts image to JPEG base64 data URI in-memory.
    """
    h, w = image_bgr.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        image_bgr = cv2.resize(image_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    is_success, buffer = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not is_success:
        return ""
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"

def analyze_document_image(
    image_bytes: bytes,
    blur_threshold: float = BLUR_THRESHOLD_DEFAULT,
    glare_threshold: float = GLARE_THRESHOLD_DEFAULT
) -> Dict[str, Any]:
    """
    Full vision pipeline executed entirely in RAM:
    1. Decode from BytesIO
    2. Sharpness / Blur score
    3. Glare ratio
    4. Auto crop perspective
    5. Stamp & signature presence heuristics
    6. In-memory data URL generation
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError("Could not decode image from provided byte stream.")

    blur_score = compute_blur_score(image_bgr)
    glare_ratio = compute_glare_ratio(image_bgr)
    cropped_img, crop_applied, crop_note = auto_crop_document(image_bgr)
    seal_sig = detect_seal_and_signature_heuristics(cropped_img)

    preview_url = image_to_base64_data_url(cropped_img)

    return {
        "blur_score": blur_score,
        "blur_threshold": blur_threshold,
        "is_blurred": bool(blur_score < blur_threshold),
        "glare_ratio": glare_ratio,
        "glare_threshold": glare_threshold,
        "has_glare": bool(glare_ratio > glare_threshold),
        "crop_applied": crop_applied,
        "crop_note": crop_note,
        "possible_seal_detected": seal_sig["possible_seal_detected"],
        "possible_signature_detected": seal_sig["possible_signature_detected"],
        "seal_signature_confidence": seal_sig["confidence"],
        "seal_signature_limitations": seal_sig["limitations"],
        "preview_data_url": preview_url,
        "processed_image_bgr": cropped_img
    }
