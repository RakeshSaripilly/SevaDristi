import type { VerificationResponse, DecodedQRResponse, SchemeInfo } from '../types';

const rawBase = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' && window.location.port === '5173' ? 'http://127.0.0.1:8000/api' : '/api');
const API_BASE = rawBase.endsWith('/api') ? rawBase : `${rawBase.replace(/\/+$/, '')}/api`;

export async function fetchSchemes(): Promise<SchemeInfo[]> {
  const res = await fetch(`${API_BASE}/schemes`);
  if (!res.ok) {
    throw new Error('Failed to fetch schemes catalog');
  }
  return res.json();
}

export interface SingleDocExtractionResult {
  extracted_name?: string | null;
  confidence: number;
  doc_type: string;
  quality: {
    blur_score: number;
    blur_threshold: number;
    is_blurred: boolean;
    glare_ratio: number;
    glare_threshold: number;
    has_glare: boolean;
    crop_applied: boolean;
    corners?: number[][];
  };
  preview_data_url?: string;
  extracted_fields: Record<string, any>;
  advisories: Array<{ en: string; te: string }>;
}

export async function extractSingleDoc(
  file: File,
  docTypeHint?: string
): Promise<SingleDocExtractionResult> {
  const formData = new FormData();
  formData.append('document', file);
  if (docTypeHint) {
    formData.append('doc_type_hint', docTypeHint);
  }

  const res = await fetch(`${API_BASE}/extract-name-only`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Single extraction failed' }));
    throw new Error(err.detail || 'Document extraction failed');
  }

  return res.json();
}

export async function verifyDocuments(
  files: File[],
  schemeId: string,
  language: string,
  userEditedNames?: Record<string, string>,
  docTypeHints?: string[]
): Promise<VerificationResponse> {
  const formData = new FormData();
  formData.append('scheme_id', schemeId);
  formData.append('language', language);
  
  for (const f of files) {
    formData.append('documents', f);
  }

  if (docTypeHints && docTypeHints.length > 0) {
    formData.append('doc_type_hints', JSON.stringify(docTypeHints));
  }

  if (userEditedNames && Object.keys(userEditedNames).length > 0) {
    formData.append('user_edited_names', JSON.stringify(userEditedNames));
  }

  const res = await fetch(`${API_BASE}/verify`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Verification failed' }));
    throw new Error(err.detail || 'Verification request failed');
  }

  return res.json();
}

export async function clearSession(sessionId: string): Promise<void> {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  await fetch(`${API_BASE}/clear-session`, {
    method: 'POST',
    body: formData,
  }).catch(() => {});
}

export async function decodeQrPayload(payloadStr: string): Promise<DecodedQRResponse> {
  const res = await fetch(`${API_BASE}/decode-qr`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ qr_payload: payloadStr }),
  });

  if (!res.ok) {
    throw new Error('Failed to communicate with QR decode service');
  }

  return res.json();
}
