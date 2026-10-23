from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class ExtractedFields(BaseModel):
    full_name: Optional[str] = None
    guardian_name: Optional[str] = None
    dob: Optional[str] = None
    pincode: Optional[str] = None
    issue_date: Optional[str] = None
    annual_income_inr: Optional[float] = None
    id_reference: Optional[str] = None
    doc_type: Optional[str] = None

class DocumentAnalysis(BaseModel):
    id: str
    doc_type: str
    doc_name: Optional[str] = None
    blur_score: float
    blur_threshold: float = 110.0
    is_blurred: bool
    glare_ratio: float
    glare_threshold: float = 0.08
    has_glare: bool
    crop_applied: bool = False
    possible_seal_detected: bool = False
    possible_signature_detected: bool = False
    seal_signature_method: str = "color_contour_heuristic"
    extracted_fields: ExtractedFields
    ocr_confidence: float
    preview_data_url: Optional[str] = None
    user_corrected: bool = False
    processing_notes: List[str] = Field(default_factory=list)

class FieldComparisonDetail(BaseModel):
    token_similarity: float
    phonetic_similarity: float
    initial_expanded: bool
    explanation: str

class FieldComparison(BaseModel):
    field_name: str
    doc_a_type: str
    doc_a_val: Optional[str] = None
    doc_b_type: str
    doc_b_val: Optional[str] = None
    status: str  # GREEN_MATCH, WARNING_INITIAL_EXPANSION, YELLOW_REVIEW, RED_MISMATCH
    composite_score: float
    details: FieldComparisonDetail

class QualityIssue(BaseModel):
    code: str
    severity: str  # INFO, WARNING, ERROR
    doc_id: str
    doc_type: str
    message: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None

class SchemeIssue(BaseModel):
    code: str
    severity: str  # INFO, WARNING, ERROR
    doc_type: Optional[str] = None
    message: str
    rule_source: Optional[str] = None

class AdvisoryItem(BaseModel):
    id: str
    category: str
    severity: str
    title: str
    description: str
    actionable_step: str

class VerificationResponse(BaseModel):
    session_id: str
    processing_mode: str  # "real" or "demo"
    overall_status: str  # "NO_ISSUES_DETECTED", "NEEDS_REVIEW", "ACTION_REQUIRED"
    scheme_id: str
    scheme_name: str
    documents: List[DocumentAnalysis]
    field_comparisons: List[FieldComparison]
    quality_issues: List[QualityIssue]
    scheme_issues: List[SchemeIssue]
    advisories: List[AdvisoryItem]
    rule_version: str
    rule_source: str
    rule_state: str  # "VERIFIED", "DEMO_ONLY", "UNVERIFIED"
    qr_available: bool = False
    qr_payload: Optional[str] = None
    qr_data_url: Optional[str] = None
    limitations: List[str] = Field(default_factory=list)

class DecodeQRRequest(BaseModel):
    qr_payload: str

class DecodedQRResponse(BaseModel):
    valid_signature: bool
    not_expired: bool
    issuer: Optional[str] = None
    scheme_id: Optional[str] = None
    session_ref: Optional[str] = None
    pre_verification_status: Optional[str] = None
    verified_fields: Dict[str, Any] = Field(default_factory=dict)
    verification_scope: str
    issued_at: Optional[str] = None
    expires_at: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

class SingleDocExtractionResponse(BaseModel):
    extracted_name: Optional[str] = None
    confidence: float
    doc_type: str
    quality: Dict[str, Any]
    preview_data_url: Optional[str] = None
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    advisories: List[Dict[str, str]] = Field(default_factory=list)

class ClearSessionResponse(BaseModel):
    status: str
    session_id: str
    message: str
