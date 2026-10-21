"""Gradient and edge operators. Edge maps are diagnostic features, not lesion masks."""
from __future__ import annotations

import cv2
import numpy as np

from src.config import CANNY_HIGH_THRESHOLD, CANNY_LOW_THRESHOLD, SOBEL_KSIZE


def _gray(image: np.ndarray) -> np.ndarray:
    """Returns uint8 grayscale from RGB or grayscale input."""
    if image.ndim == 3:
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return image.astype(np.uint8)


def sobel_gradient(image: np.ndarray, ksize: int = SOBEL_KSIZE) -> dict:
    """Returns Sobel/Scharr gradient magnitude and a display-normalized map."""
    gray = _gray(image)
    # Scharr is the more accurate 3x3 derivative; fall back to Sobel for other sizes.
    if ksize == 3:
        gx = cv2.Scharr(gray, cv2.CV_32F, 1, 0)
        gy = cv2.Scharr(gray, cv2.CV_32F, 0, 1)
    else:
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=ksize)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=ksize)
    magnitude = cv2.magnitude(gx, gy).astype(np.float32)
    peak = float(magnitude.max())
    display = np.zeros_like(gray)
    if peak > 0:
        display = np.clip(magnitude / peak * 255.0, 0, 255).astype(np.uint8)
    return {"magnitude": magnitude, "display": display}


def canny_edges(
    image: np.ndarray,
    low_threshold: int = CANNY_LOW_THRESHOLD,
    high_threshold: int = CANNY_HIGH_THRESHOLD,
) -> np.ndarray:
    """Returns a binary (0/255) Canny edge map."""
    if low_threshold >= high_threshold:
        raise ValueError("Canny low_threshold must be less than high_threshold")
    gray = _gray(image)
    return cv2.Canny(gray, int(low_threshold), int(high_threshold))


def laplacian_map(image: np.ndarray, ksize: int = 3) -> dict:
    """Returns Laplacian response and an absolute display map."""
    gray = _gray(image)
    response = cv2.Laplacian(gray, cv2.CV_32F, ksize=ksize)
    magnitude = np.abs(response)
    peak = float(magnitude.max())
    display = np.zeros_like(gray)
    if peak > 0:
        display = np.clip(magnitude / peak * 255.0, 0, 255).astype(np.uint8)
    return {"response": response.astype(np.float32), "display": display}


def edge_density(edge_map: np.ndarray, roi: np.ndarray | None = None) -> float:
    """Returns fraction of ROI pixels marked as edges (0-1)."""
    edges = np.asarray(edge_map) > 0
    if roi is None:
        return float(edges.mean())
    mask = np.asarray(roi) > 0
    if not mask.any():
        return 0.0
    return float(edges[mask].mean())
