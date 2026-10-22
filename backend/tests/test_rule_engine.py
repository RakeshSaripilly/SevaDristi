from datetime import date
import pytest
from backend.services.rule_engine import SchemeRuleEngine

@pytest.fixture
def engine():
    return SchemeRuleEngine()

def test_missing_required_document(engine):
    """
    ePASS requires IDENTITY_CARD, CASTE_CERT, INCOME_CERT, BANK_PASSBOOK.
    Providing only IDENTITY_CARD and BANK_PASSBOOK must flag DOCUMENT_MISSING.
    """
    docs = [
        {"doc_type": "IDENTITY_CARD", "extracted_fields": {"full_name": "SARIPILLY RAKESH"}},
        {"doc_type": "BANK_PASSBOOK", "extracted_fields": {"full_name": "SARIPILLY RAKESH"}}
    ]
    res = engine.evaluate_scheme("epass_scholarship", docs)
    issue_codes = [i["code"] for i in res["scheme_issues"]]
    assert "DOCUMENT_MISSING" in issue_codes

def test_certificate_validity_with_injected_clock(engine):
    """
    Income certificate issue date 2024-05-10 evaluated against 2026-03-01 (> 12 months)
    must trigger CERT_EXPIRY.
    """
    docs = [
        {"doc_type": "IDENTITY_CARD", "extracted_fields": {"full_name": "SARIPILLY RAKESH"}},
        {"doc_type": "CASTE_CERT", "extracted_fields": {"full_name": "SARIPILLY RAKESH"}},
        {"doc_type": "BANK_PASSBOOK", "extracted_fields": {"full_name": "SARIPILLY RAKESH"}},
        {"doc_type": "INCOME_CERT", "extracted_fields": {"full_name": "SARIPILLY RAKESH", "issue_date": "2024-05-10", "annual_income_inr": 100000}}
    ]
    fixed_clock = date(2026, 3, 1)
    res = engine.evaluate_scheme("epass_scholarship", docs, current_date=fixed_clock)
    issue_codes = [i["code"] for i in res["scheme_issues"]]
    assert "CERT_EXPIRY" in issue_codes

    # Evaluated shortly after issue date (e.g. 2024-08-01) should NOT trigger expiry
    valid_clock = date(2024, 8, 1)
    res_valid = engine.evaluate_scheme("epass_scholarship", docs, current_date=valid_clock)
    issue_codes_valid = [i["code"] for i in res_valid["scheme_issues"]]
    assert "CERT_EXPIRY" not in issue_codes_valid

def test_income_threshold_exceeded(engine):
    """
    Income of 2,50,000 exceeds ceiling of 2,00,000 for ePASS.
    """
    docs = [
        {"doc_type": "INCOME_CERT", "extracted_fields": {"annual_income_inr": 250000, "issue_date": "2026-01-01"}}
    ]
    res = engine.evaluate_scheme("epass_scholarship", docs, current_date=date(2026, 2, 1))
    issue_codes = [i["code"] for i in res["scheme_issues"]]
    assert "INCOME_EXCEEDED" in issue_codes

def test_unverified_scheme_flagging(engine):
    """
    Rythu Bharosa is DEMO_ONLY; must return RULE_REQUIRES_CONFIRMATION.
    """
    docs = [
        {"doc_type": "IDENTITY_CARD", "extracted_fields": {"full_name": "SARIPILLY RAKESH"}},
        {"doc_type": "LAND_PASSBOOK", "extracted_fields": {"full_name": "SARIPILLY RAKESH"}},
        {"doc_type": "BANK_PASSBOOK", "extracted_fields": {"full_name": "SARIPILLY RAKESH"}}
    ]
    res = engine.evaluate_scheme("rythu_bharosa", docs)
    assert res["rule_state"] == "DEMO_ONLY"
    issue_codes = [i["code"] for i in res["scheme_issues"]]
    assert "RULE_REQUIRES_CONFIRMATION" in issue_codes
