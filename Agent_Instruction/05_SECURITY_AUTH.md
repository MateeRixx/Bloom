# SECURITY & AUTH
# Project: SkinScan
# Version: 1.0
# For: Any agent writing backend endpoints, file handling, or deployment config.

---

## 0. AUTH DECISION [LOCKED]

```
There is NO authentication system.
There are NO user accounts.
There are NO sessions.
There is NO login or registration flow.

Reason: Public educational tool. Images are not stored.
        No user data persists beyond the request lifecycle.
        Auth adds complexity with no benefit for this scope.

Future scope note: If auth is added later, use Supabase Auth (free tier).
                   Do NOT implement custom JWT or password hashing.
```

---

## 1. WHAT SECURITY ACTUALLY MEANS FOR THIS PROJECT

Without auth, security means:
1. Malicious file uploads don't crash or compromise the server
2. CORS is locked down so only the frontend can call the API
3. Rate limiting prevents abuse of the free Render instance
4. No sensitive data leaks in error messages
5. Dependencies have no known critical CVEs

These five things are the entire security surface. Nothing else is needed.

---

## 2. FILE UPLOAD SECURITY [LOCKED]

Every uploaded file goes through these checks in order.
If any check fails, return HTTP 422 immediately. Do not process further.

### Check 1 — Content-Type header
```python
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}

async def validate_upload(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Unsupported file type: {file.content_type}. Upload JPEG or PNG only.")
```

### Check 2 — File size (before reading full content)
```python
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

async def read_image_safely(file: UploadFile) -> bytes:
    """Reads file bytes with size enforcement."""
    content = await file.read(MAX_SIZE_BYTES + 1)
    if len(content) > MAX_SIZE_BYTES:
        raise ValueError("File too large. Maximum size is 10MB.")
    return content
```

### Check 3 — Magic bytes (file signature verification)
Content-Type header can be spoofed. Verify the actual file signature.

```python
MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",   # JPEG magic bytes
    b"\x89PNG":      "image/png",    # PNG magic bytes
}

def verify_file_signature(content: bytes) -> None:
    """Raises ValueError if file bytes don't match an allowed image format."""
    for magic, fmt in MAGIC_BYTES.items():
        if content.startswith(magic):
            return
    raise ValueError("File content does not match an allowed image format.")
```

### Check 4 — OpenCV decode verification
```python
def decode_image_safely(content: bytes) -> np.ndarray:
    """Raises ValueError if OpenCV cannot decode the image."""
    nparr = np.frombuffer(content, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image. File may be corrupted.")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
```

[AGENT NOTE] All four checks run before the CV pipeline touches the image.
Wrap all four in main.py's /api/analyse handler, in this exact order.
Image bytes are never written to disk at any point.

---

## 3. CORS CONFIGURATION [LOCKED]

```python
# In main.py
from fastapi.middleware.cors import CORSMiddleware
import os

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # explicit list, never "*" in production
    allow_credentials=False,          # no cookies, no auth headers
    allow_methods=["POST", "GET"],    # only what we use
    allow_headers=["Content-Type"],   # only what we need
)
```

Development .env:
```
ALLOWED_ORIGINS=http://localhost:5173
```

Production .env (Render):
```
ALLOWED_ORIGINS=https://skinscan.onrender.com
```

[AGENT NOTE] Never use `allow_origins=["*"]` in production.
The Render frontend URL must be the only allowed origin.

---

## 4. RATE LIMITING [LOCKED]

Render free tier has limited CPU. Without rate limiting, one user
spamming requests can make the app unusable for everyone.

```python
# Install: slowapi (pure Python, no Redis needed)
# Add to requirements.txt: slowapi==0.1.9

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/analyse")
@limiter.limit("10/minute")    # 10 requests per IP per minute
async def analyse(request: Request, file: UploadFile = File(...)):
    ...
```

Rate limit response (automatic from slowapi):
```json
HTTP 429
{"error": "Rate limit exceeded: 10 per 1 minute"}
```

[AGENT NOTE] Frontend must handle HTTP 429:
```javascript
if (response.status === 429) {
  return { status: "error", message: "Too many requests. Please wait a moment." };
}
```

---

## 5. ERROR MESSAGE SAFETY [LOCKED]

Never expose internal error details to the client in production.

```python
# WRONG — exposes internal path and exception type
raise HTTPException(500, detail=f"cv2.error in enhancement.py line 42: {str(e)}")

# CORRECT — generic message to client, full detail to logs
import logging
logger = logging.getLogger(__name__)

try:
    result = pipeline.run(image)
except Exception as e:
    logger.error(f"Pipeline failed: {type(e).__name__}: {e}", exc_info=True)
    raise HTTPException(500, detail="Processing failed. Please try a different image.")
```

Logging level is controlled by LOG_LEVEL environment variable.
In development: LOG_LEVEL=DEBUG
In production:  LOG_LEVEL=INFO

---

## 6. DEPENDENCY SECURITY

Before deployment, run:
```bash
pip install pip-audit
pip-audit -r backend/requirements.txt
```

If any CRITICAL or HIGH CVEs are found, update the affected package.
Document any that cannot be updated and why.

---

## 7. FRONTEND SECURITY

### Content Security Policy (index.html)
```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self';
               script-src 'self';
               style-src 'self' https://fonts.googleapis.com;
               font-src https://fonts.gstatic.com;
               img-src 'self' data:;
               connect-src 'self' https://skinscan-api.onrender.com;">
```

`img-src data:` is required because result images are base64 data URIs.

### No sensitive data in frontend
```
- API URL is in environment variable (VITE_API_URL) — visible in bundle, but that's fine (it's a public API)
- No API keys in frontend code
- No user data stored in localStorage or sessionStorage
- No analytics scripts
- No third-party scripts of any kind
```

---

## 8. PRIVACY STATEMENT (for README and footer)

```
SkinScan does not store, log, or transmit your photos to any third party.
Images are processed in memory and discarded immediately after analysis.
No user accounts, cookies, or tracking of any kind.
```

[AGENT NOTE] This statement must be accurate. Verify before adding it:
- No logging middleware that logs request bodies
- No file.write() calls anywhere in the pipeline
- No external API calls from the CV pipeline

---

## 9. SECURITY CHECKLIST (run before deployment)

```
□ ALLOWED_ORIGINS set to production frontend URL (not "*")
□ File type check: content-type header
□ File type check: magic bytes signature
□ File size limit: 10MB enforced server-side
□ OpenCV decode verification
□ Rate limiting: 10/minute per IP
□ Error messages: generic to client, detailed to logs
□ No hardcoded secrets in any file
□ No images written to disk
□ pip-audit shows no CRITICAL/HIGH CVEs
□ CSP meta tag in index.html
□ No console.log of image data in frontend
```
