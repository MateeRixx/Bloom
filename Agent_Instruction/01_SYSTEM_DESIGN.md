# SYSTEM DESIGN
# Project: AI-Assisted Skin Image Analysis Web Application
# Version: 1.0
# Status: Source of truth. All agents must read this before writing any code.

---

## 0. HOW TO USE THIS DOCUMENT

This document is written for AI coding agents. Follow these rules:
- Every section marked [LOCKED] is finalized. Do not change behaviour described there.
- Every section marked [AGENT NOTE] is a direct instruction to you.
- When in doubt about a decision, refer to the DECISION LOG at the bottom.
- Never infer a technology choice not listed here. If something is missing, flag it.

---

## 1. PROJECT IDENTITY

```
Name:         SkinScan
Type:         Full-stack web application
Purpose:      Users upload a facial skin photo and receive AI-assisted
              analysis identifying acne, blemishes, and redness zones.
              A baseline pipeline and an improved pipeline are compared
              quantitatively on every request.
Audience:     General public, dermatology-curious users, course evaluators.
Submission:   Public GitHub repository + Render deployment URL + demo video.
```

---

## 2. HIGH-LEVEL ARCHITECTURE [LOCKED]

```
┌─────────────────────────────────────────────────────────────────┐
│  USER BROWSER                                                    │
│  React + Vite + Tailwind CSS                                    │
│  Deployed: Render Static Site                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS POST /api/analyse
                         │ multipart/form-data (image file)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND API                                                     │
│  FastAPI (Python 3.11)                                          │
│  Deployed: Render Web Service                                   │
│  Single worker, synchronous image processing                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ calls internally
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  CV PIPELINE                                                     │
│  Pure Python modules, no GPU, no model weights                  │
│  Libraries: OpenCV, scikit-image, scikit-learn,                 │
│             MediaPipe, scipy, numpy                             │
└────────────────────────┬────────────────────────────────────────┘
                         │ reads/writes
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STORAGE                                                         │
│  Local filesystem (Render ephemeral disk)                       │
│  No database. No persistent user data. No sessions.             │
│  Images are processed in memory and discarded after response.   │
└─────────────────────────────────────────────────────────────────┘
```

[AGENT NOTE] There is NO database for user data. There is NO authentication system.
Images are never written to disk in production. Everything is in-memory per request.

---

## 3. COMPONENT BREAKDOWN

### 3.1 Frontend [LOCKED]

```
Framework:    React 18 + Vite 5
Styling:      Tailwind CSS (CDN or npm, no custom CSS framework)
State:        useState + useReducer only. No Redux. No Zustand.
API layer:    Single file: src/api.js
              One function: analyseImage(file) → Promise<AnalysisResult>
Routing:      None. Single page application. No react-router.
Build output: dist/ folder (static files only)
```

**Pages / Views (all in one page, conditional rendering):**
```
View 1: Upload        → shown on load and after reset
View 2: Processing    → shown while awaiting API response
View 3: Results       → shown when API returns success
View 4: Error         → shown when API returns error or quality gate fails
```

**Components:**
```
App.jsx               ← root, owns all state, controls which view is shown
UploadZone.jsx        ← drag-drop + file picker, previews selected image
ProcessingView.jsx    ← spinner + processing stage labels
ResultsPanel.jsx      ← parent of all result components
  ├── ComparisonGrid.jsx    ← side-by-side: original / enhanced / skin mask /
  │                            baseline annotated / improved annotated
  ├── ConcernBadges.jsx     ← acne / redness / blemish severity pills
  ├── MetricsTable.jsx      ← IoU, F1, Precision, Recall for both pipelines
  └── ResetButton.jsx       ← clears state, returns to upload view
ErrorView.jsx         ← shows quality issues or server errors with guidance
api.js                ← fetch wrapper, handles multipart upload
```

### 3.2 Backend [LOCKED]

```
Framework:    FastAPI 0.111+
Python:       3.11
Entry point:  backend/main.py
CORS:         Enabled for all origins in development.
              In production: restrict to frontend Render URL.
File size:    Maximum 10MB per upload. Enforced in FastAPI.
Image types:  JPEG, PNG only. Enforced by content-type check.
Processing:   Synchronous. One image at a time per worker.
              No background tasks. No queues. No celery.
Timeout:      30 seconds per request (Render default).
```

**Endpoints:**
```
POST /api/analyse     ← main endpoint, receives image, returns AnalysisResult
GET  /api/health      ← returns {"status": "ok"}, used by Render health check
GET  /                ← returns {"name": "SkinScan API", "version": "1.0"}
```

### 3.3 CV Pipeline [LOCKED]

**Module list and single responsibility:**
```
backend/src/
├── config.py                 ← ALL parameters. No hardcoded values elsewhere.
├── preprocessing.py          ← resize, normalise, colour convert, quality gate
├── enhancement.py            ← CLAHE on LAB L-channel + bilateral filter
├── skin_segmentation.py      ← YCrCb + HSV mask + MediaPipe face ROI + erosion
├── frequency_decomposition.py← low-pass, high-pass, DoG computation
├── lesion_detection.py       ← redness (LAB A), blemishes (LAB L), acne (DoG)
                                 + watershed for touching spot separation
├── postprocessing.py         ← min area filter, morphological cleanup,
                                 connected component labelling, severity scoring
├── evaluation.py             ← IoU, Dice, Precision, Recall, F1 computation
│                                against ground truth mask (if provided)
│                                computes baseline vs improved delta
└── visualization.py          ← generates annotated images, returns as base64
```

**Pipeline execution order (NEVER change this order):**
```
1. preprocessing.py   → quality gate → normalised image
2. enhancement.py     → enhanced image
3. skin_segmentation  → skin mask + analysis zone mask
4. frequency_decomp   → low_pass, high_pass, dog images
5. lesion_detection   → raw concern masks (acne, redness, blemish)
6. postprocessing     → cleaned masks + severity scores + region props
7. evaluation.py      → metrics dict (baseline + improved)
8. visualization.py   → annotated images as base64 strings
```

---

## 4. DATA FLOW — REQUEST LIFECYCLE [LOCKED]

```
1.  User selects image in browser
2.  Frontend validates: file is JPEG/PNG, size < 10MB (client-side check)
3.  Frontend POSTs to /api/analyse as multipart/form-data
4.  FastAPI receives file bytes into memory (UploadFile)
5.  FastAPI validates: content-type, file size (server-side check)
6.  Image bytes → numpy array (never written to disk)
7.  preprocessing.py runs quality gate
    → If FAIL: return HTTP 422 with quality_issues list immediately
    → If PASS: continue
8.  BASELINE pipeline runs on numpy array
    (steps 2→5→6 of pipeline, using naive parameters from config.py)
9.  IMPROVED pipeline runs on same numpy array
    (steps 2→8 of pipeline, using improved parameters from config.py)
10. visualization.py encodes result images to base64 JPEG strings
11. FastAPI builds AnalysisResult JSON and returns HTTP 200
12. Frontend receives JSON, transitions to Results view
13. Image bytes are garbage-collected. Nothing persists.
```

---

## 5. API CONTRACT [LOCKED]

### Request
```
POST /api/analyse
Content-Type: multipart/form-data
Body:
  file: <image file>       JPEG or PNG, max 10MB
```

### Success Response (HTTP 200)
```json
{
  "status": "success",
  "processing_time_sec": 2.3,
  "quality": {
    "passed": true,
    "issues": []
  },
  "images": {
    "original":            "<base64 JPEG string>",
    "enhanced":            "<base64 JPEG string>",
    "skin_mask":           "<base64 JPEG string>",
    "baseline_annotated":  "<base64 JPEG string>",
    "improved_annotated":  "<base64 JPEG string>"
  },
  "concerns": {
    "acne": {
      "severity": "Moderate",
      "count": 11,
      "area_pct": 2.1,
      "confidence": "High"
    },
    "redness": {
      "severity": "Mild",
      "area_pct": 4.3,
      "confidence": "Medium"
    },
    "blemishes": {
      "severity": "Mild",
      "count": 3,
      "area_pct": 0.8,
      "confidence": "High"
    }
  },
  "metrics": {
    "baseline": {
      "iou": 0.38,
      "dice": 0.55,
      "precision": 0.44,
      "recall": 0.55,
      "f1": 0.49
    },
    "improved": {
      "iou": 0.61,
      "dice": 0.76,
      "precision": 0.68,
      "recall": 0.79,
      "f1": 0.73
    }
  }
}
```

### Quality Gate Failure Response (HTTP 422)
```json
{
  "status": "quality_error",
  "quality": {
    "passed": false,
    "issues": [
      "Image too dark — move to better lighting",
      "No face detected — centre your face in frame"
    ]
  }
}
```

### Server Error Response (HTTP 500)
```json
{
  "status": "error",
  "message": "Processing failed. Please try a different image."
}
```

[AGENT NOTE] The frontend must handle all three response shapes.
Never assume a 200 means quality passed — always check status field.

---

## 6. ENVIRONMENT VARIABLES [LOCKED]

```
Backend (.env):
  ALLOWED_ORIGINS=https://skinscan.onrender.com   # frontend URL
  MAX_IMAGE_SIZE_MB=10
  LOG_LEVEL=INFO

Frontend (.env):
  VITE_API_URL=https://skinscan-api.onrender.com  # backend URL

Development overrides (.env.local):
  VITE_API_URL=http://localhost:8000
```

[AGENT NOTE] Never hardcode URLs. Always read from environment variables.
Use dotenv for local development. Render injects env vars at deploy time.

---

## 7. DEPLOYMENT [LOCKED]

```
Repository:     GitHub (public)
Frontend:       Render Static Site
                Build command:  cd frontend && npm install && npm run build
                Publish dir:    frontend/dist
Backend:        Render Web Service
                Build command:  cd backend && pip install -r requirements.txt
                Start command:  cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
                Instance type:  Free (512MB RAM, shared CPU)
                Health check:   GET /api/health
Config file:    render.yaml in repo root (defines both services)
```

---

## 8. DECISION LOG

| Decision | Choice | Reason |
|---|---|---|
| Database | None | No persistent user data needed |
| Auth | None | Public tool, no user accounts |
| Image storage | None, in-memory | Privacy, simplicity, free tier |
| Webcam | Not implemented | Upload only; webcam = future scope |
| Dataset at runtime | None | Pipeline runs on user uploads |
| Background tasks | None | Processing < 5s, sync is fine |
| State management | useState only | No cross-component shared state needed |
| CSS framework | Tailwind | Utility-first, no custom CSS overhead |
| Deployment | Render | Free, GitHub-connected, one platform |

---

## 9. OUT OF SCOPE (DO NOT IMPLEMENT)

```
- User accounts or login
- Storing analysis history per user
- Webcam live capture
- Real-time processing
- Mobile app
- Payment / premium features
- Email notifications
- Any external API calls from CV pipeline
- Model training or fine-tuning
- DICOM or clinical image formats
```
