from __future__ import annotations
import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple
from rapidfuzz import fuzz, distance

HONORIFICS = {
    "sri", "sree", "shri", "smt", "shrimati", "kumari", "km",
    "mr", "mrs", "ms", "dr", "garu", "late", "thiru", "selvi"
}

INDIC_PHONETIC_REPLACEMENTS = [
    (r"EE", "I"),
    (r"OO", "U"),
    (r"Y\b", "I"),
    (r"W", "V"),
    (r"TH", "T"),
    (r"BH", "B"),
    (r"DH", "D"),
    (r"GH", "G"),
    (r"KH", "K"),
    (r"PH", "P"),
    (r"CHH", "CH"),
    (r"SH", "S"),
    (r"ZH", "L"),
    (r"CK", "K"),
    (r"(.)\1+", r"\1"),  # Collapse consecutive duplicate letters
]

def clean_and_normalize_unicode(text: Optional[str]) -> str:
    """
    Normalizes unicode, standardizes spacing, and removes non-word punctuation
    except internal dots used for initials.
    """
    if not text:
        return ""
    # Normalize unicode to NFKD
    normalized = unicodedata.normalize("NFKD", text)
    # Retain Latin/Indic letters, digits, spaces, and periods
    cleaned = re.sub(r"[^\w\s\.]", " ", normalized)
    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.upper()

def strip_honorifics(tokens: List[str]) -> List[str]:
    """
    Removes standard Indic and English honorific prefixes/suffixes.
    """
    return [t for t in tokens if t.lower().rstrip(".") not in HONORIFICS and len(t) > 0]

def indic_phonetic_transform(token: str) -> str:
    """
    Transforms English transliterated Indic name tokens into a phonetic key.
    E.g., SARIPILLY -> SARIPILLI -> SARIPILI
    """
    t = token.upper()
    for pattern, repl in INDIC_PHONETIC_REPLACEMENTS:
        t = re.sub(pattern, repl, t)
    return t

def check_initial_expansion(tokens_a: List[str], tokens_b: List[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Checks if a single-letter initial in one name expands to a full token in the other.
    E.g., ['S', 'RAKESH'] vs ['SARIPILLY', 'RAKESH'] -> True, 'S' -> 'SARIPILLY'
    """
    # Clean trailing dots
    a_clean = [t.rstrip(".") for t in tokens_a]
    b_clean = [t.rstrip(".") for t in tokens_b]

    # Look for single-letter initial in A matching start of a longer token in B
    for t_a in a_clean:
        if len(t_a) == 1:
            for t_b in b_clean:
                if len(t_b) > 1 and t_b.startswith(t_a):
                    return True, t_a, t_b

    # Look for single-letter initial in B matching start of a longer token in A
    for t_b in b_clean:
        if len(t_b) == 1:
            for t_a in a_clean:
                if len(t_a) > 1 and t_a.startswith(t_b):
                    return True, t_b, t_a

    return False, None, None

def reconcile_names(
    name_a: Optional[str],
    name_b: Optional[str],
    doc_a_type: str = "DOC_A",
    doc_b_type: str = "DOC_B",
    ocr_confidence_a: float = 1.0,
    ocr_confidence_b: float = 1.0
) -> Dict[str, Any]:
    """
    Comprehensive Indic name comparison algorithm:
    1. Unicode and whitespace normalization
    2. Honorific stripping
    3. Initial expansion detection
    4. Indic phonetic normalization
    5. Token sort & Levenshtein distance
    6. Discrepancy isolation (surname vs given name)
    7. Composite scoring and explainable status
    """
    norm_a = clean_and_normalize_unicode(name_a)
    norm_b = clean_and_normalize_unicode(name_b)

    if not norm_a or not norm_b:
        return {
            "status": "RED_MISMATCH",
            "composite_score": 0.0,
            "field_name": "full_name",
            "doc_a_type": doc_a_type,
            "doc_a_val": name_a,
            "doc_b_type": doc_b_type,
            "doc_b_val": name_b,
            "details": {
                "token_similarity": 0.0,
                "phonetic_similarity": 0.0,
                "initial_expanded": False,
                "explanation": "One or both document names are missing or unreadable."
            }
        }

    raw_tokens_a = [t for t in norm_a.split() if t]
    raw_tokens_b = [t for t in norm_b.split() if t]

    tokens_a = strip_honorifics(raw_tokens_a)
    tokens_b = strip_honorifics(raw_tokens_b)

    cleaned_str_a = " ".join(tokens_a)
    cleaned_str_b = " ".join(tokens_b)

    # 1. Exact match check
    min_ocr_conf = min(ocr_confidence_a, ocr_confidence_b)
    if cleaned_str_a == cleaned_str_b:
        status = "GREEN_MATCH"
        explanation = "Exact character match across both documents."
        if min_ocr_conf < 0.75:
            status = "YELLOW_REVIEW"
            explanation += f" Warning: Underlying OCR confidence is low ({int(min_ocr_conf * 100)}%). Manual verification advised."

        return {
            "status": status,
            "composite_score": 1.0,
            "field_name": "full_name",
            "doc_a_type": doc_a_type,
            "doc_a_val": name_a,
            "doc_b_type": doc_b_type,
            "doc_b_val": name_b,
            "details": {
                "token_similarity": 1.0,
                "phonetic_similarity": 1.0,
                "initial_expanded": False,
                "explanation": explanation
            }
        }

    # 2. Check for initial expansion
    has_initial, initial_char, expanded_token = check_initial_expansion(tokens_a, tokens_b)

    # 3. Phonetic transformation
    phonetic_tokens_a = [indic_phonetic_transform(t.rstrip(".")) for t in tokens_a]
    phonetic_tokens_b = [indic_phonetic_transform(t.rstrip(".")) for t in tokens_b]
    phonetic_str_a = " ".join(phonetic_tokens_a)
    phonetic_str_b = " ".join(phonetic_tokens_b)

    phonetic_sim = fuzz.token_sort_ratio(phonetic_str_a, phonetic_str_b) / 100.0
    token_sim = fuzz.token_sort_ratio(cleaned_str_a, cleaned_str_b) / 100.0
    lev_dist = distance.Levenshtein.normalized_similarity(cleaned_str_a, cleaned_str_b)

    # Weighted composite score
    composite_score = float(round((0.40 * token_sim) + (0.35 * phonetic_sim) + (0.25 * lev_dist), 4))

    # Check for surname divergence
    # If both have >= 2 tokens, compare the first token (often surname in South India)
    # or the token that is not the common given name.
    surname_divergence = False
    if len(tokens_a) >= 2 and len(tokens_b) >= 2:
        surname_a = tokens_a[0].rstrip(".")
        surname_b = tokens_b[0].rstrip(".")
        # If neither is a single letter initial
        if len(surname_a) > 1 and len(surname_b) > 1:
            surname_sim = fuzz.ratio(surname_a, surname_b) / 100.0
            surname_phonetic = fuzz.ratio(indic_phonetic_transform(surname_a), indic_phonetic_transform(surname_b)) / 100.0
            if surname_sim < 0.65 and surname_phonetic < 0.70:
                surname_divergence = True

    # Classification logic
    min_ocr_conf = min(ocr_confidence_a, ocr_confidence_b)

    if surname_divergence:
        status = "RED_MISMATCH"
        explanation = (
            f"Different surnames detected ('{tokens_a[0]}' vs '{tokens_b[0]}'). "
            f"Even though given names may match, different family surnames require official verification."
        )
    elif has_initial:
        status = "WARNING_INITIAL_EXPANSION"
        explanation = (
            f"Initial '{initial_char}.' on one document corresponds to expanded name '{expanded_token}'. "
            f"Non-material format variation, but may require volunteer/operator confirmation or self-declaration."
        )
    elif phonetic_sim >= 0.90:
        status = "GREEN_MATCH"
        explanation = (
            f"High phonetic equivalence ({int(phonetic_sim * 100)}%) between '{cleaned_str_a}' and '{cleaned_str_b}' "
            f"(common Indic transliteration variant, e.g. Y/I, V/W)."
        )
    elif composite_score >= 0.85:
        status = "YELLOW_REVIEW"
        explanation = (
            f"Moderate name similarity ({int(composite_score * 100)}%). Slight character or token order discrepancy."
        )
    else:
        status = "RED_MISMATCH"
        explanation = (
            f"Significant name difference detected ({int(composite_score * 100)}% similarity). "
            f"Please ensure both documents belong to the same applicant."
        )

    # Adjust for low OCR confidence if needed
    if min_ocr_conf < 0.75 and status == "GREEN_MATCH":
        status = "YELLOW_REVIEW"
        explanation += f" Warning: Underlying OCR confidence is low ({int(min_ocr_conf * 100)}%). Manual verification advised."

    return {
        "status": status,
        "composite_score": composite_score,
        "field_name": "full_name",
        "doc_a_type": doc_a_type,
        "doc_a_val": name_a,
        "doc_b_type": doc_b_type,
        "doc_b_val": name_b,
        "details": {
            "token_similarity": float(round(token_sim, 4)),
            "phonetic_similarity": float(round(phonetic_sim, 4)),
            "initial_expanded": bool(has_initial),
            "explanation": explanation
        }
    }
