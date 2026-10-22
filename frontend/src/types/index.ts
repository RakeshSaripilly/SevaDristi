export interface ExtractedFields {
  full_name?: string | null;
  guardian_name?: string | null;
  dob?: string | null;
  pincode?: string | null;
  issue_date?: string | null;
  annual_income_inr?: number | null;
  id_reference?: string | null;
  doc_type?: string | null;
}

export interface DocumentAnalysis {
  id: string;
  doc_type: string;
  doc_name?: string | null;
  blur_score: number;
  blur_threshold: number;
  is_blurred: boolean;
  glare_ratio: number;
  glare_threshold: number;
  has_glare: boolean;
  crop_applied: boolean;
  possible_seal_detected: boolean;
  possible_signature_detected: boolean;
  seal_signature_method?: string;
  extracted_fields: ExtractedFields;
  ocr_confidence: number;
  preview_data_url?: string | null;
  user_corrected?: boolean;
  processing_notes?: string[];
}

export interface FieldComparisonDetail {
  token_similarity: number;
  phonetic_similarity: number;
  initial_expanded: boolean;
  explanation: string;
}

export interface FieldComparison {
  field_name: string;
  doc_a_type: string;
  doc_a_val?: string | null;
  doc_b_type: string;
  doc_b_val?: string | null;
  status: 'GREEN_MATCH' | 'WARNING_INITIAL_EXPANSION' | 'YELLOW_REVIEW' | 'RED_MISMATCH';
  composite_score: number;
  details: FieldComparisonDetail;
}

export interface QualityIssue {
  code: string;
  severity: 'INFO' | 'WARNING' | 'ERROR';
  doc_id: string;
  doc_type: string;
  message: string;
  metric_value?: number | null;
  threshold?: number | null;
}

export interface SchemeIssue {
  code: string;
  severity: 'INFO' | 'WARNING' | 'ERROR';
  doc_type?: string | null;
  message: string;
  rule_source?: string | null;
}

export interface AdvisoryItem {
  id: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  actionable_step: string;
}

export interface VerificationResponse {
  session_id: string;
  processing_mode: 'real' | 'demo';
  overall_status: 'NO_ISSUES_DETECTED' | 'NEEDS_REVIEW' | 'ACTION_REQUIRED';
  scheme_id: string;
  scheme_name: string;
  documents: DocumentAnalysis[];
  field_comparisons: FieldComparison[];
  quality_issues: QualityIssue[];
  scheme_issues: SchemeIssue[];
  advisories: AdvisoryItem[];
  rule_version: string;
  rule_source: string;
  rule_state: 'VERIFIED' | 'DEMO_ONLY' | 'UNVERIFIED';
  qr_available: boolean;
  qr_payload?: string | null;
  qr_data_url?: string | null;
  limitations: string[];
}

export interface DecodedQRResponse {
  valid_signature: boolean;
  not_expired: boolean;
  issuer?: string | null;
  scheme_id?: string | null;
  session_ref?: string | null;
  pre_verification_status?: string | null;
  verified_fields: Record<string, any>;
  verification_scope: string;
  issued_at?: string | null;
  expires_at?: string | null;
  warnings: string[];
}

export interface SchemeInfo {
  id: string;
  display_name: string;
  display_name_te?: string;
  jurisdiction: string;
  verification_state: 'VERIFIED' | 'DEMO_ONLY' | 'UNVERIFIED';
  rule_source: string;
  effective_date?: string;
  last_verified_date?: string;
  config_version: string;
  required_documents: string[];
  description: string;
}

export type SupportedLocale =
  | 'en-IN'
  | 'hi-IN'
  | 'te-IN'
  | 'ta-IN'
  | 'kn-IN'
  | 'ml-IN'
  | 'mr-IN'
  | 'bn-IN'
  | 'gu-IN'
  | 'or-IN'
  | 'pa-IN'
  | 'as-IN';
