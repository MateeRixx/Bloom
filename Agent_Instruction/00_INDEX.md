# AGENT DOCS — INDEX
# Project: SkinScan — AI-Assisted Skin Image Analysis
# Read this file first. It tells you what to read next.

---

## DOCUMENT MAP

| File | Read When |
|---|---|
| 00_INDEX.md (this file) | Always, first |
| 01_SYSTEM_DESIGN.md | Before writing ANY code |
| 02_AGENT_INSTRUCTIONS.md | Before writing ANY code |
| 03_DATABASE_SCHEMA.md | Before writing any function that returns data |
| 04_UI_DESIGN.md | Before writing any frontend component |
| 05_SECURITY_AUTH.md | Before writing any endpoint or file handler |

---

## QUICK REFERENCE

```
Frontend:    React 18 + Vite + Tailwind. No router. No state library.
Backend:     FastAPI + Python 3.11. Synchronous. No database.
CV Pipeline: OpenCV + scikit-image + MediaPipe. No deep learning.
Deployment:  Render (both frontend and backend). Free tier.
Auth:        None.
Storage:     None. In-memory only.
```

## WHAT THIS PROJECT DOES

User uploads a skin photo → FastAPI receives it → CV pipeline runs two versions
(baseline + improved) → returns annotated images + severity scores + metrics as JSON
→ React frontend displays results.

## WHAT THIS PROJECT DOES NOT DO

Store images. Remember users. Require login. Use a database. Use neural networks.
Make medical diagnoses.

---

## IF YOU ARE STARTING FRESH

Read in this order:
1. 01_SYSTEM_DESIGN.md     — understand the full picture
2. 02_AGENT_INSTRUCTIONS.md — understand the rules
3. 03_DATABASE_SCHEMA.md   — understand data shapes
4. Start with backend/src/config.py (first file to write)
5. Then backend/src/preprocessing.py
6. Then main.py skeleton
7. Then remaining src/ modules in pipeline order
8. Then frontend/src/App.jsx + api.js
9. Then remaining frontend components

## IF YOU ARE CONTINUING EXISTING WORK

1. Read the file you are about to edit
2. Read the relevant doc above for that file's domain
3. Check 03_DATABASE_SCHEMA.md for the data shape your function must return
4. Write. Test the module standalone. Then integrate.
