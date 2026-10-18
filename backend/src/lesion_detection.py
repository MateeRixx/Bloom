"""Raw concern masks: redness (LAB-A), blemish (LAB-L), acne (DoG + watershed). Sab analysis_zone tak restricted."""
from __future__ import annotations

import cv2
import numpy as np
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.segmentation import watershed

from src.config import (
    REDNESS_A_DELTA,
    BLEMISH_L_DELTA,
    ACNE_DOG_THRESHOLD_RATIO,
    LESION_MORPH_KERNEL,
    WATERSHED_DIST_THRESHOLD,
    WATERSHED_MIN_DISTANCE,
    NAIVE_REDNESS_A_THRESHOLD,
    NAIVE_BLEMISH_L_THRESHOLD,
)


def _restrict(mask: np.ndarray, zone: np.ndarray) -> np.ndarray:
    """Returns mask limited to the analysis zone."""
    return cv2.bitwise_and(mask, zone)


def _redness_mask(lab: np.ndarray, zone: np.ndarray) -> np.ndarray:
    """Returns binary mask of pixels redder than (skin mean A + delta)."""
    a = lab[:, :, 1]
    skin_pixels = a[zone > 0]
    if skin_pixels.size == 0:
        return np.zeros_like(a)
    # adaptive: baseline skin redness se kitna upar hai (absolute threshold se robust)
    threshold = float(skin_pixels.mean()) + REDNESS_A_DELTA
    mask = np.where(a > threshold, 255, 0).astype(np.uint8)
    return _restrict(mask, zone)


def _blemish_mask(lab: np.ndarray, zone: np.ndarray) -> np.ndarray:
    """Returns binary mask of dark spots (L below skin mean - delta)."""
    l = lab[:, :, 0]
    skin_pixels = l[zone > 0]
    if skin_pixels.size == 0:
        return np.zeros_like(l)
    threshold = float(skin_pixels.mean()) - BLEMISH_L_DELTA
    mask = np.where(l < threshold, 255, 0).astype(np.uint8)
    return _restrict(mask, zone)


def _separate_touching(binary: np.ndarray) -> np.ndarray:
    """Returns binary mask split at watershed lines so touching spots count separately."""
    if binary.max() == 0:
        return binary
    dist = ndi.distance_transform_edt(binary > 0)
    peaks = peak_local_max(
        dist,
        min_distance=WATERSHED_MIN_DISTANCE,
        labels=(binary > 0).astype(np.int32),
        exclude_border=False,
    )
    # weak peaks chhaant do, par kam se kam ek seed bacha rehna chahiye
    strong = peaks[dist[tuple(peaks.T)] >= WATERSHED_DIST_THRESHOLD * dist.max()]
    seeds = strong if len(strong) else peaks
    markers = np.zeros(binary.shape, np.int32)
    markers[tuple(seeds.T)] = np.arange(1, len(seeds) + 1)
    labels = watershed(-dist, markers, mask=(binary > 0), watershed_line=True)
    return np.where(labels > 0, 255, 0).astype(np.uint8)


def _acne_mask(dog: np.ndarray, zone: np.ndarray) -> np.ndarray:
    """Returns binary acne mask from DoG magnitude, then watershed-split."""
    magnitude = np.abs(dog)  # dark ya bright dono blob pakdo
    peak = float(magnitude.max())
    if peak == 0:
        return np.zeros_like(dog, dtype=np.uint8)
    mask = np.where(magnitude >= ACNE_DOG_THRESHOLD_RATIO * peak, 255, 0).astype(np.uint8)
    mask = _restrict(mask, zone)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, LESION_MORPH_KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return _separate_touching(mask)


def naive_combined_mask(image: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
    """Baseline: fixed absolute redness + dark thresholds on broad skin. No adaptive, no exclusions, no watershed."""
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    l, a = lab[:, :, 0], lab[:, :, 1]
    red = np.where(a > NAIVE_REDNESS_A_THRESHOLD, 255, 0).astype(np.uint8)
    dark = np.where(l < NAIVE_BLEMISH_L_THRESHOLD, 255, 0).astype(np.uint8)
    # broad skin (eyes/lips included) => false positives expected
    return cv2.bitwise_and(cv2.bitwise_or(red, dark), skin_mask)


def run(frequency: dict, segmentation: dict) -> dict:
    """Returns RawConcernMasks dict: {acne, redness, blemish}."""
    lab = frequency["lab"]
    zone = segmentation["analysis_zone"]

    return {
        "acne": _acne_mask(frequency["dog"], zone),
        "redness": _redness_mask(lab, zone),
        "blemish": _blemish_mask(lab, zone),
    }


if __name__ == "__main__":
    import sys

    from src.preprocessing import run as preprocess
    from src.enhancement import run as enhance
    from src.frequency_decomposition import run as decompose
    from src.skin_segmentation import run as segment

    path = sys.argv[1] if len(sys.argv) > 1 else "test_image.jpg"
    with open(path, "rb") as f:
        image, _ = preprocess(f.read())

    enhanced = enhance(image)["enhanced"]
    frequency = decompose(enhanced)
    segmentation = segment(enhanced)

    masks = run(frequency, segmentation)
    for key, m in masks.items():
        print(f"{key:8s} shape={m.shape} dtype={m.dtype} nonzero={int((m > 0).sum())}")
    print("lesion_detection.py: OK")
