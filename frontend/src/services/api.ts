import type { VerificationResponse, DecodedQRResponse, SchemeInfo } from '../types';

const API_BASE = 'http://127.0.0.1:8000/api';

export async function fetchSchemes(): Promise<SchemeInfo[]> {
  const res = await fetch(`${API_BASE}/schemes`);
  if (!res.ok) {
    throw new Error('Failed to fetch schemes catalog');
  }
  return res.json();
}

export async function verifyDocuments(
  files: File[],
  schemeId: string,
  language: string,
  demoPreset?: string
): Promise<VerificationResponse> {
  const formData = new FormData();
  formData.append('scheme_id', schemeId);
  formData.append('language', language);
  
  if (demoPreset) {
    formData.append('demo_preset', demoPreset);
    formData.append('simulation_enabled', 'true');
  } else {
    for (const f of files) {
      formData.append('documents', f);
    }
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
