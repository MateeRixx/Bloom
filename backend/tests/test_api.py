import io

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

import main
from src.errors import FaceLandmarkError

client = TestClient(main.app)


def _png(width=512, height=512, colour=(120, 120, 120), image_format="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), colour).save(buffer, format=image_format)
    return buffer.getvalue()


def _concern(severity="Clear", count=0, area_pct=0.0, extent_score=0.0):
    return {
        "mask": np.zeros((4, 4), np.uint8),
        "count": count,
        "area_px": 0,
        "area_pct": area_pct,
        "severity": severity,
        "extent_score": extent_score,
        "regions": [],
    }


def _fake_success():
    return {
        "quality": {"passed": True, "issues": [], "reason_codes": []},
        "concerns": {
            "acne": _concern(),
            "redness": _concern(count=-1),
            "blemish": _concern(),
        },
        "images": {key: "base64" for key in (
            "original", "enhanced", "skin_mask", "baseline_annotated", "improved_annotated"
        )},
        "detection": {
            "face_detected": True,
            "landmarks_available": True,
            "fallback_used": False,
            "model": "mediapipe_face_mesh",
        },
        "mediapipe_mode": "mediapipe",
        "processing_time_sec": 0.1,
    }


def test_success_contract(monkeypatch):
    monkeypatch.setattr(main.pipeline, "run", lambda content: _fake_success())
    response = client.post("/api/analyse", files={"file": ("face.png", _png(), "image/png")})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["metrics"] is None
    assert body["detection"]["fallback_used"] is False
    assert body["concerns"]["acne"]["severity"] == "Clear"
    assert "extent_score" in body["concerns"]["acne"]
    assert "confidence" not in body["concerns"]["acne"]
    assert "count" not in body["concerns"]["redness"]


def test_quality_error_contract(monkeypatch):
    monkeypatch.setattr(main.pipeline, "run", lambda content: {
        "quality": {"passed": False, "issues": ["Too dark"], "reason_codes": ["too_dark"]},
        "processing_time_sec": 0.0,
    })
    response = client.post("/api/analyse", files={"file": ("face.png", _png(), "image/png")})
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "quality_error"
    assert body["quality"]["reason_codes"] == ["too_dark"]


def test_face_error_contract(monkeypatch):
    def raise_face_error(content):
        raise FaceLandmarkError("No face landmarks detected.")

    monkeypatch.setattr(main.pipeline, "run", raise_face_error)
    response = client.post("/api/analyse", files={"file": ("face.png", _png(), "image/png")})
    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "face_error"
    assert body["reason_code"] == "no_face_landmarks"
    assert body["detection"]["fallback_used"] is False


def test_unsupported_content_type():
    response = client.post("/api/analyse", files={"file": ("face.txt", b"hello", "text/plain")})
    assert response.status_code == 422
    assert response.json()["status"] == "invalid_image"


def test_corrupt_image_rejected():
    response = client.post("/api/analyse", files={"file": ("face.png", b"not-an-image", "image/png")})
    assert response.status_code == 422
    assert response.json()["status"] == "invalid_image"


def test_size_limit_rejected(monkeypatch):
    monkeypatch.setattr(main, "MAX_SIZE_BYTES", 10)
    response = client.post("/api/analyse", files={"file": ("face.png", _png(), "image/png")})
    assert response.status_code == 422
    assert response.json()["status"] == "invalid_image"


def test_cors_allowed_and_denied_origins():
    allowed = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    denied = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert denied.headers.get("access-control-allow-origin") is None
