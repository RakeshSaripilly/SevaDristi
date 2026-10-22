import pytest
from backend.services.reconciler import (
    reconcile_names,
    clean_and_normalize_unicode,
    strip_honorifics,
    indic_phonetic_transform,
    check_initial_expansion
)

def test_case_a_phonetic_variation():
    """
    SARIPILLY RAKESH vs SARIPILLI RAKESH:
    Expected: GREEN_MATCH with high phonetic similarity.
    """
    res = reconcile_names("SARIPILLY RAKESH", "SARIPILLI RAKESH")
    assert res["status"] == "GREEN_MATCH"
    assert res["details"]["phonetic_similarity"] >= 0.90
    assert res["composite_score"] >= 0.90

def test_case_b_initial_expansion():
    """
    S. RAKESH vs SARIPILLY RAKESH:
    Expected: WARNING_INITIAL_EXPANSION.
    """
    res = reconcile_names("S. RAKESH", "SARIPILLY RAKESH")
    assert res["status"] == "WARNING_INITIAL_EXPANSION"
    assert res["details"]["initial_expanded"] is True

def test_case_c_different_surname():
    """
    SARIPILLY RAKESH vs KONDAPALLI RAKESH:
    Expected: RED_MISMATCH due to surname discrepancy.
    """
    res = reconcile_names("SARIPILLY RAKESH", "KONDAPALLI RAKESH")
    assert res["status"] == "RED_MISMATCH"
    assert "Different surnames" in res["details"]["explanation"]

def test_normalization_and_honorifics():
    """
    Tests Unicode normalization, case-insensitivity, and honorific stripping.
    """
    res = reconcile_names("Sri. RAKESH SARIPILLY", "rakesh saripilly")
    assert res["status"] == "GREEN_MATCH"
    assert res["composite_score"] >= 0.95

def test_low_confidence_ocr_warning():
    """
    Low-confidence OCR should downgrade GREEN_MATCH to YELLOW_REVIEW with advisory.
    """
    res = reconcile_names("SARIPILLY RAKESH", "SARIPILLY RAKESH", ocr_confidence_a=0.55)
    assert res["status"] == "YELLOW_REVIEW"
    assert "OCR confidence is low" in res["details"]["explanation"]

def test_empty_and_malformed_names():
    """
    Empty and malformed inputs should safely return RED_MISMATCH without crashing.
    """
    res1 = reconcile_names("", "SARIPILLY RAKESH")
    assert res1["status"] == "RED_MISMATCH"

    res2 = reconcile_names(None, None)
    assert res2["status"] == "RED_MISMATCH"

    res3 = reconcile_names("   ", "   ")
    assert res3["status"] == "RED_MISMATCH"
