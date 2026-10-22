from __future__ import annotations
import json
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.models.schemas import (
    VerificationResponse,
    DocumentAnalysis,
    ExtractedFields,
    FieldComparison,
    FieldComparisonDetail,
    QualityIssue,
    SchemeIssue,
    AdvisoryItem
)
from backend.services.vision_gate import analyze_document_image
from backend.services.ocr_extractor import extract_fields_from_ocr, HAS_PYTESSERACT
from backend.services.reconciler import reconcile_names
from backend.services.rule_engine import SchemeRuleEngine
from backend.services.qr_bridge import generate_signed_qr_payload, generate_qr_image_data_url
from backend.services.privacy import mask_aadhaar_string, mask_name_privacy

router = APIRouter(prefix="/api", tags=["Verification"])

SYNTHETIC_CASES_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "synthetic_cases.json"
ADVISORIES_PATH = Path(__file__).resolve().parent.parent / "locales" / "advisories.json"

rule_engine = SchemeRuleEngine()

def load_advisories() -> dict:
    if ADVISORIES_PATH.exists():
        with open(ADVISORIES_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("advisories", {})
    return {}

def load_synthetic_presets() -> dict:
    if SYNTHETIC_CASES_PATH.exists():
        with open(SYNTHETIC_CASES_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("presets", {})
    return {}

ADVISORY_CATALOG = load_advisories()
SYNTHETIC_PRESETS = load_synthetic_presets()

def resolve_advisory(advisory_id: str, lang: str, severity: str = "WARNING", category: str = "GENERAL") -> AdvisoryItem:
    adv_dict = ADVISORY_CATALOG.get(advisory_id, {})
    lang_content = adv_dict.get(lang) or adv_dict.get("en-IN") or {
        "title": advisory_id.replace("_", " ").title(),
        "description": "Please review this requirement before proceeding.",
        "action": "Ensure documents meet official guidelines."
    }
    return AdvisoryItem(
        id=advisory_id,
        category=category,
        severity=severity,
        title=lang_content["title"],
        description=lang_content["description"],
        actionable_step=lang_content["action"]
    )

@router.post("/verify", response_model=VerificationResponse)
async def verify_documents(
    documents: List[UploadFile] = File(default=[]),
    scheme_id: str = Form(default="epass_scholarship"),
    language: str = Form(default="en-IN"),
    demo_preset: Optional[str] = Form(default=None),
    simulation_enabled: Optional[bool] = Form(default=False)
):
    session_id = f"ephem-{uuid.uuid4().hex[:8]}"
    advisory_items: List[AdvisoryItem] = []
    quality_issues: List[QualityIssue] = []
    analyzed_docs: List[DocumentAnalysis] = []
    field_comparisons: List[FieldComparison] = []
    
    # -------------------------------------------------------------
    # 1. Preset / Synthetic Demo Flow
    # -------------------------------------------------------------
    if demo_preset and demo_preset in SYNTHETIC_PRESETS:
        preset_data = SYNTHETIC_PRESETS[demo_preset]
        target_scheme_id = preset_data.get("scheme_id", scheme_id)
        
        # Build DocumentAnalysis objects from synthetic fixture
        for d in preset_data.get("documents", []):
            ext_f = d.get("extracted_fields", {})
            # Mask identity card numbers
            if ext_f.get("id_reference") and d.get("doc_type") == "IDENTITY_CARD":
                ext_f["id_reference"] = mask_aadhaar_string(ext_f["id_reference"])

            doc_analysis = DocumentAnalysis(
                id=d["id"],
                doc_type=d["doc_type"],
                doc_name=d.get("doc_name"),
                blur_score=d.get("blur_score", 200.0),
                blur_threshold=d.get("blur_threshold", 110.0),
                is_blurred=d.get("is_blurred", False),
                glare_ratio=d.get("glare_ratio", 0.02),
                glare_threshold=d.get("glare_threshold", 0.08),
                has_glare=d.get("has_glare", False),
                crop_applied=d.get("crop_applied", True),
                possible_seal_detected=d.get("possible_seal_detected", False),
                possible_signature_detected=d.get("possible_signature_detected", True),
                seal_signature_method="synthetic_demo_fixture",
                extracted_fields=ExtractedFields(**ext_f),
                ocr_confidence=d.get("ocr_confidence", 0.95),
                preview_data_url=None,
                user_corrected=False,
                processing_notes=["Synthetic demonstration fixture record."]
            )
            analyzed_docs.append(doc_analysis)

            # Quality issues
            if doc_analysis.is_blurred:
                quality_issues.append(QualityIssue(
                    code="IMAGE_BLUR",
                    severity="WARNING",
                    doc_id=doc_analysis.id,
                    doc_type=doc_analysis.doc_type,
                    message=f"Document image sharpness ({doc_analysis.blur_score:.1f}) below threshold ({doc_analysis.blur_threshold:.1f}).",
                    metric_value=doc_analysis.blur_score,
                    threshold=doc_analysis.blur_threshold
                ))
                advisory_items.append(resolve_advisory("IMAGE_BLUR", language, "WARNING", "IMAGE_QUALITY"))

            if doc_analysis.has_glare:
                quality_issues.append(QualityIssue(
                    code="IMAGE_GLARE",
                    severity="WARNING",
                    doc_id=doc_analysis.id,
                    doc_type=doc_analysis.doc_type,
                    message=f"Glare reflection ratio ({doc_analysis.glare_ratio * 100:.1f}%) exceeds threshold ({doc_analysis.glare_threshold * 100:.1f}%).",
                    metric_value=doc_analysis.glare_ratio,
                    threshold=doc_analysis.glare_threshold
                ))
                advisory_items.append(resolve_advisory("IMAGE_GLARE", language, "WARNING", "IMAGE_QUALITY"))

            if not doc_analysis.possible_seal_detected and doc_analysis.doc_type in ["INCOME_CERT", "CASTE_CERT"]:
                advisory_items.append(resolve_advisory("SEAL_UNCERTAIN", language, "INFO", "DOCUMENT_INTEGRITY"))

        # Reconcile names across documents
        name_docs = [(d.doc_type, d.extracted_fields.full_name, d.ocr_confidence) for d in analyzed_docs if d.extracted_fields.full_name]
        for i in range(len(name_docs)):
            for j in range(i + 1, len(name_docs)):
                type_a, name_a, conf_a = name_docs[i]
                type_b, name_b, conf_b = name_docs[j]
                recon = reconcile_names(name_a, name_b, type_a, type_b, conf_a, conf_b)
                fc = FieldComparison(
                    field_name="full_name",
                    doc_a_type=type_a,
                    doc_a_val=name_a,
                    doc_b_type=type_b,
                    doc_b_val=name_b,
                    status=recon["status"],
                    composite_score=recon["composite_score"],
                    details=FieldComparisonDetail(**recon["details"])
                )
                field_comparisons.append(fc)

                if recon["status"] == "WARNING_INITIAL_EXPANSION":
                    advisory_items.append(resolve_advisory("INITIAL_EXPANSION", language, "WARNING", "NAME_MATCHING"))
                elif recon["status"] == "RED_MISMATCH":
                    advisory_items.append(resolve_advisory("NAME_MISMATCH", language, "ERROR", "NAME_MATCHING"))

        # Evaluate Scheme rules
        doc_dicts = [
            {"doc_type": d.doc_type, "extracted_fields": d.extracted_fields.model_dump()}
            for d in analyzed_docs
        ]
        eval_res = rule_engine.evaluate_scheme(target_scheme_id, doc_dicts)
        scheme_issues = [SchemeIssue(**si) for si in eval_res.get("scheme_issues", [])]

        for si in scheme_issues:
            if si.code == "CERT_EXPIRY":
                advisory_items.append(resolve_advisory("CERT_EXPIRY", language, "ERROR", "SCHEME_RULES"))
            elif si.code == "DOCUMENT_MISSING":
                advisory_items.append(resolve_advisory("DOCUMENT_MISSING", language, "ERROR", "SCHEME_RULES"))
            elif si.code == "RULE_REQUIRES_CONFIRMATION":
                advisory_items.append(resolve_advisory("RULE_REQUIRES_CONFIRMATION", language, "WARNING", "SCHEME_RULES"))

        # Determine overall status
        has_errors = any(i.severity == "ERROR" for i in scheme_issues) or any(fc.status == "RED_MISMATCH" for fc in field_comparisons)
        has_warnings = (
            any(i.severity == "WARNING" for i in scheme_issues)
            or any(fc.status in ["WARNING_INITIAL_EXPANSION", "YELLOW_REVIEW"] for fc in field_comparisons)
            or any(q.severity == "WARNING" for q in quality_issues)
        )

        overall_status = "ACTION_REQUIRED" if has_errors else ("NEEDS_REVIEW" if has_warnings else "NO_ISSUES_DETECTED")

        # Generate Pre-Verification Summary QR
        verified_name = analyzed_docs[0].extracted_fields.full_name if analyzed_docs else None
        qr_payload = generate_signed_qr_payload(
            session_id=session_id,
            scheme_id=target_scheme_id,
            overall_status=overall_status,
            verified_fields={
                "nam": mask_name_privacy(verified_name),
                "dob_yr": (analyzed_docs[0].extracted_fields.dob or "")[:4],
                "pin": analyzed_docs[0].extracted_fields.pincode or "500032",
                "cnt": len(analyzed_docs)
            },
            warnings=[a.id for a in advisory_items if a.severity in ["WARNING", "ERROR"]]
        )
        qr_data_url = generate_qr_image_data_url(qr_payload)

        # De-duplicate advisories by ID
        unique_advisories = {a.id: a for a in advisory_items}

        return VerificationResponse(
            session_id=session_id,
            processing_mode="demo",
            overall_status=overall_status,
            scheme_id=target_scheme_id,
            scheme_name=eval_res.get("scheme_name", target_scheme_id),
            documents=analyzed_docs,
            field_comparisons=field_comparisons,
            quality_issues=quality_issues,
            scheme_issues=scheme_issues,
            advisories=list(unique_advisories.values()),
            rule_version=eval_res.get("rule_version", "v1.0"),
            rule_source=eval_res.get("rule_source", "Telangana MeeSeva"),
            rule_state=eval_res.get("rule_state", "VERIFIED"),
            qr_available=True,
            qr_payload=qr_payload,
            qr_data_url=qr_data_url,
            limitations=[
                "SIMULATED RESULT: Generated from synthetic demo fixtures.",
                "Pre-verification advisory only; final determination rests with MeeSeva / CSC authority."
            ]
        )

    # -------------------------------------------------------------
    # 2. Live Document Processing Flow
    # -------------------------------------------------------------
    if not documents:
        raise HTTPException(
            status_code=400,
            detail="No document images provided. Please upload documents or select a synthetic demo preset."
        )

    for idx, doc_file in enumerate(documents):
        # Validate MIME type and file size (max 10MB)
        if doc_file.content_type not in ["image/jpeg", "image/png", "image/webp", "image/jpg"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format '{doc_file.content_type}'. Upload JPEG, PNG, or WEBP.")

        file_bytes = await doc_file.read()
        if len(file_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")

        # In-memory vision gate analysis
        try:
            vision_res = analyze_document_image(file_bytes)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decode image '{doc_file.filename}': {str(e)}")

        # OCR extraction
        ocr_fields, ocr_conf, ocr_status = extract_fields_from_ocr(vision_res["processed_image_bgr"])
        
        # Mask identity numbers immediately
        if ocr_fields.get("id_reference"):
            ocr_fields["id_reference"] = mask_aadhaar_string(ocr_fields["id_reference"])

        doc_analysis = DocumentAnalysis(
            id=f"doc_{idx + 1}_{uuid.uuid4().hex[:4]}",
            doc_type=ocr_fields.get("doc_type", "IDENTITY_CARD"),
            doc_name=doc_file.filename,
            blur_score=vision_res["blur_score"],
            blur_threshold=vision_res["blur_threshold"],
            is_blurred=vision_res["is_blurred"],
            glare_ratio=vision_res["glare_ratio"],
            glare_threshold=vision_res["glare_threshold"],
            has_glare=vision_res["has_glare"],
            crop_applied=vision_res["crop_applied"],
            possible_seal_detected=vision_res["possible_seal_detected"],
            possible_signature_detected=vision_res["possible_signature_detected"],
            seal_signature_method="color_contour_heuristic",
            extracted_fields=ExtractedFields(**ocr_fields),
            ocr_confidence=ocr_conf,
            preview_data_url=vision_res["preview_data_url"],
            user_corrected=False,
            processing_notes=[vision_res["crop_note"], ocr_status]
        )
        analyzed_docs.append(doc_analysis)

        # Vision quality issues
        if doc_analysis.is_blurred:
            quality_issues.append(QualityIssue(
                code="IMAGE_BLUR",
                severity="WARNING",
                doc_id=doc_analysis.id,
                doc_type=doc_analysis.doc_type,
                message=f"Image sharpness score ({doc_analysis.blur_score:.1f}) is below readable threshold ({doc_analysis.blur_threshold:.1f}).",
                metric_value=doc_analysis.blur_score,
                threshold=doc_analysis.blur_threshold
            ))
            advisory_items.append(resolve_advisory("IMAGE_BLUR", language, "WARNING", "IMAGE_QUALITY"))

        if doc_analysis.has_glare:
            quality_issues.append(QualityIssue(
                code="IMAGE_GLARE",
                severity="WARNING",
                doc_id=doc_analysis.id,
                doc_type=doc_analysis.doc_type,
                message=f"Light glare ({doc_analysis.glare_ratio * 100:.1f}%) detected on document surface.",
                metric_value=doc_analysis.glare_ratio,
                threshold=doc_analysis.glare_threshold
            ))
            advisory_items.append(resolve_advisory("IMAGE_GLARE", language, "WARNING", "IMAGE_QUALITY"))

        if ocr_conf < 0.70 and HAS_PYTESSERACT:
            advisory_items.append(resolve_advisory("OCR_UNCERTAIN", language, "WARNING", "EXTRACTION"))

    # Reconcile names between docs
    name_docs = [(d.doc_type, d.extracted_fields.full_name, d.ocr_confidence) for d in analyzed_docs if d.extracted_fields.full_name]
    for i in range(len(name_docs)):
        for j in range(i + 1, len(name_docs)):
            type_a, name_a, conf_a = name_docs[i]
            type_b, name_b, conf_b = name_docs[j]
            recon = reconcile_names(name_a, name_b, type_a, type_b, conf_a, conf_b)
            fc = FieldComparison(
                field_name="full_name",
                doc_a_type=type_a,
                doc_a_val=name_a,
                doc_b_type=type_b,
                doc_b_val=name_b,
                status=recon["status"],
                composite_score=recon["composite_score"],
                details=FieldComparisonDetail(**recon["details"])
            )
            field_comparisons.append(fc)

            if recon["status"] == "WARNING_INITIAL_EXPANSION":
                advisory_items.append(resolve_advisory("INITIAL_EXPANSION", language, "WARNING", "NAME_MATCHING"))
            elif recon["status"] == "RED_MISMATCH":
                advisory_items.append(resolve_advisory("NAME_MISMATCH", language, "ERROR", "NAME_MATCHING"))

    # Scheme rule checks
    doc_dicts = [
        {"doc_type": d.doc_type, "extracted_fields": d.extracted_fields.model_dump()}
        for d in analyzed_docs
    ]
    eval_res = rule_engine.evaluate_scheme(scheme_id, doc_dicts)
    scheme_issues = [SchemeIssue(**si) for si in eval_res.get("scheme_issues", [])]

    for si in scheme_issues:
        if si.code == "CERT_EXPIRY":
            advisory_items.append(resolve_advisory("CERT_EXPIRY", language, "ERROR", "SCHEME_RULES"))
        elif si.code == "DOCUMENT_MISSING":
            advisory_items.append(resolve_advisory("DOCUMENT_MISSING", language, "ERROR", "SCHEME_RULES"))
        elif si.code == "RULE_REQUIRES_CONFIRMATION":
            advisory_items.append(resolve_advisory("RULE_REQUIRES_CONFIRMATION", language, "WARNING", "SCHEME_RULES"))

    has_errors = any(i.severity == "ERROR" for i in scheme_issues) or any(fc.status == "RED_MISMATCH" for fc in field_comparisons)
    has_warnings = (
        any(i.severity == "WARNING" for i in scheme_issues)
        or any(fc.status in ["WARNING_INITIAL_EXPANSION", "YELLOW_REVIEW"] for fc in field_comparisons)
        or any(q.severity == "WARNING" for q in quality_issues)
    )

    overall_status = "ACTION_REQUIRED" if has_errors else ("NEEDS_REVIEW" if has_warnings else "NO_ISSUES_DETECTED")

    # Generate QR
    verified_name = analyzed_docs[0].extracted_fields.full_name if analyzed_docs else None
    qr_payload = generate_signed_qr_payload(
        session_id=session_id,
        scheme_id=scheme_id,
        overall_status=overall_status,
        verified_fields={
            "nam": mask_name_privacy(verified_name),
            "dob_yr": (analyzed_docs[0].extracted_fields.dob or "")[:4],
            "pin": analyzed_docs[0].extracted_fields.pincode or "",
            "cnt": len(analyzed_docs)
        },
        warnings=[a.id for a in advisory_items if a.severity in ["WARNING", "ERROR"]]
    )
    qr_data_url = generate_qr_image_data_url(qr_payload)

    unique_advisories = {a.id: a for a in advisory_items}

    limitations = [
        "In-memory processing only: No personal data or document images are written to persistent storage.",
        "Pre-verification heuristic tool only. Final application acceptance is determined by official MeeSeva personnel."
    ]
    if not HAS_PYTESSERACT:
        limitations.append("Local OCR engine not detected on system PATH. Extracted fields may require manual entry.")

    return VerificationResponse(
        session_id=session_id,
        processing_mode="real",
        overall_status=overall_status,
        scheme_id=scheme_id,
        scheme_name=eval_res.get("scheme_name", scheme_id),
        documents=analyzed_docs,
        field_comparisons=field_comparisons,
        quality_issues=quality_issues,
        scheme_issues=scheme_issues,
        advisories=list(unique_advisories.values()),
        rule_version=eval_res.get("rule_version", "v1.0"),
        rule_source=eval_res.get("rule_source", "Telangana Portal"),
        rule_state=eval_res.get("rule_state", "VERIFIED"),
        qr_available=True,
        qr_payload=qr_payload,
        qr_data_url=qr_data_url,
        limitations=limitations
    )
