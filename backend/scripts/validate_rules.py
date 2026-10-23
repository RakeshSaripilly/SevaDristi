#!/usr/bin/env python3
"""
Schemes Rule Validation Script
Validates rule provenance, schema integrity, and verification status for Telangana welfare rules.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

ALLOWED_VERIFICATION_STATES = {"VERIFIED", "UNVERIFIED", "DEMO_ONLY"}

def validate_schemes_file(file_path: Path) -> bool:
    print(f"[*] Validating schemes rule catalog: {file_path}")
    if not file_path.exists():
        print(f"[ERROR] Schemes rule file not found at: {file_path}")
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] JSON decode error: {e}")
        return False

    version = data.get("version")
    if not version:
        print("[ERROR] Missing root 'version' field.")
        return False

    schemes = data.get("schemes")
    if not isinstance(schemes, list) or len(schemes) == 0:
        print("[ERROR] 'schemes' must be a non-empty list.")
        return False

    errors = []
    for idx, s in enumerate(schemes):
        sid = s.get("id", f"index_{idx}")
        # Required fields
        for field in ["id", "display_name", "jurisdiction", "verification_state", "rule_source", "required_documents"]:
            if not s.get(field):
                errors.append(f"Scheme '{sid}' missing required field '{field}'.")

        # Verification state check
        vstate = s.get("verification_state")
        if vstate not in ALLOWED_VERIFICATION_STATES:
            errors.append(f"Scheme '{sid}' invalid verification_state '{vstate}'. Must be one of {ALLOWED_VERIFICATION_STATES}.")

        # Date validation
        lvd = s.get("last_verified_date")
        if lvd:
            try:
                datetime.strptime(lvd, "%Y-%m-%d")
            except ValueError:
                errors.append(f"Scheme '{sid}' has invalid last_verified_date format '{lvd}', expected YYYY-MM-DD.")

        # Required documents
        req_docs = s.get("required_documents", [])
        if not isinstance(req_docs, list) or len(req_docs) == 0:
            errors.append(f"Scheme '{sid}' required_documents must be a non-empty list.")

    if errors:
        print(f"[FAIL] Found {len(errors)} validation error(s):")
        for err in errors:
            print(f"  - {err}")
        return False

    print(f"[SUCCESS] All {len(schemes)} scheme rules validated successfully (Catalog Version: {version}).")
    return True

if __name__ == "__main__":
    target = os.getenv("RULES_FILE_PATH")
    path = Path(target) if target else Path(__file__).resolve().parent.parent / "rules" / "schemes.json"
    ok = validate_schemes_file(path)
    sys.exit(0 if ok else 1)
