from __future__ import annotations
import re
import shutil
from typing import Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image

from backend.services.privacy import mask_aadhaar_string

# Check if pytesseract and tesseract binary are available
HAS_PYTESSERACT = False
try:
    import pytesseract
    if shutil.which("tesseract") or shutil.which("tesseract.exe"):
        HAS_PYTESSERACT = True
except Exception:
    HAS_PYTESSERACT = False

DATE_PATTERNS = [
    re.compile(r'\b(\d{2})[/.-](\d{2})[/.-](\d{4})\b'),  # DD/MM/YYYY or MM/DD/YYYY
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
                return f"{g[2]}-{g[1]}-{g[0]}"
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

def extract_fields_from_ocr(
    image_bgr: np.ndarray,
    user_hint_type: Optional[str] = None
) -> Tuple[Dict[str, Any], float, str]:
    """
    Extracts text using pytesseract if available.
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
                "id_reference": None
            },
            0.0,
            "OCR_UNAVAILABLE: Local OCR engine (Tesseract) is not installed or not on system PATH."
        )

    # Perform OCR
    pil_img = Image.fromarray(image_bgr)
    data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
    text = pytesseract.image_to_string(pil_img)

    # Average confidence of detected words
    conf_list = [float(c) for c in data.get("conf", []) if c != "-1" and str(c).isdigit()]
    avg_conf = (sum(conf_list) / max(1, len(conf_list))) / 100.0 if conf_list else 0.5

    detected_type = user_hint_type or classify_doc_type(text)
    masked_text = mask_aadhaar_string(text)

    # Heuristic field extractions
    dob = parse_iso_date(text)
    pincode = extract_pincode(text)
    income = extract_income_amount(text) if detected_type == "INCOME_CERT" else None

    # Name extraction heuristic: find lines with common names or capital strings
    lines = [line.strip() for line in masked_text.split("\n") if line.strip()]
    candidate_name = None
    for line in lines:
        if re.search(r'\b(Name|Applicant|Sri|Smt)\b[:\s]*([A-Za-z\s\.]{3,35})', line, re.IGNORECASE):
            m = re.search(r'\b(Name|Applicant|Sri|Smt)\b[:\s]*([A-Za-z\s\.]{3,35})', line, re.IGNORECASE)
            candidate_name = m.group(2).strip()
            break

    # ID reference extraction
    id_ref = None
    if detected_type == "IDENTITY_CARD":
        # Check for masked Aadhaar pattern
        m_id = re.search(r'XXXX-XXXX-\d{4}', masked_text)
        if m_id:
            id_ref = m_id.group(0)

    fields = {
        "doc_type": detected_type,
        "full_name": candidate_name,
        "guardian_name": None,
        "dob": dob,
        "pincode": pincode,
        "issue_date": dob if detected_type in ["INCOME_CERT", "CASTE_CERT"] else None,
        "annual_income_inr": income,
        "id_reference": id_ref
    }

    return fields, float(round(avg_conf, 2)), "OCR_SUCCESS"
