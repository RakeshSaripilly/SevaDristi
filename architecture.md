# Antigravity Build Prompt — SevaDristi

## Role and Objective

Act as a Principal Full-Stack Engineer, Computer Vision Engineer, and Privacy-by-Design Architect.

Build **SevaDristi**, an offline-capable, multilingual document pre-verification assistant for citizens and volunteers preparing applications for CSC and Telangana MeeSeva service centres.

The application should help identify document-quality problems, possible discrepancies between supporting documents, and missing requirements before a citizen travels to a service centre.

This is a hackathon prototype, not a government-authorized verification service. Never represent a pre-verification result as official approval, guaranteed acceptance, proof of identity, or proof that a document is genuine.

### Mandatory execution workflow

1. Inspect the existing workspace and preserve useful existing work.
2. Create an implementation-plan artifact before writing application code.
3. Implement the backend, frontend, demo fixtures, translations, tests and documentation.
4. Run backend tests and frontend build checks in the terminal.
5. Start the FastAPI and Vite development servers.
6. Use the available browser to exercise the actual application.
7. Fix discovered errors and rerun relevant tests.
8. Produce a verification report containing actual commands, test results, browser checks, known limitations and screenshots if supported.

Do not claim that tests passed, servers started, offline operation works or browser verification succeeded unless those actions were actually completed. If a required dependency or tool is unavailable, document the limitation and continue with the remaining verifiable tasks.

---

# 1. Implementation Plan Artifact

Create `IMPLEMENTATION_PLAN.md` before coding.

It must include:

- Project architecture and directory tree.
- Module responsibilities and dependency boundaries.
- API contracts for `POST /api/verify` and `POST /api/decode-qr`.
- Request and response examples, validation errors and HTTP status codes.
- A Mermaid data-flow diagram.
- The internationalization architecture for all 12 languages.
- Privacy and temporary-file lifecycle.
- Scheme-rule configuration and provenance.
- QR payload structure, signing and verification.
- Demo-mode versus real-processing behaviour.
- Unit, integration, privacy, accessibility and browser test plans.
- An ordered implementation checklist with acceptance criteria.

Use a modular architecture. Keep computer vision, OCR, matching, scheme rules, QR handling and API routing in separate backend modules.

# 2. Technology Stack

## Backend

- Python 3.11+
- FastAPI and Pydantic
- OpenCV (`opencv-python-headless`)
- Pillow
- `rapidfuzz`
- `qrcode`
- Python standard libraries: `io`, `hashlib`, `hmac`, `base64`, `zlib`, `datetime`, `logging`
- `pytest` and FastAPI's test client

Use an actual OCR adapter if a supported engine is available. Detect missing dependencies explicitly and expose the active processing mode in the API response.

## Frontend

- React with Vite
- TypeScript
- Tailwind CSS
- `lucide-react`
- PWA manifest and service worker
- Responsive mobile citizen/volunteer interface
- Desktop CSC operator simulation

Use accessible components, loading states, empty states, inline validation and meaningful error messages. Do not use placeholder buttons for core functionality.

## Required directory structure

```text
SevaDristi/
├── IMPLEMENTATION_PLAN.md
├── README.md
├── backend/
│   ├── main.py
│   ├── api/
│   │   ├── verify.py
│   │   └── qr.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── vision_gate.py
│   │   ├── ocr_extractor.py
│   │   ├── reconciler.py
│   │   ├── rule_engine.py
│   │   ├── qr_bridge.py
│   │   └── privacy.py
│   ├── rules/
│   │   └── schemes.json
│   ├── locales/
│   │   └── advisories.json
│   ├── fixtures/
│   │   └── synthetic_cases.json
│   ├── tests/
│   │   ├── test_reconciler.py
│   │   ├── test_vision_gate.py
│   │   ├── test_rule_engine.py
│   │   ├── test_privacy.py
│   │   ├── test_qr.py
│   │   └── test_api.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── services/
    │   ├── hooks/
    │   ├── locales/
    │   ├── types/
    │   └── App.tsx
    ├── public/
    │   ├── manifest.json
    │   └── sw.js
    ├── package.json
    └── vite.config.ts
```

Adjust the structure if the existing project requires it, but maintain the separation of concerns.

# 3. API Contracts

## POST /api/verify

Accept a multipart request containing:

- `documents`: one or more document images.
- `scheme_id`: configured scheme identifier.
- `language`: requested advisory locale.
- `demo_preset`: optional synthetic demo case identifier.
- `simulation_enabled`: optional flag restricted to demo mode.

Never allow a client-provided flag to turn fabricated data into a real verification result.

The response must include:

```json
{
  "session_id": "ephemeral-session-id",
  "processing_mode": "real",
  "overall_status": "NEEDS_REVIEW",
  "documents": [],
  "field_comparisons": [],
  "quality_issues": [],
  "scheme_issues": [],
  "advisories": [],
  "rule_version": "configured-version",
  "rule_source": "configured-source",
  "qr_available": false,
  "limitations": []
}
```

This is a response-shape example, not hardcoded output. Populate every field from actual processing and configuration.

Requirements:

- Validate MIME type, file signature, dimensions and upload size.
- Reject malformed, unsupported or excessively large files safely.
- Process images in memory using `io.BytesIO` where feasible.
- Never persist raw uploads or unredacted document images.
- Return per-field OCR confidence and extraction provenance.
- Return actionable issues rather than an unexplained numeric score.
- Do not infer missing fields or silently substitute synthetic values.
- Set `processing_mode` to `demo` for fixture-driven runs.
- Return useful errors for unavailable OCR, unsupported documents and low-confidence extraction.
- Avoid logging sensitive request bodies, OCR output or identity numbers.

## POST /api/decode-qr

Accept a QR payload and verify its structure, integrity, issuer and expiry.

Return:

- `valid_signature`
- `not_expired`
- `issuer`
- `scheme_id`
- `verified_fields`
- `verification_scope`
- `warnings`

A successfully verified QR signature means the application-issued payload has not been altered and passes the configured signing checks. It does not mean that a government authority has approved the application.

Reject malformed, expired, altered or incorrectly signed payloads. Never trust a QR merely because it contains a valid-looking checksum.

# 4. Multilingual Architecture

Support these 12 locales:

| Locale | Native language name |
|---|---|
| `en-IN` | English |
| `hi-IN` | हिन्दी |
| `te-IN` | తెలుగు |
| `ta-IN` | தமிழ் |
| `kn-IN` | ಕನ್ನಡ |
| `ml-IN` | മലയാളം |
| `mr-IN` | मराठी |
| `bn-IN` | বাংলা |
| `gu-IN` | ગુજરાતી |
| `or-IN` | ଓଡ଼ିଆ |
| `pa-IN` | ਪੰਜਾਬੀ |
| `as-IN` | অসমীয়া |

Create one JSON translation file per locale under `frontend/src/locales/`.

Include translations for:

- Navigation and page labels.
- Scheme selection.
- Document capture instructions.
- Image-quality issues.
- Name and date discrepancies.
- Missing-document warnings.
- Confidence and review statuses.
- QR generation and scanning.
- Privacy notices.
- Errors, empty states and accessibility labels.

Store backend advisories in `backend/locales/advisories.json`.

Use stable advisory IDs shared across frontend and backend. All locales must have complete keys. Add a test that checks translation completeness and rejects empty strings.

Do not present machine-generated translations as professionally validated. Mark translations that require native-speaker review in the documentation.

### Text-to-speech

Use `window.speechSynthesis` when available.

- Prefer the selected locale's actual installed voice.
- Check available voices instead of assuming every language exists.
- Display a speaking indicator and provide stop/replay controls.
- Use browser TTS for Telugu, Hindi and English when a compatible voice is available.
- For the other languages, attempt compatible installed voices first.
- If unavailable, display the localized advisory and an honest voice-unavailable message.
- Never claim that text-to-speech works offline unless verified on the target device.

Do not use fabricated transliteration as a substitute for a validated translation.

# 5. Module A — Document Vision Quality Gate

Implement `backend/services/vision_gate.py`.

## Blur detection

Use variance of the Laplacian:

`cv2.Laplacian(gray, cv2.CV_64F).var()`

Start with a configurable threshold of `110.0`.

Below the threshold, flag `BLUR_WARNING`. Make the threshold configurable because the score depends on resolution, text content and image characteristics.

Do not automatically classify every low-scoring image as a rejected government document.

## Glare detection

Use HSV-based heuristics:

- `V > 245`
- `S < 25`
- Flag significant glare when the detected ratio exceeds `0.08`.

Return the measured ratio and the threshold used.

## Document crop and perspective correction

Implement `auto_crop_document()` using contour detection and a four-point perspective transform.

Return the original preview and processed preview when available. If document boundaries cannot be detected confidently, retain the original image and explain the problem.

## Seal and signature checks

For applicable certificate types, implement heuristic checks for possible colored stamp regions and signature-like marks.

Return:

- `possible_seal_detected`
- `possible_signature_detected`
- `confidence`
- `method`
- `limitations`

Never claim that a seal is authentic or that a signature belongs to the applicant. Missing or uncertain detection must result in a review warning, not a fabricated certainty.

## Demo simulation

Provide a clearly labelled jury-demo simulation control.

Simulation must be isolated from real image processing. Display a persistent `SIMULATED RESULT` label whenever simulated measurements or results are shown.

# 6. Module B — OCR and Field Extraction

Implement `backend/services/ocr_extractor.py`.

Extract fields only when supported by the OCR output or explicitly supplied synthetic fixtures.

Supported document types:

- `IDENTITY_CARD`
- `RATION_CARD`
- `INCOME_CERT`
- `CASTE_CERT`
- `BANK_PASSBOOK`
- `LAND_PASSBOOK`

Expected fields include:

- `doc_type`
- `full_name`
- `guardian_name`
- `dob`
- `pincode`
- `issue_date`
- `annual_income_inr`
- `id_reference`

Use ISO date formatting (`YYYY-MM-DD`) for normalized dates. Return `null` for unknown values rather than inventing values.

Mask identity-number values at the extraction boundary. The public response must never contain a full Aadhaar number.

### OCR requirements

1. Prefer a locally available OCR engine with tested support for the document's script.
2. Make OCR dependencies optional and document their installation.
3. If no compatible engine exists, return `OCR_UNAVAILABLE` for real uploads.
4. Provide a separate fixture-driven mode for the jury demo.
5. Display extracted fields with confidence values.
6. Allow users to correct extracted fields before reconciliation.
7. Preserve the distinction between OCR-extracted values and user-corrected values.
8. Do not describe OCR output as authoritative identity data.

Use synthetic documents for testing. Do not require real Aadhaar numbers or real citizen records.

# 7. Module C — Indic Name Reconciliation

Implement `backend/services/reconciler.py`.

The matching engine must work with arbitrary names. Use `RAKESH` in the initial regression tests and jury demo fixtures only.

Implement these stages:

1. Unicode normalization and safe whitespace cleanup.
2. Language-aware normalization that does not erase meaningful distinctions.
3. Honorific removal using configurable language-specific lists.
4. Token comparison using RapidFuzz.
5. Initial expansion detection.
6. Phonetic comparison using a documented Indic-compatible approach.
7. Composite score and confidence-aware classification.

Do not treat English Soundex or arbitrary character substitutions as a complete Indic phonetic algorithm. Document limitations for Telugu, Hindi, transliteration and OCR-confused characters.

### Required matching cases

**Case A: Phonetic variation**

- Document A: `SARIPILLY RAKESH`
- Document B: `SARIPILLI RAKESH`

Expected: `GREEN_MATCH` or a high-confidence equivalent when the configured normalization and evaluation demonstrate that the difference is non-material.

**Case B: Initial expansion**

- Document A: `S. RAKESH`
- Document B: `SARIPILLY RAKESH`

Expected: `WARNING_INITIAL_EXPANSION`, never an automatic hard failure solely because an initial was expanded.

**Case C: Different surname**

- Document A: `SARIPILLY RAKESH`
- Document B: `KONDAPALLI RAKESH`

Expected: `RED_MISMATCH` or `NEEDS_REVIEW` depending on confidence and token evidence. Do not let the shared first name dominate the surname discrepancy.

Use a configurable composite score that combines token similarity, phonetic similarity and character-level similarity. Do not rely on an unvalidated formula to establish identity.

A score of `0.92` or higher can be a provisional high-similarity threshold for the synthetic regression set, but it must not be treated as a universal identity-verification threshold.

### Output

Return:

- Original names.
- Normalized names.
- Token comparison.
- Initial-expansion details.
- Phonetic comparison.
- Component scores.
- Overall score.
- Final status.
- Human-readable explanation.
- OCR-confidence warnings.

Keep explanations traceable to actual comparison results.

# 8. Module D — Deterministic Scheme Rule Engine

Implement `backend/services/rule_engine.py`.

Configure schemes through `backend/rules/schemes.json`.

Seed the prototype with:

1. Telangana ePASS Post-Matric Scholarship.
2. Aasara / Cheyutha Pension.
3. Rythu Bharosa.

The initial configuration may include candidate document requirements, income thresholds, age thresholds and certificate-validity periods, but every policy value must be traceable to a source.

For each configured rule, include:

- Scheme ID and display name.
- Applicable jurisdiction.
- Required document types.
- Field-level requirements.
- Effective date, if known.
- Rule source URL or document reference.
- Last-verified date.
- Configuration version.
- Verification state: `VERIFIED`, `UNVERIFIED` or `DEMO_ONLY`.

Do not present an unverified rule as current official policy. Do not invent official source URLs or claim that a candidate requirement has been confirmed.

For rules that have not been verified, return `RULE_REQUIRES_CONFIRMATION` and explain that the checklist needs official review.

### Validation behaviour

Check:

- Missing required documents.
- Missing required fields.
- Configured certificate-validity periods.
- Income and age thresholds only when verified rules and reliable extracted values are available.
- Invalid or ambiguous dates.
- OCR uncertainty affecting eligibility-related fields.

Calculate expiry against the current date using an injectable clock for deterministic tests.

Do not automatically infer that a document is invalid merely because its issue date is old. Apply only a verified rule that establishes the relevant validity period.

### Localized advisories

Use stable identifiers such as:

- `CERT_EXPIRY`
- `INITIAL_EXPANSION`
- `NAME_MISMATCH`
- `DOCUMENT_MISSING`
- `IMAGE_BLUR`
- `IMAGE_GLARE`
- `OCR_UNCERTAIN`
- `RULE_REQUIRES_CONFIRMATION`
- `SEAL_UNCERTAIN`

Provide localized advisory messages in all 12 languages.

# 9. Module E — Privacy and Redaction

Implement `backend/services/privacy.py`.

Privacy is a mandatory acceptance criterion.

- Never save raw uploaded document images to disk.
- Process uploads in memory.
- Do not log OCR text, names, dates of birth, addresses, identity numbers or raw request bodies.
- Mask identity numbers before data reaches the public API response, logs, QR payload or analytics.
- Do not store document images in browser local storage, IndexedDB, service-worker caches or persistent application state.
- Clear temporary image buffers and session state when processing finishes or the user resets the session, to the extent supported by the runtime.
- Apply strict upload limits and reject unsupported file formats.
- Use synthetic fixtures for demos and automated tests.
- Provide a visible privacy notice explaining local processing, data retention and limitations.

### Aadhaar redaction

For the synthetic demonstration, render a black redaction region with the label `[Aadhaar Redacted]`.

For real images:

- Apply redaction only when the sensitive region is reliably located.
- If the location is uncertain, do not claim that the preview is safely redacted.
- Prevent the original unredacted preview from being exposed in the interface.
- Never return the full extracted identity number to the client.
- Test privacy using synthetic documents containing identifiable test patterns.

Treat redaction as a defence-in-depth measure. Do not claim that a black rectangle guarantees complete anonymization of the source document.

# 10. Module F — Signed Pre-Verification QR

Implement `backend/services/qr_bridge.py`.

Generate a QR only when the configured pre-verification policy allows it. A warning result may still produce a summary QR if clearly labelled as incomplete or requiring review.

Use a minimal payload:

- Schema version.
- Application issuer.
- Random or ephemeral session reference.
- Scheme ID.
- Pre-verification status.
- Issued-at timestamp.
- Expiry timestamp.
- Minimal explicitly selected fields, if genuinely necessary.

Avoid embedding names, dates of birth, addresses, bank details or identity numbers by default. Prefer a signed, privacy-preserving summary.

### Integrity and expiry

- Use HMAC-SHA256 or an appropriate digital signature implementation.
- Load secrets from environment configuration, never hardcode them in source code.
- Compare HMAC values safely.
- Validate issuer, schema, expiry and signature.
- Reject malformed or altered payloads.
- Use a configurable seven-day expiry for the prototype.
- Use compression only if it meaningfully reduces the payload.
- Document that compression and Base64 are not security mechanisms.

If a signing secret is missing, disable QR signing and display a clear configuration error rather than silently issuing trusted-looking passes.

### QR terminology

Call the feature **Pre-Verification Summary QR**.

It is not an official government approval, an eligibility certificate, an identity credential or a guarantee of faster processing.

### Self-declaration

For initial-expansion cases, offer a draft self-declaration template only if the user chooses it.

- Clearly label it `DRAFT — VERIFY REQUIREMENTS BEFORE USE`.
- Do not claim that a self-declaration is accepted by every authority.
- Do not fabricate legal language or signatures.
- Do not automatically submit or digitally sign the declaration.

# 11. Frontend View A — Citizen / Gram Volunteer

Create a mobile-first interface that works at entry-level phone screen sizes.

### Header

- SevaDristi logo and product name.
- Twelve-language native-script language selector.
- Privacy indicator.
- Real/demo processing indicator.
- Offline capability status based on actual runtime checks.

### Scheme selector

Display cards for the three configured schemes.

Each card must distinguish verified policy rules from unverified demonstration configuration.

### Document capture

Support camera capture and image upload.

Include:

- Capture guidance.
- Crop and rotate controls.
- Before/after preview.
- Blur and glare indicators.
- OCR extraction status.
- Field correction.
- Document removal.
- Session reset.

### Four jury demo presets

All names and records must be synthetic and clearly marked as demonstration data. Use `RAKESH` for the matching regression cases.

**Preset 1 — RED: Multiple issues**

- Ration card: `S. RAKESH`.
- Identity card: `SARIPILLY RAKESH`.
- Bank passbook: `KONDAPALLI RAKESH`.
- Income certificate issue date: `2024-05-10`.
- One image has simulated blur below the configured threshold.

Expected result: a combination of mismatch, possible initial expansion, configured expiry warning and image-quality warning.

The old issue date alone must not trigger expiry unless the configured validity rule and current date establish it.

**Preset 2 — YELLOW: Initial and phonetic variation**

- Identity: `SARIPILLY RAKESH`.
- Ration card: `SARIPILLI RAKESH`.
- Bank passbook: `S. RAKESH`.
- Other relevant checks use valid synthetic fixture values.

Expected result: explain the phonetic similarity and initial expansion, and request human confirmation where needed.

**Preset 3 — GREEN: No detected issues**

- Required synthetic documents contain `SARIPILLY RAKESH`.
- Image quality checks pass.
- Required fields are present.
- Applicable configured checks pass.
- No unresolved high-impact discrepancy remains.

Expected result: `NO_ISSUES_DETECTED` or an equivalent clearly scoped status. Never display “government approved.”

Generate a signed Pre-Verification Summary QR only when signing is properly configured.

**Preset 4 — GLARE AND SEAL REVIEW**

- Simulated glare ratio: 15%.
- Certificate seal detection returns uncertain or not detected.

Expected result: glare warning and a possible-seal review warning. Do not claim the document is fraudulent or invalid solely because the heuristic failed.

### Audit report

Show:

- Traffic-light summary.
- Image-quality measurements.
- Document comparison matrix.
- Field-level OCR confidence.
- Matching explanation.
- Rule-source information.
- Missing-document checklist.
- Spoken advisories.
- Human-review requirements.
- Reset and clear-session controls.

Every issue card must explain:

1. What was detected.
2. Which documents or fields are involved.
3. Why it matters.
4. What the citizen can do next.
5. Whether the conclusion is a heuristic, an OCR result or a verified configured rule.

### Wage-saved dashboard

Use explicit demo labels.

Display actual counts of simulated cases processed, issues detected and cases requiring review.

If you display estimated wages or visits potentially avoided, show the assumptions and label them as estimates. Do not represent simulated outcomes as measured real-world impact.

# 12. Frontend View B — CSC Operator Desktop

Build a desktop operator simulation resembling a form-based service workflow, without copying protected branding or claiming integration with the actual MeeSeva portal.

Include fields for:

- Applicant name.
- Guardian name.
- Date of birth.
- PIN code.
- Income certificate reference, if required.
- Verification summary reference.
- Pre-verification status.

### QR workflow

1. Scan or upload a QR image.
2. Decode the payload.
3. Validate its signature and expiry through the backend.
4. Show issuer and verification scope.
5. Auto-fill only fields present in the signed payload and permitted by the configured privacy policy.
6. Highlight unavailable fields.
7. Display warnings for expired or invalid payloads.

Do not auto-fill fabricated personal data when the QR is invalid. Do not claim that this simulation communicates with or is accepted by the actual government system.

# 13. PWA and Offline Behaviour

Implement the PWA manifest and service worker.

Cache only static application assets and approved public resources.

Never cache document uploads, OCR responses containing personal data, QR payloads or private verification reports.

Test offline behaviour explicitly:

- App shell loads after a successful initial installation.
- Cached translations remain accessible.
- Local rule evaluation works when the required rule configuration is available.
- Image processing works offline only if its required dependencies are locally available.
- TTS is reported as available only when an appropriate voice can actually be used.
- Network-dependent features show a clear offline-unavailable message.

Display a capability checklist distinguishing fully offline, partially offline and network-dependent features.

# 14. Required Automated Tests

## Name reconciliation

In `backend/tests/test_reconciler.py`, test:

1. `SARIPILLY RAKESH` vs `SARIPILLI RAKESH`: high phonetic similarity.
2. `S. RAKESH` vs `SARIPILLY RAKESH`: `WARNING_INITIAL_EXPANSION`.
3. `SARIPILLY RAKESH` vs `KONDAPALLI RAKESH`: surname discrepancy flagged.
4. Case, whitespace and Unicode normalization.
5. Low-confidence OCR does not become a high-confidence match.
6. Empty and malformed names are handled safely.

## Vision tests

Test:

- Synthetic sharp image.
- Synthetic blurred image.
- Synthetic glare image.
- Unreadable or unsupported image.
- Empty image.
- Perspective-correction failure.
- Uncertain seal and signature detection.

Use deterministic synthetic images rather than relying on real citizen documents.

## Rule engine tests

Test:

- Missing required document.
- Valid and expired certificate relative to an injected clock.
- Income threshold on a verified test rule.
- Unverified policy rule.
- Missing date.
- Invalid date.
- Complete, warning and incomplete results.

## Privacy tests

Assert that:

- Full Aadhaar-like test patterns never appear in public API responses.
- Logs do not contain sensitive test strings.
- No uploaded image is written to disk.
- Redacted previews do not expose the tested sensitive region.
- Session reset clears application state.
- Exceptions do not leak OCR output.

## QR tests

Test:

- Valid signature.
- Modified payload.
- Wrong signing key.
- Expired payload.
- Malformed payload.
- Missing secret.
- Disallowed or excessive fields.
- Compression/decompression round-trip if compression is used.

## API and frontend tests

Test:

- Valid synthetic verification request.
- Invalid uploads.
- OCR unavailable.
- Demo mode clearly identified.
- Language switching.
- Translation completeness.
- All four jury presets.
- QR auto-fill and invalid QR handling.
- Session reset.
- Responsive layout and accessibility labels.

Aim for complete coverage of critical branches. Do not claim 100% test coverage merely because all tests pass.

# 15. Build, Run and Browser Verification

Use the installed environment and available terminal/browser tools.

Backend:

```bash
cd backend
python -m pytest -q
```

Frontend:

```bash
cd frontend
npm run build
```

Use the actual available package scripts. Install dependencies only when permitted and necessary.

Start:

- FastAPI on `127.0.0.1:8000`.
- Vite on `127.0.0.1:5173`.

Configure CORS for the frontend development origin only.

Use the browser to verify:

1. The citizen view renders.
2. All twelve language options appear.
3. The four demo presets execute and display distinct expected outcomes.
4. Telugu, Hindi and Tamil translations render correctly.
5. Audio controls behave correctly when compatible voices are available.
6. The operator view can decode a valid demo QR and reject a tampered one.
7. The interface handles a missing OCR engine without crashing.
8. The application can reload its static shell offline after initial caching, if the environment supports a genuine offline test.
9. Session reset clears the active results.
10. The browser console and backend logs contain no avoidable errors or personal data.

Create `VERIFICATION_REPORT.md` containing:

- Actual test commands and their exit status.
- Number of tests passed and failed.
- Frontend build result.
- Server startup result.
- Browser scenarios executed.
- Offline capabilities actually verified.
- Known bugs and unimplemented items.
- Performance measurements with hardware and test conditions.
- Screenshots or artifacts if the environment supports creating them.

Never substitute a screenshot of a mockup for a successful browser test.

# 16. Definition of Done

The prototype is complete when:

- The implementation plan exists.
- The backend and frontend are implemented.
- The API contracts are documented and tested.
- All four demo presets produce explainable results.
- The matching regression cases pass.
- Privacy tests pass.
- QR signing and tamper detection work when properly configured.
- All twelve language files contain complete keys.
- Unverified scheme rules are clearly identified.
- Real OCR and synthetic demo processing are visibly distinguished.
- The frontend builds successfully.
- Available browser checks have been executed and documented.
- Known limitations are disclosed in the README and verification report.

**Final engineering principle:** Prefer a smaller, demonstrably working system over a feature-rich mockup. Never fabricate OCR output, official policy, verification success, privacy guarantees, performance metrics or test results to make the demonstration appear more complete.