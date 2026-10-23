from __future__ import annotations
import re
import shutil
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import cv2
from PIL import Image

from backend.services.privacy import mask_aadhaar_string

logger = logging.getLogger("sevadristi.ocr")

# Check if pytesseract and tesseract binary are available
HAS_PYTESSERACT = False
try:
    import pytesseract
    if shutil.which("tesseract") or shutil.which("tesseract.exe"):
        HAS_PYTESSERACT = True
except Exception:
    HAS_PYTESSERACT = False

DATE_PATTERNS = [
    re.compile(r'\b(\d{2})[/.-](\d{2})[/.-](\d{4})\b'),  # DD/MM/YYYY or DD-MM-YYYY
    re.compile(r'\b(\d{4})[/.-](\d{2})[/.-](\d{2})\b'),  # YYYY-MM-DD
]

def parse_iso_date(text: str) -> Optional[str]:
    """
    Attempts to parse text and return normalized YYYY-MM-DD date.
    """
    for pat in DATE_PATTERNS:
        m = pat.search(text)
        if m:
            g = m.groups()
            if len(g[0]) == 4:  # YYYY-MM-DD
                return f"{g[0]}-{g[1]}-{g[2]}"
            elif len(g[2]) == 4:  # DD/MM/YYYY
                day, month, year = int(g[0]), int(g[1]), int(g[2])
                if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                    return f"{year:04d}-{month:02d}-{day:02d}"
    return None

def extract_income_amount(text: str) -> Optional[float]:
    """
    Searches for income figures (e.g. Rs. 1,20,000 or 150000).
    """
    matches = re.findall(r'(?:Rs\.?|INR|\bIncome\b[:\s]*|₹)\s*([\d,]{4,10})', text, re.IGNORECASE)
    for m in matches:
        clean_num = m.replace(",", "")
        try:
            val = float(clean_num)
            if 5000 <= val <= 10000000:
                return val
        except ValueError:
            continue
    return None

def extract_pincode(text: str) -> Optional[str]:
    """
    Matches 6-digit Indian PIN codes (e.g., 500032).
    """
    m = re.search(r'\b(5\d{5})\b', text)  # Telangana pins start with 5
    if m:
        return m.group(1)
    m_any = re.search(r'\b([1-9]\d{5})\b', text)
    if m_any:
        return m_any.group(1)
    return None

def classify_doc_type(text: str) -> str:
    """
    Heuristic classifier based on document header keywords.
    """
    t = text.lower()
    if any(k in t for k in ["unique identification", "aadhaar", "uidai", "enrollment", "male", "female", "yob"]):
        return "IDENTITY_CARD"
    if any(k in t for k in ["ration", "food security", "fsc", "epds", "consumer affairs"]):
        return "RATION_CARD"
    if any(k in t for k in ["income certificate", "annual income", "tahsildar", "revenue department", "meeseva income"]):
        return "INCOME_CERT"
    if any(k in t for k in ["caste certificate", "community", "social status", "scheduled caste", "scheduled tribe", "backward class"]):
        return "CASTE_CERT"
    if any(k in t for k in ["bank", "account no", "ifsc", "passbook", "savings", "branch"]):
        return "BANK_PASSBOOK"
    if any(k in t for k in ["pattadar", "passbook", "rofr", "survey no", "katha", "land"]):
        return "LAND_PASSBOOK"
    return "IDENTITY_CARD"

def preprocess_image_for_ocr(image_bgr: np.ndarray) -> np.ndarray:
    """
    Real document image preprocessing:
    1. Grayscale conversion
    2. Adaptive thresholding
    3. Deskewing to normalize rotated camera captures
    """
    if len(image_bgr.shape) == 3:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    else:
        gray = image_bgr.copy()

    # Slight Gaussian blur to reduce high frequency noise
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Deskew angle estimation
    try:
        thresh_for_skew = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh_for_skew > 0))
        if len(coords) > 100:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle
            if abs(angle) > 0.5 and abs(angle) < 30:
                (h, w) = gray.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    except Exception as e:
        logger.debug(f"Deskew skipped: {e}")

    # Adaptive Thresholding for contrast enhancement
    processed = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 4
    )
    return processed

def get_available_ocr_languages() -> str:
    """
    Discovers available Tesseract languages, prioritising Indic languages.
    """
    if not HAS_PYTESSERACT:
        return "eng"
    try:
        installed = pytesseract.get_languages()
        target_langs = ["eng", "tel", "hin", "tam", "kan", "mal"]
        found = [lang for lang in target_langs if lang in installed]
        return "+".join(found) if found else "eng"
    except Exception:
        return "eng"

def extract_names_from_text(text: str, doc_type: str, avg_conf: float) -> List[Dict[str, Any]]:
    """
    Extracts candidate names from real OCR text using document-specific regex patterns.
    Never returns synthetic placeholder data.
    """
    extracted_names: List[Dict[str, Any]] = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Pattern 1: Explicit labels (Name: X, Applicant Name: X)
    for line in lines:
        m = re.search(r'\b(?:Name(?:\s+of\s+Applicant)?|Applicant\s+Name|Sri/Smt|Sri|Smt|Kumari)\s*[:\-]?\s*([A-Za-z\s\.]{3,40})', line, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            # Clean common trailing artifacts
            candidate = re.sub(r'\b(DOB|Date|Father|S/o|D/o|W/o|Age|Gender|Year)\b.*', '', candidate, flags=re.IGNORECASE).strip()
            if len(candidate) >= 3 and not candidate.isnumeric():
                extracted_names.append({
                    "value": candidate.upper(),
                    "source_doc": doc_type,
                    "confidence": float(round(avg_conf, 2)),
                    "field_role": "APPLICANT"
                })
                break

    # Pattern 2: Certification statements ("This is to certify that Sri/Smt X")
    if not extracted_names:
        cert_match = re.search(r'certify\s+that\s+(?:Sri/Smt/Kumari\s+|Sri\s+|Smt\s+)?([A-Za-z\s\.]{3,40})', text, re.IGNORECASE)
        if cert_match:
            candidate = cert_match.group(1).strip()
            candidate = re.sub(r'\b(S/o|D/o|W/o|Resident|Village|Mandal|District)\b.*', '', candidate, flags=re.IGNORECASE).strip()
            if len(candidate) >= 3:
                extracted_names.append({
                    "value": candidate.upper(),
                    "source_doc": doc_type,
                    "confidence": float(round(avg_conf, 2)),
                    "field_role": "APPLICANT"
                })

    # Pattern 3: Aadhaar front card layout (Name typically precedes DOB/Year of Birth)
    if not extracted_names and doc_type == "IDENTITY_CARD":
        for i, line in enumerate(lines):
            if re.search(r'\b(?:DOB|Date\s+of\s+Birth|Year\s+of\s+Birth|YOB)\b', line, re.IGNORECASE):
                # Candidate is usually 1-2 lines above DOB
                for back_offset in [1, 2]:
                    if i - back_offset >= 0:
                        prev_line = lines[i - back_offset]
                        # Filter out Government / UIDAI headers
                        if not re.search(r'\b(Government|India|UIDAI|Unique|Identification|Authority|Enrollment)\b', prev_line, re.IGNORECASE):
                            clean_line = re.sub(r'[^A-Za-z\s\.]', '', prev_line).strip()
                            if len(clean_line) >= 3 and len(clean_line.split()) >= 1:
                                extracted_names.append({
                                    "value": clean_line.upper(),
                                    "source_doc": doc_type,
                                    "confidence": float(round(avg_conf * 0.9, 2)),
                                    "field_role": "APPLICANT"
                                })
                                break
                if extracted_names:
                    break

    return extracted_names

def extract_fields_from_ocr(
    image_bgr: np.ndarray,
    user_hint_type: Optional[str] = None
) -> Tuple[Dict[str, Any], float, str]:
    """
    Extracts text using real Tesseract OCR with adaptive preprocessing.
    If Tesseract is missing, returns status OCR_UNAVAILABLE with no synthetic placeholders.
    Returns: (fields_dict, confidence_score, status_note)
    """
    if not HAS_PYTESSERACT:
        return (
            {
                "doc_type": user_hint_type or "IDENTITY_CARD",
                "full_name": None,
                "guardian_name": None,
                "dob": None,
                "pincode": None,
                "issue_date": None,
                "annual_income_inr": None,
                "id_reference": None,
                "extracted_names": [],
                "raw_text_preview": ""
            },
            0.0,
            "OCR_UNAVAILABLE: Tesseract OCR engine is not installed or not on system PATH. Install tesseract-ocr + tel/hin."
        )

    # 1. Image preprocessing
    preprocessed = preprocess_image_for_ocr(image_bgr)
    pil_img = Image.fromarray(preprocessed)

    # 2. Configure languages and PSM mode
    ocr_lang = get_available_ocr_languages()
    custom_config = r'--oem 3 --psm 6'

    try:
        data = pytesseract.image_to_data(pil_img, lang=ocr_lang, config=custom_config, output_type=pytesseract.Output.DICT)
        raw_text = pytesseract.image_to_string(pil_img, lang=ocr_lang, config=custom_config)
    except Exception as e:
        logger.warning(f"PSM 6 failed, falling back to default PSM: {e}")
        try:
            data = pytesseract.image_to_data(pil_img, lang="eng", output_type=pytesseract.Output.DICT)
            raw_text = pytesseract.image_to_string(pil_img, lang="eng")
        except Exception as fallback_e:
            return (
                {
                    "doc_type": user_hint_type or "IDENTITY_CARD",
                    "full_name": None,
                    "guardian_name": None,
                    "dob": None,
                    "pincode": None,
                    "issue_date": None,
                    "annual_income_inr": None,
                    "id_reference": None,
                    "extracted_names": [],
                    "raw_text_preview": ""
                },
                0.0,
                f"OCR_ERROR: {str(fallback_e)}"
            )

    # 3. Calculate word confidence
    conf_list = [float(c) for c in data.get("conf", []) if c != "-1" and str(c).isdigit()]
    avg_conf = (sum(conf_list) / max(1, len(conf_list))) / 100.0 if conf_list else 0.5
    avg_conf = float(round(avg_conf, 2))

    detected_type = user_hint_type or classify_doc_type(raw_text)
    masked_text = mask_aadhaar_string(raw_text)

    # 4. Extract fields using real patterns
    dob = parse_iso_date(raw_text)
    pincode = extract_pincode(raw_text)
    income = extract_income_amount(raw_text) if detected_type == "INCOME_CERT" else None

    # Name extraction
    extracted_names = extract_names_from_text(masked_text, detected_type, avg_conf)
    candidate_name = extracted_names[0]["value"] if extracted_names else None

    # ID reference extraction
    id_ref = None
    if detected_type == "IDENTITY_CARD":
        m_id = re.search(r'XXXX-XXXX-\d{4}', masked_text)
        if m_id:
            id_ref = m_id.group(0)

    # Issue date check
    issue_date = dob if detected_type in ["INCOME_CERT", "CASTE_CERT"] else None

    fields = {
        "doc_type": detected_type,
        "full_name": candidate_name,
        "guardian_name": None,
        "dob": dob,
        "pincode": pincode,
        "issue_date": issue_date,
        "annual_income_inr": income,
        "id_reference": id_ref,
        "extracted_names": extracted_names,
        "raw_text_preview": masked_text[:200]
    }

    return fields, avg_conf, "OCR_SUCCESS"
