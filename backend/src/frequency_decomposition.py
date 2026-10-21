"""Low-pass / high-pass / DoG frequency band extraction. RGB in, float32 maps out."""
from __future__ import annotations

import cv2
import numpy as np

from src.config import (
    DOG_SIGMA_1,
    DOG_SIGMA_2,
    LP_KERNEL_SIZE,
)


def run(image: np.ndarray) -> dict:
    """Returns FrequencyImages dict: {low_pass, high_pass, dog, lab}."""
    if image is None or image.size == 0:
        raise ValueError("frequency_decomposition.run received empty image array")

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)

    # low-pass: bade structures (skin tone, shading)
    low_pass = cv2.GaussianBlur(gray, LP_KERNEL_SIZE, 0)
    # high-pass: fine texture (pores, spot edges) around mid-grey 128
    high_pass = gray - low_pass + 128
    # DoG: fine Gaussian minus coarse => blob/spot response (acne)
    fine = cv2.GaussianBlur(gray, (0, 0), DOG_SIGMA_1)
    coarse = cv2.GaussianBlur(gray, (0, 0), DOG_SIGMA_2)
    dog = fine - coarse
    # LAB: colour analysis ke liye (redness = A channel)
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)

    return {
        "low_pass": low_pass,
        "high_pass": high_pass,
        "dog": dog,
        "lab": lab,
    }


if __name__ == "__main__":
    import sys

    from src.enhancement import run as enhance
    from src.preprocessing import load_image_from_bytes

    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m src.frequency_decomposition <image>")
    path = sys.argv[1]
    with open(path, "rb") as f:
        image = load_image_from_bytes(f.read())

    result = run(enhance(image)["enhanced"])
    for key, arr in result.items():
        print(f"{key:10s} shape={arr.shape} dtype={arr.dtype} min={arr.min():.1f} max={arr.max():.1f}")
    print("frequency_decomposition.py: OK")
