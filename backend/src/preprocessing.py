"""Load -> RGB convert -> resize -> quality gate. Ye pipeline ka pehla step hai."""
from __future__ import annotations

import cv2
import numpy as np

from src.config import (
    RESIZE_TARGET,
    MIN_BRIGHTNESS,
    MAX_BRIGHTNESS,
    MIN_BLUR_SCORE,
    MEDIAPIPE_MODEL_SELECTION,
    FACE_MIN_DETECTION_CONFIDENCE,
)

# MediaPipe model bhaari hai, isliye lazy-load (pehli baar use hone par).
_face_detector = None


def _get_face_detector():
    """Returns lazily-built MediaPipe FaceDetection instance."""
    global _face_detector
    if _face_detector is None:
        import mediapipe as mp  # lazy import keeps module load light
        _face_detector = mp.solutions.face_detection.FaceDetection(
            model_selection=MEDIAPIPE_MODEL_SELECTION,
            min_detection_confidence=FACE_MIN_DETECTION_CONFIDENCE,
        )
    return _face_detector


def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """Returns RGB uint8 numpy array from raw image bytes."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Could not decode image — unsupported format or corrupted file")
    # BGR->RGB sirf yahin hota hai; iske baad sab modules RGB maanenge
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def resize_image(image: np.ndarray) -> np.ndarray:
    """Returns image resized to RESIZE_TARGET (width, height)."""
    return cv2.resize(image, RESIZE_TARGET, interpolation=cv2.INTER_AREA)


def detect_face(image: np.ndarray) -> bool:
    """Returns True if MediaPipe finds at least one face in the RGB image."""
    result = _get_face_detector().process(image)
    return bool(result.detections)


def check_image_quality(image: np.ndarray) -> dict:
    """Returns QualityResult dict (passed, issues, brightness, blur_score, face_detected)."""
    if image is None or image.size == 0:
        raise ValueError("check_image_quality received empty image array")

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    brightness = float(gray.mean())                              # average exposure
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())    # variance = sharpness
    face_detected = detect_face(image)

    issues: list[str] = []
    # brightness band check
    if brightness < MIN_BRIGHTNESS:
        issues.append("Image too dark — move to better lighting")
    elif brightness > MAX_BRIGHTNESS:
        issues.append("Image overexposed — reduce direct light or flash")
    # sharpness check
    if blur_score < MIN_BLUR_SCORE:
        issues.append("Image too blurry — hold steady and refocus")
    # face presence check
    if not face_detected:
        issues.append("No face detected — centre your face in frame")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "brightness": round(brightness, 1),
        "blur_score": round(blur_score, 1),
        "face_detected": face_detected,
    }


def run(image_bytes: bytes) -> tuple[np.ndarray, dict]:
    """Returns (resized RGB image, QualityResult) — pipeline entry step."""
    image = resize_image(load_image_from_bytes(image_bytes))
    return image, check_image_quality(image)


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "test_image.jpg"
    with open(path, "rb") as f:
        image, quality = run(f.read())
    print(f"image shape: {image.shape}")
    print(f"quality: {quality}")
    print("preprocessing.py: OK")
