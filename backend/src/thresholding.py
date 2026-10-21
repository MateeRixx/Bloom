"""Thresholding strategies used by lesion detection and DIP experiments.

All functions take a single-channel image and a boolean/uint8 ROI. Pixels outside
the ROI are always returned as background so threshold statistics cannot be
dominated by background/hair/eyes.
"""
from __future__ import annotations

import cv2
import numpy as np
from skimage.filters import threshold_otsu

from src.config import ADAPTIVE_BLOCK_SIZE, ADAPTIVE_C


def _as_uint8(channel: np.ndarray) -> np.ndarray:
    """Returns a uint8 view suitable for OpenCV thresholding."""
    if channel.dtype == np.uint8:
        return channel
    return cv2.normalize(channel, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


def _roi_mask(roi: np.ndarray | None, shape: tuple[int, ...]) -> np.ndarray:
    """Returns a boolean ROI; None means the whole image."""
    if roi is None:
        return np.ones(shape[:2], dtype=bool)
    return np.asarray(roi) > 0


def _restrict(mask: np.ndarray, roi: np.ndarray) -> np.ndarray:
    """Returns uint8 mask with pixels outside the ROI cleared."""
    return np.where(roi, mask, 0).astype(np.uint8)


def _values(channel: np.ndarray, roi: np.ndarray) -> np.ndarray:
    """Returns flattened ROI values, or an empty array."""
    return channel[roi].astype(np.float32).ravel()


def mean_std_threshold(
    channel: np.ndarray,
    roi: np.ndarray | None,
    min_delta: float,
    std_mult: float,
    high_is_foreground: bool = True,
) -> tuple[float, np.ndarray]:
    """Returns (threshold, mask) using mean ± max(min_delta, std_mult * std)."""
    mask_roi = _roi_mask(roi, channel.shape)
    values = _values(channel, mask_roi)
    if values.size == 0:
        return 0.0, np.zeros(channel.shape[:2], dtype=np.uint8)
    offset = max(float(min_delta), float(std_mult) * float(values.std()))
    if high_is_foreground:
        threshold = float(values.mean()) + offset
        mask = np.where(channel > threshold, 255, 0).astype(np.uint8)
    else:
        threshold = float(values.mean()) - offset
        mask = np.where(channel < threshold, 255, 0).astype(np.uint8)
    return threshold, _restrict(mask, mask_roi)


def otsu_threshold(
    channel: np.ndarray,
    roi: np.ndarray | None,
    high_is_foreground: bool = True,
) -> tuple[float, np.ndarray]:
    """Returns (Otsu threshold, mask) computed from ROI pixels only."""
    mask_roi = _roi_mask(roi, channel.shape)
    values = _values(channel, mask_roi)
    if values.size == 0 or float(values.max()) == float(values.min()):
        return 0.0, np.zeros(channel.shape[:2], dtype=np.uint8)
    threshold = float(threshold_otsu(values))
    if high_is_foreground:
        mask = np.where(channel > threshold, 255, 0).astype(np.uint8)
    else:
        mask = np.where(channel < threshold, 255, 0).astype(np.uint8)
    return threshold, _restrict(mask, mask_roi)


def adaptive_threshold(
    channel: np.ndarray,
    roi: np.ndarray | None,
    block_size: int = ADAPTIVE_BLOCK_SIZE,
    c: float = ADAPTIVE_C,
    high_is_foreground: bool = True,
) -> tuple[float, np.ndarray]:
    """Returns (mean C, mask) using OpenCV local mean adaptive thresholding."""
    mask_roi = _roi_mask(roi, channel.shape)
    if not mask_roi.any():
        return float(c), np.zeros(channel.shape[:2], dtype=np.uint8)

    # block size must be odd and fit inside the image
    size = max(3, int(block_size))
    if size % 2 == 0:
        size += 1
    size = min(size, min(channel.shape[:2]) - (1 - min(channel.shape[:2]) % 2))
    size = max(3, size)

    method = cv2.THRESH_BINARY if high_is_foreground else cv2.THRESH_BINARY_INV
    mask = cv2.adaptiveThreshold(
        _as_uint8(channel), 255, cv2.ADAPTIVE_THRESH_MEAN_C, method, size, float(c)
    )
    return float(c), _restrict(mask, mask_roi)


def ratio_of_max_threshold(
    channel: np.ndarray,
    roi: np.ndarray | None,
    ratio: float,
) -> tuple[float, np.ndarray]:
    """Returns (ratio * local maximum, mask) computed inside the ROI."""
    mask_roi = _roi_mask(roi, channel.shape)
    values = _values(channel, mask_roi)
    if values.size == 0 or float(values.max()) <= 0:
        return 0.0, np.zeros(channel.shape[:2], dtype=np.uint8)
    threshold = float(ratio) * float(values.max())
    mask = np.where(channel >= threshold, 255, 0).astype(np.uint8)
    return threshold, _restrict(mask, mask_roi)
