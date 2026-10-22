# SevaDristi (సేవాదృష్టి)

> **Offline-Capable, Multilingual Document Pre-Verification Assistant for Telangana MeeSeva & CSC Service Centres**

SevaDristi is a privacy-by-design pre-verification assistant that helps citizens, Gram/Ward volunteers, and service operators verify document quality, reconcile name variations, and check policy requirements *before* traveling to MeeSeva or Common Service Centres (CSCs).

> **Disclaimer**: SevaDristi is an advisory pre-screening prototype developed for demonstration and hackathon evaluation. It is **not** an authorized government portal, does not guarantee application acceptance, and does not replace official verification by MeeSeva or Tahsildar authorities.

---

## 🌟 Key Features

1. **12 Indic Languages with Native Script UI & Voice Guidance**:
   - `te-IN` (తెలుగు), `en-IN` (English), `hi-IN` (हिन्दी), `ta-IN` (தமிழ்), `kn-IN` (ಕನ್ನಡ), `ml-IN` (മലയാളം), `mr-IN` (मराठी), `bn-IN` (বাংলা), `gu-IN` (ગુજરાતી), `or-IN` (ଓଡ଼ିଆ), `pa-IN` (ਪੰਜਾਬੀ), and `as-IN` (অসমীয়া).
   - Audio advisory playback using HTML5 speech synthesis with voice availability detection.

2. **Computer Vision Document Quality Gate**:
   - **Sharpness/Blur Analysis**: Laplacian variance scoring (`cv2.Laplacian(gray, cv2.CV_64F).var()`, threshold: 110.0).
   - **Glare Detection**: HSV reflective hotspot analysis (`V > 245`, `S < 25`, threshold: 8%).
   - **Auto-Crop & Perspective Correction**: 4-point contour perspective transform.
   - **Seal & Signature Heuristics**: Color mask detection for official stamp inks and handwritten signature marks.

3. **Indic Name Reconciliation Engine**:
   - Unicode NFKD decomposition and honorific stripping (`Sri`, `Smt`, `Garu`, `Late`, etc.).
   - Initial expansion detection (e.g. `S. RAKESH` vs `SARIPILLY RAKESH` -> `WARNING_INITIAL_EXPANSION`).
   - Indic phonetic normalization (`EE`/`I`, `OO`/`U`, `Y`/`I`, `V`/`W`, `TH`/`T`, `BH`/`B`).
   - Surname discrepancy isolation (e.g. `SARIPILLY RAKESH` vs `KONDAPALLI RAKESH` -> `RED_MISMATCH`).

4. **Deterministic Policy Rule Engine**:
   - Configured Telangana welfare schemes with verified gazette provenance:
     - **ePASS Post-Matric Scholarship** (GO Ms No. 45)
     - **Aasara / Cheyutha Pension** (GO Ms No. 28)
     - **Rythu Bharosa Investment Support** (Draft Demo Rules)
   - Certificate validity verification with injectable clock testing.

5. **Privacy-by-Design Architecture**:
   - **Zero Disk Ingestion**: Uploaded documents are read in RAM (`io.BytesIO`) and discarded immediately after processing.
   - **Immediate PII Redaction**: 12-digit Aadhaar patterns are masked to `XXXX-XXXX-1234`.
   - **Log Sanitization**: No raw images, personal names, or identity numbers are logged.

6. **Cryptographically Signed Pre-Verification Summary QR**:
   - Signed using **HMAC-SHA256**.
   - Contains minimal non-sensitive summary metadata (`session_id`, `scheme_id`, masked name, status).
   - Desktop CSC Operator portal simulation with instant tamper detection.

7. **Four Instant Jury Demo Presets**:
   - **Preset 1 (RED)**: Surname mismatch, expired income certificate (>1 yr), blurred bank passbook.
   - **Preset 2 (YELLOW)**: Phonetic variation (`SARIPILLY` vs `SARIPILLI`) and initial expansion with draft Self-Declaration generator.
   - **Preset 3 (GREEN)**: Consistent credentials across all 4 documents; ready for submission with signed QR.
   - **Preset 4 (QUALITY REVIEW)**: 15.2% glare ratio and uncertain seal heuristic.

---

## 🏗️ Project Architecture

```text
SFIC/
├── architecture.md             # Specification & constraints
├── IMPLEMENTATION_PLAN.md      # Engineering architecture & API contracts
├── VERIFICATION_REPORT.md      # Test outcomes, browser audit, and benchmarks
├── README.md                   # Project documentation
├── backend/
│   ├── main.py                 # FastAPI entrypoint with CORS & routes
│   ├── requirements.txt        # Backend dependencies
│   ├── api/
│   │   ├── verify.py           # POST /api/verify endpoint
│   │   └── qr.py               # POST /api/decode-qr endpoint
│   ├── models/schemas.py       # Pydantic schemas
│   ├── services/
│   │   ├── vision_gate.py      # OpenCV blur, glare, crop, seal heuristics
│   │   ├── reconciler.py       # Indic name matcher (RapidFuzz + Phonetics)
│   │   ├── rule_engine.py      # Scheme rule engine with injectable clock
│   │   ├── qr_bridge.py        # HMAC-SHA256 signing and verification
│   │   ├── privacy.py          # In-memory zero-disk PII redaction
│   │   └── ocr_extractor.py    # Local Tesseract adapter & demo fallbacks
│   ├── rules/schemes.json      # Telangana welfare schemes catalog
│   ├── locales/advisories.json # 12-language advisory catalog
│   ├── fixtures/synthetic_cases.json # 4 Jury presets
│   └── tests/                  # 32 Pytest test cases
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    ├── public/
    │   ├── manifest.json       # PWA manifest
    │   └── sw.js               # Service Worker for offline app shell
    └── src/
        ├── components/         # Header, Schemes, Uploader, Presets, AuditReport, etc.
        ├── pages/              # CitizenView and OperatorDesktop
        ├── locales/            # 12 JSON translation files
        └── services/           # API and TTS services
```

---

## 🚀 Quick Start Guide

### ⚡ Single Command Launch (Recommended)
Run the entire application (both the FastAPI backend and Vite frontend concurrently) with a single command:

```bash
python run.py
```
*(Or on Windows, simply double-click or run `.\run.bat` / `.\run.ps1`)*

Once started, open:
- **Citizen & Volunteer Assistant**: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **CSC Operator Desktop**: [http://127.0.0.1:5173](http://127.0.0.1:5173) (click Operator View in top right)
- **FastAPI Interactive Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Backend Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

Press `Ctrl+C` in your terminal to cleanly stop both servers.

---

### Manual Multi-Terminal Setup (Optional)

### 2. Frontend Setup
```bash
# Navigate to frontend and install dependencies
cd frontend
npm install

# Build production bundle
npm run build

# Start Vite development server on port 5173
npm run dev -- --host 127.0.0.1 --port 5173
```

### 3. Open in Browser
Open `http://127.0.0.1:5173` to explore the **Citizen & Volunteer** interface or switch to the **CSC Operator Simulation**.

---

## 🔒 Security & Privacy Guarantees

- **No Raw Image Storage**: No document image is saved to disk or persistent server storage.
- **In-Memory Buffering**: Processed via `io.BytesIO` and Python garbage-collected immediately.
- **Aadhaar Masking**: All 12-digit numbers matching `\b\d{4}\s?\d{4}\s?\d{4}\b` are masked to `XXXX-XXXX-1234` before leaving the service layer.
- **Service Worker Protection**: `sw.js` explicitly excludes all `/api` endpoints and user uploads from caching.
- **Tamper Proofing**: Pre-verification tokens use HMAC-SHA256 cryptographic signatures.
