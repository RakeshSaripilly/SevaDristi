from __future__ import annotations
import os
import json
import uuid
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks

from backend.models.schemas import (
    VerificationResponse,
    DocumentAnalysis,
    ExtractedFields,
    FieldComparison,
    FieldComparisonDetail,
    QualityIssue,
    SchemeIssue,
    AdvisoryItem,
    SingleDocExtractionResponse,
    ClearSessionResponse
)
from backend.services.vision_gate import analyze_document_image
from backend.services.ocr_extractor import extract_fields_from_ocr, HAS_PYTESSERACT
from backend.services.reconciler import reconcile_names
from backend.services.rule_engine import SchemeRuleEngine
from backend.services.qr_bridge import generate_signed_qr_payload, generate_qr_image_data_url
from backend.services.privacy import (
    mask_aadhaar_string,
    mask_name_privacy,
    validate_image_file,
    scan_file_for_malware
)
from backend.services.metrics import (
    VISION_BLUR_SCORE,
    VISION_GLARE_RATIO,
    RECONCILER_SCORE,
    VERIFICATIONS_TOTAL
)
from backend.services.audit_logger import record_verification_log
from backend.services.cache import session_cache

logger = logging.getLogger("sevadristi.verify")
router = APIRouter(prefix="/api", tags=["Verification"])

ADVISORIES_PATH = Path(__file__).resolve().parent.parent / "locales" / "advisories.json"
rule_engine = SchemeRuleEngine()

def load_advisories() -> dict:
    if ADVISORIES_PATH.exists():
        with open(ADVISORIES_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("advisories", {})
    return {}

ADVISORY_CATALOG = load_advisories()

def resolve_advisory(advisory_id: str, lang: str, severity: str = "WARNING", category: str = "GENERAL") -> AdvisoryItem:
    adv_dict = ADVISORY_CATALOG.get(advisory_id, {})
    lang_content = adv_dict.get(lang) or adv_dict.get("te-IN") or adv_dict.get("en-IN") or {
        "title": advisory_id.replace("_", " ").title(),
        "description": "Please review this requirement before visiting the MeeSeva centre.",
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

@router.post("/extract-name-only", response_model=SingleDocExtractionResponse)
async def extract_name_only(
    document: UploadFile = File(...),
    doc_type_hint: Optional[str] = Form(None)
):
    """
    Rapid single document OCR & quality preview for real-time camera/upload check.
    Allows instant preview of blur score, glare ratio, and extracted name before full submission.
    """
    file_bytes = await document.read()

    # Step 1: Pillow signature check & malware gate
    is_valid_img, img_err = validate_image_file(file_bytes, document.filename)
    if not is_valid_img:
        raise HTTPException(status_code=400, detail=f"File rejected: {img_err}")

    is_clean, scan_err = scan_file_for_malware(file_bytes)
    if not is_clean:
        raise HTTPException(status_code=400, detail=f"Security violation: {scan_err}")

    # Step 2: Vision analysis
    try:
        vision_res = analyze_document_image(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing error: {str(e)}")

    # Step 3: OCR extraction
    ocr_fields, ocr_conf, ocr_status = extract_fields_from_ocr(
        vision_res["processed_image_bgr"],
        user_hint_type=doc_type_hint
    )

    if ocr_fields.get("id_reference"):
        ocr_fields["id_reference"] = mask_aadhaar_string(ocr_fields["id_reference"])

    candidate_name = ocr_fields.get("full_name")

    return SingleDocExtractionResponse(
        extracted_name=candidate_name,
        confidence=ocr_conf,
        doc_type=ocr_fields.get("doc_type", doc_type_hint or "IDENTITY_CARD"),
        quality={
            "blur_score": vision_res["blur_score"],
            "blur_threshold": vision_res["blur_threshold"],
            "is_blurred": vision_res["is_blurred"],
            "is_blurry": vision_res["is_blurred"],
            "glare_ratio": vision_res["glare_ratio"],
            "glare_threshold": vision_res["glare_threshold"],
            "has_glare": vision_res["has_glare"],
            "is_glare": vision_res["has_glare"],
            "crop_applied": vision_res["crop_applied"],
            "crop_suggested": vision_res["crop_applied"],
            "corners": vision_res.get("detected_corners")
        },
        preview_data_url=vision_res["preview_data_url"],
        extracted_fields=ocr_fields,
        advisories=vision_res.get("advisories", [])
    )

@router.post("/clear-session", response_model=ClearSessionResponse)
async def clear_session(session_id: str = Form(...)):
    """
    Purges ephemeral session cache upon user logout or manual reset.
    """
    session_cache.delete_session(session_id)
    return ClearSessionResponse(
        status="SUCCESS",
        session_id=session_id,
        message="Session state purged from cache."
    )

@router.post("/verify", response_model=VerificationResponse)
async def verify_documents(
    background_tasks: BackgroundTasks,
    documents: List[UploadFile] = File(default=[]),
    scheme_id: str = Form(default="epass_scholarship"),
    language: str = Form(default="te-IN"),
    doc_type_hints: Optional[str] = Form(default=None),
    user_edited_names: Optional[str] = Form(default=None)
):
    """
    100% Real User Pre-Verification Endpoint:
    - Strictly accepts actual document uploads (Zero synthetic presets).
    - In-memory processing via io.BytesIO (Zero disk writes).
    - Image quality assessment (Laplacian blur variance + HSV glare).
    - Tesseract multilingual OCR with deskewing & adaptive thresholding.
    - Indic name reconciliation with Telugu transliteration handling.
    - Welfare policy validation (issue date age, income ceiling).
    - Cryptographically signed HMAC-SHA256 QR code generation.
    """
    session_id = f"ephem-{uuid.uuid4().hex[:8]}"
    advisory_items: List[AdvisoryItem] = []
    quality_issues: List[QualityIssue] = []
    analyzed_docs: List[DocumentAnalysis] = []
    field_comparisons: List[FieldComparison] = []

    if not documents:
        raise HTTPException(
            status_code=400,
            detail="No document images provided. Please capture or upload real documents."
        )

    # Parse optional doc type hints (e.g. ['IDENTITY_CARD', 'INCOME_CERT'])
    hints_list: List[str] = []
    if doc_type_hints:
        try:
            parsed = json.loads(doc_type_hints)
            if isinstance(parsed, list):
                hints_list = parsed
        except Exception:
            pass

    # Parse optional user-edited names dictionary
    edited_names_dict: Dict[str, str] = {}
    if user_edited_names:
        try:
            parsed_names = json.loads(user_edited_names)
            if isinstance(parsed_names, dict):
                edited_names_dict = parsed_names
        except Exception:
            pass

    for idx, doc_file in enumerate(documents):
        file_bytes = await doc_file.read()
        type_hint = hints_list[idx] if idx < len(hints_list) else None

        # Step 1: File size and Pillow signature magic validation
        is_valid_img, img_err = validate_image_file(file_bytes, doc_file.filename)
        if not is_valid_img:
            raise HTTPException(status_code=400, detail=f"File '{doc_file.filename}' rejected: {img_err}")

        # Step 2: Virus/Malware scan gate
        is_clean, scan_err = scan_file_for_malware(file_bytes)
        if not is_clean:
            raise HTTPException(status_code=400, detail=f"Security violation in '{doc_file.filename}': {scan_err}")

        # Step 3: In-memory vision gate analysis (never saved to disk)
        try:
            vision_res = analyze_document_image(file_bytes)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process image '{doc_file.filename}': {str(e)}")

        VISION_BLUR_SCORE.observe(vision_res["blur_score"])
        VISION_GLARE_RATIO.observe(vision_res["glare_ratio"])

        # Step 4: Real OCR extraction
        ocr_fields, ocr_conf, ocr_status = extract_fields_from_ocr(
            vision_res["processed_image_bgr"],
            user_hint_type=type_hint
        )

        detected_doc_type = ocr_fields.get("doc_type", type_hint or "IDENTITY_CARD")

        # Step 5: Check if citizen corrected this document's name
        user_corrected = False
        doc_id = f"doc_{idx + 1}_{uuid.uuid4().hex[:4]}"
        if detected_doc_type in edited_names_dict:
            ocr_fields["full_name"] = edited_names_dict[detected_doc_type].strip().upper()
            user_corrected = True
        elif doc_id in edited_names_dict:
            ocr_fields["full_name"] = edited_names_dict[doc_id].strip().upper()
            user_corrected = True

        # Mask identity numbers immediately
        if ocr_fields.get("id_reference"):
            ocr_fields["id_reference"] = mask_aadhaar_string(ocr_fields["id_reference"])

        doc_analysis = DocumentAnalysis(
            id=doc_id,
            doc_type=detected_doc_type,
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
            user_corrected=user_corrected,
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

        if ocr_conf < 0.60 and HAS_PYTESSERACT:
            advisory_items.append(resolve_advisory("OCR_UNCERTAIN", language, "WARNING", "EXTRACTION"))

    # Step 6: Indic Name Reconciliation across documents
    name_docs = [
        (d.doc_type, d.extracted_fields.full_name, d.ocr_confidence)
        for d in analyzed_docs
        if d.extracted_fields.full_name
    ]
    for i in range(len(name_docs)):
        for j in range(i + 1, len(name_docs)):
            type_a, name_a, conf_a = name_docs[i]
            type_b, name_b, conf_b = name_docs[j]
            recon = reconcile_names(name_a, name_b, type_a, type_b, conf_a, conf_b)
            RECONCILER_SCORE.observe(recon["composite_score"])
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

    # Step 7: Scheme Rule Engine evaluation
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
        elif si.code == "INCOME_EXCEEDED":
            advisory_items.append(resolve_advisory("INCOME_EXCEEDED", language, "ERROR", "SCHEME_RULES"))

    # Step 8: Overall Status Determination
    has_errors = any(i.severity == "ERROR" for i in scheme_issues) or any(fc.status == "RED_MISMATCH" for fc in field_comparisons)
    has_warnings = (
        any(i.severity == "WARNING" for i in scheme_issues)
        or any(fc.status in ["WARNING_INITIAL_EXPANSION", "YELLOW_REVIEW"] for fc in field_comparisons)
        or any(q.severity == "WARNING" for q in quality_issues)
    )

    overall_status = "ACTION_REQUIRED" if has_errors else ("NEEDS_REVIEW" if has_warnings else "NO_ISSUES_DETECTED")
    VERIFICATIONS_TOTAL.labels(status=overall_status, scheme_id=scheme_id, processing_mode="real").inc()

    # Step 9: Generate Signed QR code
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

    # Step 10: Cache session in Redis & record non-PII audit log
    session_cache.set_session(session_id, {
        "scheme_id": scheme_id,
        "overall_status": overall_status,
        "processing_mode": "real"
    })
    background_tasks.add_task(
        record_verification_log,
        session_id=session_id,
        scheme_id=scheme_id,
        overall_status=overall_status,
        processing_mode="real"
    )

    limitations = [
        "In-memory stream processing only: No personal data or raw document images are ever persisted to disk.",
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
