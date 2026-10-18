# DATA SHAPES & SCHEMA
# Project: SkinScan
# Version: 1.0
# Note: There is NO database. This file defines all data shapes used
#       across the pipeline, API, and frontend to enforce consistency.
#       Treat every shape here as a contract between modules.

---

## 0. WHY THIS FILE EXISTS WITHOUT A DATABASE

Every bug at module boundaries comes from mismatched data shapes.
This file defines the exact Python dict and TypeScript/JS object shapes
that flow between every module. If a function returns something not
defined here, it is wrong.

---

## 1. INTERNAL PIPELINE SHAPES (Python dicts)

### 1.1 QualityResult
Returned by: `preprocessing.check_image_quality()`
Consumed by: `pipeline.py` (decides whether to continue or abort)

```python
QualityResult = {
    "passed": bool,          # True = image is usable, False = abort
    "issues": list[str],     # Human-readable issues. Empty list if passed.
    "brightness": float,     # Mean pixel brightness 0-255
    "blur_score": float,     # Laplacian variance
    "face_detected": bool,   # Whether MediaPipe found a face
}

# Example — passing image
{"passed": True, "issues": [], "brightness": 142.3, "blur_score": 210.5, "face_detected": True}

# Example — failing image
{"passed": False, "issues": ["Image too dark — move to better lighting",
                              "No face detected — centre your face in frame"],
 "brightness": 45.2, "blur_score": 210.5, "face_detected": False}
```

### 1.2 EnhancedImages
Returned by: `enhancement.run()`
Consumed by: `skin_segmentation.py`, `frequency_decomposition.py`

```python
EnhancedImages = {
    "original":   np.ndarray,    # shape (H, W, 3), dtype uint8, RGB
    "normalised": np.ndarray,    # illumination-normalised, same shape
    "enhanced":   np.ndarray,    # CLAHE + bilateral filtered, same shape
}
```

### 1.3 SegmentationMasks
Returned by: `skin_segmentation.run()`
Consumed by: `lesion_detection.py`, `visualization.py`

```python
SegmentationMasks = {
    "skin_mask":     np.ndarray,  # shape (H, W), dtype uint8, values 0 or 255
    "analysis_zone": np.ndarray,  # skin_mask eroded + eyes/lips excluded
    "face_mask":     np.ndarray,  # raw face region from MediaPipe or fallback
    "exclusion_mask":np.ndarray,  # eyes + lips + brows + nostrils combined
    "mediapipe_mode":str,         # "mediapipe" or "fallback"
}
```

### 1.4 FrequencyImages
Returned by: `frequency_decomposition.run()`
Consumed by: `lesion_detection.py`

```python
FrequencyImages = {
    "low_pass":  np.ndarray,   # shape (H, W), dtype float32, Gaussian blurred gray
    "high_pass": np.ndarray,   # shape (H, W), dtype float32, original - low_pass + 128
    "dog":       np.ndarray,   # shape (H, W), dtype float32, DoG response
    "lab":       np.ndarray,   # shape (H, W, 3), dtype uint8, LAB colour space
}
```

### 1.5 RawConcernMasks
Returned by: `lesion_detection.run()`
Consumed by: `postprocessing.py`

```python
RawConcernMasks = {
    "acne":     np.ndarray,  # shape (H, W), dtype uint8, binary mask 0/255
    "redness":  np.ndarray,  # shape (H, W), dtype uint8, binary mask 0/255
    "blemish":  np.ndarray,  # shape (H, W), dtype uint8, binary mask 0/255
}
```

### 1.6 ConcernResult
Returned by: `postprocessing.process_concern()`
One per concern type (acne, redness, blemish)

```python
ConcernResult = {
    "mask":        np.ndarray,   # cleaned binary mask (H, W), uint8
    "count":       int,          # number of detected regions (N/A for redness → -1)
    "area_px":     int,          # total area in pixels
    "area_pct":    float,        # area as % of skin region (0-100)
    "severity":    str,          # "Mild" | "Moderate" | "Severe"
    "confidence":  str,          # "High" | "Medium" | "Low"
    "regions":     list[dict],   # per-region props (see RegionProp below)
}

RegionProp = {
    "id":           int,
    "area_px":      int,
    "centroid":     tuple[float, float],   # (row, col)
    "bbox":         tuple[int,int,int,int],# (min_row, min_col, max_row, max_col)
    "confidence":   str,                   # "High" | "Medium" | "Low"
}
```

### 1.7 MetricsResult
Returned by: `evaluation.compute_metrics()`
Contains both baseline and improved metrics.

```python
MetricsResult = {
    "baseline": PipelineMetrics,
    "improved": PipelineMetrics,
}

PipelineMetrics = {
    "iou":       float,   # 0.0 to 1.0
    "dice":      float,   # 0.0 to 1.0
    "precision": float,   # 0.0 to 1.0
    "recall":    float,   # 0.0 to 1.0
    "f1":        float,   # 0.0 to 1.0
}
```

[AGENT NOTE] When no ground truth mask is available (user-uploaded image),
metrics are computed by treating the improved pipeline's output as a
pseudo-reference for the baseline. This is an approximation — state this
in report/README. Do NOT invent ground truth that doesn't exist.

### 1.8 VisualizationOutput
Returned by: `visualization.generate_all()`
Consumed by: `pipeline.py` then `main.py`

```python
VisualizationOutput = {
    "original":            str,   # base64 JPEG
    "enhanced":            str,   # base64 JPEG
    "skin_mask":           str,   # base64 JPEG (mask visualised as green overlay)
    "baseline_annotated":  str,   # base64 JPEG
    "improved_annotated":  str,   # base64 JPEG
}
```

### 1.9 PipelineOutput
Returned by: `pipeline.run()`
Consumed by: `main.py` → serialised to JSON response

```python
PipelineOutput = {
    "quality":           QualityResult,
    "concerns": {
        "acne":          ConcernResult,
        "redness":       ConcernResult,
        "blemish":       ConcernResult,
    },
    "metrics":           MetricsResult,
    "images":            VisualizationOutput,
    "processing_time_sec": float,
    "mediapipe_mode":    str,         # "mediapipe" or "fallback"
}
```

---

## 2. API RESPONSE SHAPES (JSON)

These are subsets of PipelineOutput, serialised to JSON.
See 01_SYSTEM_DESIGN.md Section 5 for the exact JSON structure.

Key serialisation rules:
- numpy arrays → never appear in JSON response
- np.float32/float64 → Python float (use `float()` wrapper)
- np.int32/int64 → Python int (use `int()` wrapper)
- np.ndarray images → base64 string via visualization.py

```python
# In main.py — safe serialisation helper
def make_concern_json(concern: ConcernResult) -> dict:
    return {
        "severity":   concern["severity"],
        "count":      int(concern["count"]),
        "area_pct":   round(float(concern["area_pct"]), 2),
        "confidence": concern["confidence"],
    }
```

---

## 3. FRONTEND DATA SHAPES (JavaScript)

### AnalysisResult (what api.js returns to App.jsx)
```javascript
// Success
{
  status: "success",                  // string
  processing_time_sec: 2.3,          // number
  quality: {
    passed: true,                     // boolean
    issues: [],                       // string[]
  },
  images: {
    original:           "...",        // base64 string
    enhanced:           "...",
    skin_mask:          "...",
    baseline_annotated: "...",
    improved_annotated: "...",
  },
  concerns: {
    acne:     { severity: "Moderate", count: 11, area_pct: 2.1, confidence: "High" },
    redness:  { severity: "Mild",     area_pct: 4.3,            confidence: "Medium" },
    blemishes:{ severity: "Mild",     count: 3,  area_pct: 0.8, confidence: "High" },
  },
  metrics: {
    baseline: { iou: 0.38, dice: 0.55, precision: 0.44, recall: 0.55, f1: 0.49 },
    improved: { iou: 0.61, dice: 0.76, precision: 0.68, recall: 0.79, f1: 0.73 },
  },
}

// Quality error
{
  status: "quality_error",
  quality: {
    passed: false,
    issues: ["Image too dark — move to better lighting"],
  }
}

// Server error
{
  status: "error",
  message: "Processing failed. Please try a different image.",
}
```

### AppState (useState shape in App.jsx)
```javascript
const [appState, setAppState] = useState({
  view: "upload",          // "upload" | "processing" | "results" | "error"
  selectedFile: null,      // File object | null
  previewUrl: null,        // object URL string | null
  result: null,            // AnalysisResult | null
  errorMessage: null,      // string | null
});
```

[AGENT NOTE] App.jsx owns ALL state. No component below it owns state
that is shared with siblings. Props flow down. Events bubble up via callbacks.

---

## 4. CONFIGURATION SHAPE

### render.yaml (deployment config)
```yaml
services:
  - type: web
    name: skinscan-api
    env: python
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ALLOWED_ORIGINS
        value: https://skinscan.onrender.com
      - key: MAX_IMAGE_SIZE_MB
        value: "10"
      - key: LOG_LEVEL
        value: INFO

  - type: static
    name: skinscan
    buildCommand: cd frontend && npm install && npm run build
    staticPublishPath: frontend/dist
    envVars:
      - key: VITE_API_URL
        value: https://skinscan-api.onrender.com
```

---

## 5. CONCERN TYPE CONSTANTS

These string values are used identically across backend and frontend.
Do not rename them.

```
Backend key   Frontend key   Display label   Overlay colour
"acne"        "acne"         "Acne"          RGB(59, 130, 246)   blue contours
"redness"     "redness"      "Redness"       RGB(239, 68, 68)    red fill, 40% opacity
"blemish"     "blemishes"    "Blemishes"     RGB(234, 179, 8)    yellow contours
```

[AGENT NOTE] Note the inconsistency: backend uses "blemish" (singular),
frontend key is "blemishes" (plural). This is intentional — the API response
uses "blemishes" as the JSON key. Serialise accordingly in main.py:

```python
"concerns": {
    "acne":      make_concern_json(output["concerns"]["acne"]),
    "redness":   make_concern_json(output["concerns"]["redness"]),
    "blemishes": make_concern_json(output["concerns"]["blemish"]),  # ← rename here
}
```
