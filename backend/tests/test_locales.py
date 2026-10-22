import json
from pathlib import Path
import pytest

LOCALES = [
    "en-IN", "hi-IN", "te-IN", "ta-IN", "kn-IN", "ml-IN",
    "mr-IN", "bn-IN", "gu-IN", "or-IN", "pa-IN", "as-IN"
]

def test_backend_advisories_completeness():
    advisories_path = Path(__file__).resolve().parent.parent / "locales" / "advisories.json"
    assert advisories_path.exists()
    with open(advisories_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    advisories = data.get("advisories", {})
    assert len(advisories) >= 6

    for code, lang_dict in advisories.items():
        for loc in LOCALES:
            assert loc in lang_dict, f"Missing locale '{loc}' in advisory '{code}'"
            item = lang_dict[loc]
            assert item.get("title") and len(item["title"].strip()) > 0
            assert item.get("description") and len(item["description"].strip()) > 0
            assert item.get("action") and len(item["action"].strip()) > 0

def test_frontend_locales_key_parity():
    frontend_locales_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "locales"
    assert frontend_locales_dir.exists()

    en_path = frontend_locales_dir / "en-IN.json"
    assert en_path.exists()
    with open(en_path, "r", encoding="utf-8") as f:
        en_keys = json.load(f)

    for loc in LOCALES:
        loc_path = frontend_locales_dir / f"{loc}.json"
        assert loc_path.exists(), f"Locale file '{loc}.json' does not exist."
        with open(loc_path, "r", encoding="utf-8") as f:
            loc_data = json.load(f)

        for k, v in en_keys.items():
            assert k in loc_data, f"Missing key '{k}' in frontend locale '{loc}.json'"
            assert loc_data[k] is not None and len(str(loc_data[k]).strip()) > 0, f"Empty value for '{k}' in '{loc}.json'"
