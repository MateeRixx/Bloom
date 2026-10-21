"""Global histogram equalisation and gamma correction for comparison with CLAHE."""
from __future__ import annotations

import cv2
import numpy as np

from src.config import GAMMA_CORRECTION


def equalize_luminance(image: np.ndarray) -> np.ndarray:
    """Returns RGB image after global histogram equalisation of the LAB L channel."""
    if image.ndim != 3:
        raise ValueError("equalize_luminance expects an RGB image")
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    lum, a, b = cv2.split(lab)
    lum_eq = cv2.equalizeHist(lum)
    return cv2.cvtColor(cv2.merge([lum_eq, a, b]), cv2.COLOR_LAB2RGB)


def gamma_correct(image: np.ndarray, gamma: float = GAMMA_CORRECTION) -> np.ndarray:
    """Returns gamma-corrected image (gamma < 1 brightens mid-tones)."""
    if gamma <= 0:
        raise ValueError("gamma must be positive")
    lut = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.uint8)
    return cv2.LUT(image, lut)


def compare_histogram_methods(image: np.ndarray) -> dict:
    """Returns original, global-equalised, and CLAHE outputs as RGB uint8 arrays."""
    from src.enhancement import enhance_image

    return {
        "original": image,
        "global_equalized": equalize_luminance(image),
        "clahe": enhance_image(image),
        "gamma": gamma_correct(image),
    }
