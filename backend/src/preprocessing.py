"""Load -> RGB convert -> resize -> brightness/sharpness quality gate."""
from __future__ import annotations

import cv2
import numpy as np

from src.config import (
    MAX_BRIGHTNESS,
    MIN_BLUR_SCORE,
    MIN_BRIGHTNESS,
    RESIZE_TARGET,
)
from src.errors import InvalidImageError


def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """Returns RGB uint8 numpy array from raw image bytes."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise InvalidImageError("Could not decode image — unsupported format or corrupted file")
    # BGR->RGB happens only here; every downstream module receives RGB.
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def resize_image(image: np.ndarray) -> np.ndarray:
    """Returns image resized to RESIZE_TARGET (width, height)."""
    return cv2.resize(image, RESIZE_TARGET, interpolation=cv2.INTER_AREA)


def check_image_quality(image: np.ndarray) -> dict:
    """Returns QualityResult dict (passed, issues, reason_codes, brightness, blur_score).

    Face presence is intentionally *not* checked here. FaceMesh performs the single
    face/landmark inference later in the pipeline, avoiding a duplicate model pass.
    """
    if image is None or image.size == 0:
        raise ValueError("check_image_quality received empty image array")

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    brightness = float(gray.mean())                              # average exposure
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())    # variance = sharpness

    issues: list[str] = []
    reason_codes: list[str] = []
    # brightness band check
    if brightness < MIN_BRIGHTNESS:
        issues.append("Image too dark — move to better lighting")
        reason_codes.append("too_dark")
    elif brightness > MAX_BRIGHTNESS:
        issues.append("Image overexposed — reduce direct light or flash")
        reason_codes.append("overexposed")
    # sharpness check
    if blur_score < MIN_BLUR_SCORE:
        issues.append("Image too blurry — hold steady and refocus")
        reason_codes.append("too_blurry")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "reason_codes": reason_codes,
        "brightness": round(brightness, 1),
        "blur_score": round(blur_score, 1),
    }


def run(image_bytes: bytes) -> tuple[np.ndarray, dict]:
    """Returns (resized RGB image, QualityResult) — pipeline entry step."""
    image = resize_image(load_image_from_bytes(image_bytes))
    return image, check_image_quality(image)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m src.preprocessing <image>")
    path = sys.argv[1]
    with open(path, "rb") as f:
        image, quality = run(f.read())
    print(f"image shape: {image.shape}")
    print(f"quality: {quality}")
    print("preprocessing.py: OK")
