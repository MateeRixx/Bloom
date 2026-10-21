"""Bloom API: FastAPI routes + upload validation. Business logic lives in pipeline.py."""
import logging
import os

# Keep MediaPipe/TFLite C++ logs quiet (must be set before importing MediaPipe).
os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

from dotenv import load_dotenv
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import pipeline
import routine
from src.config import MAX_IMAGE_SIZE_MB, RATE_LIMIT
from src.errors import FaceLandmarkError, InvalidImageError
from src.image_validation import inspect_image

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger("bloom")

MAX_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
# Trim whitespace and ignore empty entries (e.g. "https://a, https://b,").
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173"
).split(",") if origin.strip()]
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAGIC_BYTES = (b"\xff\xd8\xff", b"\x89PNG")  # JPEG, PNG signatures

app = FastAPI(title="Bloom API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,      # explicit list, never "*" in production
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# In-process rate limiting: per worker, reset on restart. This deployment is scoped
# to a single Render web service process; use a shared store for multi-instance use.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- Upload validation (content-type -> size -> magic bytes -> dimensions -> decode) ---
def validate_content_type(file: UploadFile) -> None:
    """Raises ValueError if the declared content-type is not JPEG/PNG."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise InvalidImageError(f"Unsupported file type: {file.content_type}. Upload JPEG or PNG only.")


async def read_image_safely(file: UploadFile) -> bytes:
    """Returns file bytes, raising ValueError if over the size limit."""
    content = await file.read(MAX_SIZE_BYTES + 1)
    if len(content) > MAX_SIZE_BYTES:
        raise InvalidImageError(f"File too large. Maximum size is {MAX_IMAGE_SIZE_MB}MB.")
    return content


def verify_file_signature(content: bytes) -> None:
    """Raises ValueError if the bytes don't match a JPEG/PNG signature."""
    if not content.startswith(MAGIC_BYTES):
        raise InvalidImageError("File content does not match an allowed image format.")


def make_concern_json(concern: dict) -> dict:
    """Returns the API concern shape (count omitted for redness)."""
    out = {
        "severity": concern["severity"],
        "area_pct": round(float(concern["area_pct"]), 2),
        "extent_score": float(concern["extent_score"]),
    }
    if concern["count"] != -1:
        out["count"] = int(concern["count"])
    return out


def build_success(result: dict) -> dict:
    """Returns the HTTP 200 response body from a PipelineOutput."""
    return {
        "status": "success",
        "processing_time_sec": result["processing_time_sec"],
        "quality": {"passed": True, "issues": result["quality"]["issues"]},
        "detection": result["detection"],
        "images": result["images"],
        "concerns": {
            "acne": make_concern_json(result["concerns"]["acne"]),
            "redness": make_concern_json(result["concerns"]["redness"]),
            "blemishes": make_concern_json(result["concerns"]["blemish"]),  # internal -> API
        },
        "metrics": None,
        "metrics_note": (
            "Per-image accuracy is not computed for unlabelled uploads. "
            "See the offline evaluation workflow for independent ground-truth metrics."
        ),
        "mediapipe_mode": result["mediapipe_mode"],
    }


# --- Routes ---
@app.get("/")
async def root() -> dict:
    """Returns API name and version."""
    return {"name": "Bloom API", "version": "1.0"}


@app.get("/api/health")
async def health() -> dict:
    """Health check used by Render."""
    return {"status": "ok"}


@app.post("/api/analyse")
@limiter.limit(RATE_LIMIT)
async def analyse(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    """Accepts an image and returns the full analysis as JSON."""
    validate_content_type(file)
    content = await read_image_safely(file)
    verify_file_signature(content)
    inspect_image(content)
    result = pipeline.run(content)

    if not result["quality"]["passed"]:
        return JSONResponse(status_code=422, content={
            "status": "quality_error",
            "quality": {
                "passed": False,
                "issues": result["quality"]["issues"],
                "reason_codes": result["quality"].get("reason_codes", []),
            },
        })

    logger.info(
        "Analysed image in %ss (model=%s)",
        result["processing_time_sec"],
        result["detection"]["model"],
    )
    return JSONResponse(status_code=200, content=build_success(result))


@app.post("/api/routine")
@limiter.limit(RATE_LIMIT)
async def get_routine(request: Request, concerns: dict) -> dict:
    """Returns a personalized skincare routine based on detected concerns."""
    return routine.build_routine(concerns)


# --- Centralised error handling (generic to client, detail to logs) ---
@app.exception_handler(InvalidImageError)
async def invalid_image_handler(request: Request, exc: InvalidImageError) -> JSONResponse:
    """Maps decode/format/size validation failures to HTTP 422."""
    return JSONResponse(status_code=422, content={
        "status": "invalid_image",
        "message": str(exc),
    })


@app.exception_handler(FaceLandmarkError)
async def landmark_error_handler(request: Request, exc: FaceLandmarkError) -> JSONResponse:
    """Maps strict-mode face/landmark failures to HTTP 422."""
    return JSONResponse(status_code=422, content={
        "status": "face_error",
        "message": str(exc),
        "reason_code": exc.reason_code,
        "detection": {
            "face_detected": False,
            "landmarks_available": False,
            "fallback_used": False,
        },
    })


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Maps validation/quality ValueErrors to HTTP 422."""
    return JSONResponse(status_code=422, content={
        "status": "quality_error",
        "quality": {"passed": False, "issues": [str(exc)], "reason_codes": []},
        "message": str(exc),
    })


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Maps malformed requests (e.g. missing file) to HTTP 422."""
    return JSONResponse(status_code=422, content={
        "status": "error",
        "message": "Invalid request. Send an image file as multipart/form-data.",
    })


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Logs full detail, returns a generic message to the client."""
    logger.error("Unhandled error: %s: %s", type(exc).__name__, exc, exc_info=True)
    return JSONResponse(status_code=500, content={
        "status": "error",
        "message": "Processing failed. Please try a different image.",
    })
