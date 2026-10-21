"""Illumination normalisation + CLAHE enhancement. Input/output dono RGB."""
from __future__ import annotations

import cv2
import numpy as np

from src.config import (
    BILATERAL_D,
    BILATERAL_SIGMA_COLOR,
    BILATERAL_SIGMA_SPACE,
    CLAHE_CLIP_LIMIT,
    CLAHE_TILE_GRID,
    TARGET_L_MEAN,
)


def normalise_illumination(image: np.ndarray) -> np.ndarray:
    """Returns RGB image with LAB L-channel mean shifted to TARGET_L_MEAN."""
    if image is None or image.size == 0:
        raise ValueError("normalise_illumination received empty image array")

    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    lum, a, b = cv2.split(lab)
    # L-channel ka mean target tak shift karo (contrast waise hi rahe)
    shift = TARGET_L_MEAN - float(lum.mean())
    l_norm = np.clip(lum.astype(np.float32) + shift, 0, 255).astype(np.uint8)
    return cv2.cvtColor(cv2.merge([l_norm, a, b]), cv2.COLOR_LAB2RGB)


def enhance_image(image: np.ndarray) -> np.ndarray:
    """Returns CLAHE-enhanced + bilateral-smoothed RGB image."""
    if image is None or image.size == 0:
        raise ValueError("enhance_image received empty image array")

    try:
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        lum, a, b = cv2.split(lab)
        # CLAHE sirf luminance par => local contrast badhta hai, colour safe
        clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_TILE_GRID)
        l_enhanced = clahe.apply(lum)
        merged = cv2.cvtColor(cv2.merge([l_enhanced, a, b]), cv2.COLOR_LAB2RGB)
        # bilateral: skin smooth, edges (blemish boundaries) preserve
        return cv2.bilateralFilter(merged, BILATERAL_D, BILATERAL_SIGMA_COLOR, BILATERAL_SIGMA_SPACE)
    except cv2.error as e:
        raise RuntimeError(f"CLAHE enhancement failed: {e}") from e


def run(image: np.ndarray) -> dict:
    """Returns EnhancedImages dict: {original, normalised, enhanced} all RGB uint8."""
    normalised = normalise_illumination(image)
    enhanced = enhance_image(normalised)
    return {"original": image, "normalised": normalised, "enhanced": enhanced}


if __name__ == "__main__":
    import sys

    from src.preprocessing import load_image_from_bytes

    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m src.enhancement <image>")
    path = sys.argv[1]
    with open(path, "rb") as f:
        image = load_image_from_bytes(f.read())

    result = run(image)
    for key, arr in result.items():
        print(f"{key:11s} shape={arr.shape} dtype={arr.dtype}")
    print("enhancement.py: OK")
