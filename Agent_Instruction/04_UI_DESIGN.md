# UI DESIGN SPECIFICATION
# Project: SkinScan
# Version: 1.0
# For: Any agent writing frontend code.
# Note: This is the visual and interaction contract. Do not deviate.

---

## 0. DESIGN PHILOSOPHY

```
Clean medical utility aesthetic.
No gradients. No decorative elements.
Information density: medium — enough data to be credible, not overwhelming.
Colour carries meaning: green = good/mild, yellow = moderate, red = severe/error.
Every interactive element has a visible loading/disabled state.
Mobile-first layout (most users will upload from phone).
```

---

## 1. DESIGN TOKENS [LOCKED]

These exact values go into tailwind.config.js as custom tokens.
Use these class names everywhere. Never use arbitrary Tailwind values
like `bg-[#1a1a2e]` or hardcoded colour hex in JSX.

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f0f9ff",
          100: "#e0f2fe",
          500: "#0ea5e9",   // primary action colour
          600: "#0284c7",   // primary hover
          700: "#0369a1",   // primary active / dark text
        },
        concern: {
          acne:    "#3b82f6",   // blue
          redness: "#ef4444",   // red
          blemish: "#eab308",   // yellow
        },
        severity: {
          mild:     { bg: "#dcfce7", text: "#166534" },   // green
          moderate: { bg: "#fef9c3", text: "#854d0e" },   // yellow
          severe:   { bg: "#fee2e2", text: "#991b1b" },   // red
        },
        surface: {
          base:    "#ffffff",
          subtle:  "#f8fafc",
          border:  "#e2e8f0",
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
};
```

---

## 2. TYPOGRAPHY

```
Font imports (in index.html <head>):
  Inter (weights 400, 500, 600) — Google Fonts
  JetBrains Mono (weight 400) — Google Fonts only for metric values

Scale:
  text-xs    (12px) — captions, metadata
  text-sm    (14px) — body, labels, table cells
  text-base  (16px) — default body
  text-lg    (18px) — section headings
  text-2xl   (24px) — page title
  text-4xl   (36px) — metric numbers (font-mono)
```

---

## 3. LAYOUT [LOCKED]

```
Single page. No navigation bar needed.
Max width: max-w-4xl (896px) centred.
Padding: px-4 on mobile, px-8 on desktop.
Background: bg-surface-subtle (near-white grey)

Page structure (top to bottom):
┌────────────────────────────────────────────────────┐
│  Header (sticky)                                   │
│  Logo + title: "SkinScan"   Subtitle: "AI Skin Analysis" │
├────────────────────────────────────────────────────┤
│  Main content area (conditional on view state)     │
│  Centred, max-w-4xl                               │
│                                                    │
│  VIEW: upload      → UploadZone                   │
│  VIEW: processing  → ProcessingView               │
│  VIEW: results     → ResultsPanel                 │
│  VIEW: error       → ErrorView                    │
├────────────────────────────────────────────────────┤
│  Footer (minimal)                                  │
│  "For educational use only. Not medical advice."  │
└────────────────────────────────────────────────────┘
```

---

## 4. COMPONENT SPECIFICATIONS

### 4.1 Header
```
Height: h-16
Background: bg-white border-b border-surface-border
Content: left-aligned logo mark + "SkinScan" in text-xl font-semibold
         right-aligned: "Not medical advice" text-xs text-slate-400
Sticky: yes (sticky top-0 z-10)
```

### 4.2 UploadZone
```
Container:
  - Centred, max-w-md, mt-16
  - Rounded-xl border-2 border-dashed border-surface-border
  - bg-white p-12
  - Hover state: border-brand-500 bg-brand-50

Content (top to bottom):
  - Upload icon (camera or cloud-upload, 48px, text-slate-300)
  - "Upload a skin photo" text-lg font-medium text-slate-700
  - "JPEG or PNG, up to 10MB" text-sm text-slate-400
  - "Choose file" button (brand-500, solid, rounded-lg, px-6 py-2)
  - OR "drag and drop here" text-sm text-slate-400

Selected state (file chosen, not yet submitted):
  - Shows image preview (thumbnail, rounded-lg, max-h-48, object-cover)
  - File name + size text-sm text-slate-500
  - "Analyse" button (full width, bg-brand-500, text-white, h-12)
  - "Remove" text button (text-sm text-slate-400 underline)

Drag-over state:
  - Border colour: border-brand-500
  - Background: bg-brand-50
  - Icon changes to slightly larger
```

### 4.3 ProcessingView
```
Container: centred, mt-24

Content:
  - Spinner (animate-spin, 48px circle, border-4 border-brand-500 border-t-transparent)
  - "Analysing your image…" text-lg font-medium mt-6
  - Processing stage label (cycles through stages, text-sm text-slate-500 mt-2):
      Stage 1: "Enhancing image quality…"
      Stage 2: "Detecting skin region…"
      Stage 3: "Analysing frequency patterns…"
      Stage 4: "Identifying concerns…"
      Stage 5: "Computing metrics…"
  - Stage label cycles on 1.5s interval using useEffect

No cancel button. Processing takes 2-5s, not worth adding complexity.
```

### 4.4 ResultsPanel
```
Container: mt-8 space-y-6

Layout (top to bottom):
  1. ComparisonGrid
  2. ConcernBadges
  3. MetricsTable
  4. ResetButton
```

### 4.5 ComparisonGrid
```
Title: "Analysis Results" text-lg font-semibold mb-4

Grid layout: 5 images in a horizontal scroll row on mobile,
             2-3 column grid on desktop (md:grid-cols-3 + last two span)

Each image cell:
  - bg-white rounded-lg overflow-hidden border border-surface-border
  - Image: w-full aspect-square object-cover
  - Label below: text-xs text-slate-500 text-center py-2

Image labels (in order):
  1. "Original"
  2. "Enhanced"
  3. "Skin Mask"
  4. "Baseline Detection"
  5. "Improved Detection"

Improved Detection cell:
  - Border: border-brand-500 border-2 (highlight as primary result)
  - Label: "Improved Detection ★" with brand colour text
```

### 4.6 ConcernBadges
```
Container: bg-white rounded-xl p-6 border border-surface-border

Title: "Detected Concerns" text-lg font-semibold mb-4

Layout: 3 cards in a row (grid-cols-1 sm:grid-cols-3 gap-4)

Each concern card:
  ┌──────────────────────────────────┐
  │  ● Acne                [Moderate]│  ← concern name left, severity badge right
  │  11 regions · 2.1% of skin area  │  ← count + area
  │  Confidence: High                │  ← small text, text-slate-400
  └──────────────────────────────────┘

Severity badge colours:
  Mild:     bg-green-100 text-green-800
  Moderate: bg-yellow-100 text-yellow-800
  Severe:   bg-red-100 text-red-800

Concern dot colours:
  Acne:     text-blue-500
  Redness:  text-red-500
  Blemish:  text-yellow-500

Redness card: no "count" field (show "—" for count)
```

### 4.7 MetricsTable
```
Container: bg-white rounded-xl p-6 border border-surface-border

Title: "Pipeline Comparison" text-lg font-semibold mb-4
Subtitle: "Baseline (naive) vs Improved (frequency-aware)" text-sm text-slate-500 mb-4

Table structure:
┌─────────────┬──────────┬──────────┬──────────┐
│ Metric      │ Baseline │ Improved │ Delta    │
├─────────────┼──────────┼──────────┼──────────┤
│ IoU         │ 0.38     │ 0.61     │ +60.5%  ▲│
│ Dice        │ 0.55     │ 0.76     │ +38.2%  ▲│
│ Precision   │ 0.44     │ 0.68     │ +54.5%  ▲│
│ Recall      │ 0.55     │ 0.79     │ +43.6%  ▲│
│ F1-Score    │ 0.49     │ 0.73     │ +49.0%  ▲│
└─────────────┴──────────┴──────────┴──────────┘

Styling:
  - Header row: bg-surface-subtle text-xs font-semibold uppercase text-slate-500
  - Baseline column: text-slate-500 (de-emphasised)
  - Improved column: text-slate-900 font-medium (emphasised)
  - Delta column: text-green-700 font-medium (always positive in our pipeline)
  - Alternating row background: even rows bg-surface-subtle
  - All numbers: font-mono text-sm

Delta calculation: ((improved - baseline) / baseline * 100).toFixed(1) + "%"
```

### 4.8 ErrorView
```
Container: centred, max-w-md, mt-16
  - bg-red-50 border border-red-200 rounded-xl p-8

Content:
  - Warning icon (⚠, 40px, text-red-400)
  - "We couldn't analyse this image" text-lg font-medium text-red-900 mt-4
  - Issues list (for quality errors):
    Each issue: "• Image too dark — move to better lighting" text-sm text-red-700
  - Generic message (for server errors):
    "Something went wrong. Please try again." text-sm text-red-700
  - "Try another image" button (brand-500, full width, mt-6)
    → resets to upload view

Tips section (for quality errors only):
  - "Tips for a better photo:" text-sm font-medium text-slate-600 mt-4
  - "✓ Face a window or natural light source"
  - "✓ Hold phone at arm's length"
  - "✓ Keep face centred and fully visible"
  - "✓ Avoid heavy filters or flash"
```

### 4.9 ResetButton
```
Full width button at bottom of results panel
"Analyse another image" text-sm
Style: border border-surface-border text-slate-600 rounded-lg py-3
Hover: bg-surface-subtle
```

---

## 5. INTERACTION STATES

Every interactive element must implement all states:

```
Button states:
  default:   visible, clickable
  hover:     slightly darker bg
  active:    slightly darker + scale-95
  disabled:  opacity-50 cursor-not-allowed
  loading:   spinner replacing text, disabled

File input states:
  empty:     dashed border, upload prompt
  drag-over: solid border, bg tint
  selected:  preview shown, analyse button active
  uploading: analyse button shows spinner, disabled

Image cells in grid:
  loading:   grey placeholder with animate-pulse
  loaded:    fade-in transition (transition-opacity duration-300)
  error:     grey box with "Image unavailable" text-xs
```

---

## 6. RESPONSIVE BREAKPOINTS

```
Mobile (default, < 640px):
  - UploadZone: full width, p-8
  - ComparisonGrid: horizontal scroll (flex overflow-x-auto)
  - ConcernBadges: single column (grid-cols-1)
  - MetricsTable: horizontal scroll

Tablet (sm:, 640px+):
  - ConcernBadges: 3 columns (sm:grid-cols-3)

Desktop (md:, 768px+):
  - ComparisonGrid: 3-column grid
  - Full padding (px-8)
```

---

## 7. ACCESSIBILITY REQUIREMENTS

```
- All images have descriptive alt text
- Buttons have aria-label when icon-only
- Focus ring visible on all interactive elements (focus:ring-2 focus:ring-brand-500)
- Colour is never the only indicator — icons or text labels always accompany colour
- Loading states announced via aria-live="polite"
- Error messages in role="alert"
```

---

## 8. WHAT NOT TO BUILD

```
- No dark mode toggle
- No animations beyond loading spinner and image fade-in
- No tooltips (add title attribute for extra context instead)
- No modals or overlays
- No navigation between pages
- No share / download buttons (future scope)
- No charts or graphs (the metrics table is sufficient)
```

---

## 9. FOOTER

```
Content: "SkinScan is for educational purposes only and does not constitute
          medical advice. Consult a dermatologist for skin concerns."
Style:   text-xs text-slate-400 text-center py-8 border-t border-surface-border
```
