from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List, Optional

import os
SCHEMES_FILE_DEFAULT = Path(__file__).resolve().parent.parent / "rules" / "schemes.json"

class SchemeRuleEngine:
    def __init__(self, schemes_file: Optional[Path] = None):
        env_path = os.getenv("RULES_FILE_PATH")
        if schemes_file:
            target_path = schemes_file
        elif env_path and Path(env_path).exists():
            target_path = Path(env_path)
        else:
            target_path = SCHEMES_FILE_DEFAULT
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {"version": "2026.1", "schemes": []}
        
        self.schemes_by_id = {s["id"]: s for s in self.config.get("schemes", [])}

    def get_scheme(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        return self.schemes_by_id.get(scheme_id)

    def evaluate_scheme(
        self,
        scheme_id: str,
        documents: List[Dict[str, Any]],
        current_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Evaluates documents against configured scheme requirements.
        Uses an injectable current_date for deterministic unit tests.
        """
        now = current_date or date.today()
        scheme = self.get_scheme(scheme_id)

        if not scheme:
            return {
                "scheme_found": False,
                "scheme_issues": [
                    {
                        "code": "UNKNOWN_SCHEME",
                        "severity": "ERROR",
                        "message": f"Requested scheme '{scheme_id}' is not in the configured catalog."
                    }
                ],
                "rule_version": self.config.get("version", "unknown"),
                "rule_source": "None",
                "rule_state": "UNVERIFIED"
            }

        issues: List[Dict[str, Any]] = []
        rule_state = scheme.get("verification_state", "UNVERIFIED")

        # 1. Unverified rule advisory
        if rule_state in ["DEMO_ONLY", "UNVERIFIED"]:
            issues.append({
                "code": "RULE_REQUIRES_CONFIRMATION",
                "severity": "WARNING",
                "doc_type": None,
                "message": (
                    f"Policy rules for '{scheme['display_name']}' are marked as {rule_state}. "
                    "Confirm current gazette requirements at your local MeeSeva centre."
                ),
                "rule_source": scheme.get("rule_source")
            })

        # 2. Check for missing required documents
        required_docs = scheme.get("required_documents", [])
        provided_doc_types = {d.get("doc_type") for d in documents if d.get("doc_type")}

        for req_doc in required_docs:
            if req_doc not in provided_doc_types:
                issues.append({
                    "code": "DOCUMENT_MISSING",
                    "severity": "ERROR",
                    "doc_type": req_doc,
                    "message": f"Mandatory document type '{req_doc}' is missing from the application set.",
                    "rule_source": scheme.get("rule_source")
                })

        # 3. Check document fields and validity periods
        field_reqs = scheme.get("field_requirements", {})
        for doc in documents:
            dtype = doc.get("doc_type")
            fields = doc.get("extracted_fields", {})
            if isinstance(fields, dict):
                f_dict = fields
            else:
                f_dict = fields.model_dump() if hasattr(fields, "model_dump") else {}

            # Specific rules for Income Certificate validity
            if dtype == "INCOME_CERT":
                max_months = field_reqs.get("INCOME_CERT", {}).get("max_age_months_validity", 12)
                issue_date_str = f_dict.get("issue_date")
                if issue_date_str:
                    try:
                        issue_dt = datetime.strptime(issue_date_str, "%Y-%m-%d").date()
                        age_days = (now - issue_dt).days
                        # Max validity in days approximate (months * 30.5)
                        max_days = int(max_months * 30.5)
                        if age_days > max_days:
                            issues.append({
                                "code": "CERT_EXPIRY",
                                "severity": "ERROR",
                                "doc_type": "INCOME_CERT",
                                "message": (
                                    f"Income certificate issue date ({issue_date_str}) is {age_days} days old, "
                                    f"exceeding the configured {max_months}-month validity window."
                                ),
                                "rule_source": scheme.get("rule_source")
                            })
                    except ValueError:
                        issues.append({
                            "code": "INVALID_DATE",
                            "severity": "WARNING",
                            "doc_type": "INCOME_CERT",
                            "message": f"Unable to parse issue date '{issue_date_str}' on Income Certificate.",
                            "rule_source": scheme.get("rule_source")
                        })
                else:
                    issues.append({
                        "code": "MISSING_FIELD",
                        "severity": "WARNING",
                        "doc_type": "INCOME_CERT",
                        "message": "Issue date could not be verified on Income Certificate.",
                        "rule_source": scheme.get("rule_source")
                    })

                # Income threshold check (only if rule is verified)
                max_income = field_reqs.get("INCOME_CERT", {}).get("max_annual_income_inr")
                ann_income = f_dict.get("annual_income_inr")
                if max_income and ann_income:
                    if ann_income > max_income:
                        issues.append({
                            "code": "INCOME_EXCEEDED",
                            "severity": "ERROR",
                            "doc_type": "INCOME_CERT",
                            "message": f"Annual income (₹{ann_income:,.0f}) exceeds scheme ceiling of ₹{max_income:,.0f}.",
                            "rule_source": scheme.get("rule_source")
                        })

            # Check age requirement if applicable (e.g. Aasara pension >= 57)
            if dtype == "IDENTITY_CARD":
                min_age = field_reqs.get("IDENTITY_CARD", {}).get("min_age_years")
                dob_str = f_dict.get("dob")
                if min_age and dob_str:
                    try:
                        dob_dt = datetime.strptime(dob_str, "%Y-%m-%d").date()
                        age_years = (now - dob_dt).days // 365
                        if age_years < min_age:
                            issues.append({
                                "code": "AGE_THRESHOLD_NOT_MET",
                                "severity": "ERROR",
                                "doc_type": "IDENTITY_CARD",
                                "message": f"Calculated age ({age_years} years) is below minimum age requirement of {min_age} years.",
                                "rule_source": scheme.get("rule_source")
                            })
                    except ValueError:
                        pass

        return {
            "scheme_found": True,
            "scheme_name": scheme.get("display_name", scheme_id),
            "scheme_issues": issues,
            "rule_version": scheme.get("config_version", self.config.get("version", "v1.0")),
            "rule_source": scheme.get("rule_source", "Telangana Portal"),
            "rule_state": rule_state
        }
