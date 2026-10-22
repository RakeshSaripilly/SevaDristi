# SevaDristi (సేవాదృష్టి)

<p align="center">
  <img src="frontend/public/favicon.svg" width="96" height="96" alt="SevaDristi Logo" />
</p>

<p align="center">
  <strong>Offline-Capable, Multilingual Document Pre-Verification Assistant for Telangana MeeSeva & CSC Service Centres</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React 18" />
  <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV" />
  <img src="https://img.shields.io/badge/Tests-32%20Passed-success?style=for-the-badge" alt="Tests 32 Passed" />
</p>

---

> **Disclaimer**: SevaDristi is an advisory pre-screening prototype developed for demonstration and hackathon evaluation. It is **not** an authorized government portal, does not guarantee application acceptance, and does not replace official verification by MeeSeva or Tahsildar authorities.

---

## 🌟 Overview & Problem Solved

Every year, millions of citizens—particularly rural farmers, daily-wage laborers, and students—travel tens of kilometers to MeeSeva centers or Common Service Centres (CSCs) only to face **rejection at the counter** due to:
- Blurry photo scans or heavy camera glare.
- Minor transliteration discrepancies between Aadhaar and academic marks memos (e.g., *Saripilly* vs *Saripilli*, or *S. Rakesh* vs *Saripilly Rakesh*).
- Expired income certificates or missing seals.

This causes loss of daily wages, repetitive travel costs, and administrative backlogs. **SevaDristi** solves this by empowering citizens and Gram/Ward volunteers with an **instant pre-verification assistant** that runs in real-time, diagnoses issues with actionable guidance in 12 native Indic languages, and produces a tamper-proof QR audit token for CSC operators.

---

## 🚀 Key Capabilities

### 1. 🌐 12 Indic Languages with Voice Advisories
- Native script UI and phonetics for 12 official languages:
  - `te-IN` (తెలుగు), `en-IN` (English), `hi-IN` (हिन्दी), `ta-IN` (தமிழ்), `kn-IN` (ಕನ್ನಡ), `ml-IN` (മലയാളം), `mr-IN` (मराठी), `bn-IN` (বাংলা), `gu-IN` (ગુજરાતી), `or-IN` (ଓଡ଼ିଆ), `pa-IN` (ਪੰਜਾਬੀ), and `as-IN` (অসমীয়া).
- Browser-native HTML5 Text-to-Speech (TTS) voice guidance with automatic fallback detection.

### 2. 👁️ Computer Vision Document Quality Gate
- **Sharpness/Blur Analysis**: Laplacian variance calculation (`cv2.Laplacian(gray, cv2.CV_64F).var()`, threshold: 110.0).
- **Glare & Hotspot Detection**: HSV reflective hotspot filtering (`V > 245`, `S < 25`, threshold: 8% pixel ratio).
- **Perspective & Edge Rectification**: Automated 4-point contour detection and homography warping.
- **Stamp & Signature Verification**: Color mask heuristics for official violet/blue stamp ink and pen strokes.

### 3. 🔍 Indic Name Reconciliation Engine
- NFKD Unicode normalization and honorific stripping (`Sri`, `Smt`, `Kumari`, `Garu`, `Late`, etc.).
- Initial expansion detection (e.g., `S. RAKESH` vs `SARIPILLY RAKESH` $\rightarrow$ `WARNING_INITIAL_EXPANSION`).
- Indic phonetic normalization (`EE`/`I`, `OO`/`U`, `Y`/`I`, `V`/`W`, `TH`/`T`, `BH`/`B`).
- Surname discrepancy isolation (e.g., `SARIPILLY RAKESH` vs `KONDAPALLI RAKESH` $\rightarrow$ `RED_MISMATCH`).

### 4. 📋 Deterministic Welfare Policy Engine
- Pre-configured Telangana welfare schemes with verified gazette provenance:
  - **ePASS Post-Matric Scholarship** (GO Ms No. 45)
  - **Aasara / Cheyutha Pension** (GO Ms No. 28)
  - **Rythu Bharosa Investment Support** (Telangana Agriculture Dept)
- Validates certificate issue dates, age limits, caste validity, and income ceilings with injectable clock testing.

### 5. 🛡️ Privacy-by-Design Architecture
- **Zero Disk Storage**: Documents are streamed directly into memory (`io.BytesIO`) and destroyed immediately after extraction.
- **PII Masking**: Aadhaar numbers are automatically masked to `XXXX-XXXX-1234`.
- **Sanitized Logging**: No citizen identity numbers or image payloads are ever persisted to application logs.

### 6. 📱 Cryptographically Signed QR Bridge
- Signed using **HMAC-SHA256**.
- Packs minimal summary metadata (`session_id`, `scheme_id`, masked name, verification status).
- CSC Operator portal validates the signature instantaneously to detect tampering.

### 7. ⏱️ Wage & Travel Saved Metrics
- Quantifies estimated savings for each pre-verified application:
  - $\approx ₹450$ daily wage saved.
  - $\approx ₹60$ round-trip bus fare saved.
  - $\approx 4.5$ hours of transit and counter wait time saved.

---

## 🧪 Instant Jury Demo Presets

The application includes 4 one-click synthetic presets for instant demonstration:

| Preset | Target Status | Discrepancies Simulated | Actionable Output |
| :--- | :---: | :--- | :--- |
| **Preset 1 (Reject)** | 🔴 **RED** | Surname mismatch (`Kondapalli` vs `Saripilly`), expired income certificate (>1 yr), blurred bank passbook | Clear rejection breakdown + list of documents to renew |
| **Preset 2 (Warning)** | 🟡 **YELLOW** | Phonetic spelling variation (`Saripilly` vs `Saripilli`) + initial expansion | Ready-to-print **Self-Declaration Affidavit** draft |
| **Preset 3 (Ready)** | 🟢 **GREEN** | All 4 documents consistent, valid dates, high image sharpness | Green status + **HMAC-signed QR Code** |
| **Preset 4 (Quality)** | ⚠️ **REVIEW** | Glare ratio exceeds 15% and faint seal | Step-by-step camera retake instructions |

---

## 🏗️ System Architecture

```text
SevaDristi/
├── architecture.md             # Complete technical architecture specification
├── IMPLEMENTATION_PLAN.md      # Detailed engineering checklist
├── VERIFICATION_REPORT.md      # End-to-end verification and test results
├── README.md                   # Project overview & quick start
├── run.py                      # Single-command unified launcher
├── run.bat                     # Windows batch launcher
├── run.ps1                     # PowerShell launcher
├── backend/
│   ├── main.py                 # FastAPI application & CORS configuration
│   ├── requirements.txt        # Backend dependencies
│   ├── api/
│   │   ├── verify.py           # POST /api/verify endpoint
│   │   └── qr.py               # POST /api/decode-qr endpoint
│   ├── models/schemas.py       # Pydantic data schemas
│   ├── services/
│   │   ├── vision_gate.py      # OpenCV blur, glare, crop & seal heuristics
│   │   ├── reconciler.py       # Indic rapid name matcher & phonetics
│   │   ├── rule_engine.py      # Scheme rule engine with injectable clock
│   │   ├── qr_bridge.py        # HMAC-SHA256 signature generation & verification
│   │   ├── privacy.py          # Zero-disk in-memory processing & PII masking
│   │   └── ocr_extractor.py    # Local Tesseract adapter & demo fallbacks
│   ├── rules/schemes.json      # Welfare schemes catalog
│   ├── locales/advisories.json # 12-language localized advisories
│   ├── fixtures/synthetic_cases.json # Demo presets
│   └── tests/                  # 32 Pytest automated test suites
└── frontend/
    ├── package.json            # Frontend dependencies & scripts
    ├── vite.config.ts          # Vite build config
    ├── tailwind.config.js      # Tailwind configuration
    ├── public/
    │   ├── manifest.json       # PWA manifest
    │   └── sw.js               # Service Worker for offline app shell
    └── src/
        ├── components/         # Header, SchemeSelector, Uploader, Presets, AuditReport, etc.
        ├── pages/              # CitizenView and OperatorDesktop
        ├── locales/            # 12 Indic JSON language packs
        ├── services/           # Axios API client & HTML5 TTS wrapper
        └── types/              # TypeScript interfaces
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & npm

---

### Option A: ⚡ Single-Command Launch (Recommended)

Run both the FastAPI backend and Vite frontend concurrently with one command:

```bash
python run.py
```

*(On Windows, you can also double-click `run.bat` or run `.\run.ps1`)*

Once running, access:
- **Citizen & Volunteer Assistant**: [http://127.0.0.1:5173](http://127.0.0.1:5173)
- **CSC Operator Desktop**: [http://127.0.0.1:5173](http://127.0.0.1:5173) *(click "Operator View" in the top bar)*
- **FastAPI Interactive Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Backend Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

Press `Ctrl+C` in your terminal to cleanly stop both processes.

---

### Option B: Manual Multi-Terminal Setup

#### Terminal 1 — Backend Setup
```bash
# Navigate to backend
cd backend

# Create & activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

#### Terminal 2 — Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev -- --host 127.0.0.1 --port 5173
```

---

## 🧪 Testing & Verification

SevaDristi includes comprehensive backend test coverage (32 unit & integration tests) covering vision heuristics, phonetic name reconciliation, scheme eligibility logic, HMAC-SHA256 security, and 12-language advisory localization.

To run the test suite:

```bash
# From the project root:
python -m pytest backend/tests -v
```

Output:
```text
======================== 32 passed, 0 failed in 1.48s ========================
```

---

## 🔒 Security & Privacy Guarantees

| Guarantee | Technical Implementation |
| :--- | :--- |
| **No Raw Image Storage** | Zero disk persistence; images are processed in-memory via `io.BytesIO` and immediately deallocated. |
| **Aadhaar Masking** | Regex `\b\d{4}\s?\d{4}\s?\d{4}\b` automatically redacts identity numbers to `XXXX-XXXX-1234`. |
| **Anti-Tampering** | Summary QR payload is signed with a server-side `HMAC-SHA256` secret key. |
| **Network Security** | CORS strictly limits origins to trusted localhost/production domains. |
| **Service Worker Isolation** | Offline Service Worker caches only static assets and explicitly bypasses all `/api/` endpoints. |

---

## 📄 License & Attribution

Developed for academic, research, and hackathon evaluation under the **MIT License**.
Special thanks to Telangana MeeSeva guidelines and open-source civic technology standards.
