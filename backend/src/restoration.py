"""Restoration experiments: synthetic noise, median, Gaussian, and Wiener filters.

Enhancement (CLAHE/bilateral) is separate from restoration. These functions are
used by the experiment runner, not by the production detection path.
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy.signal import wiener

from src.config import (
    GAUSSIAN_DENOISE_SIGMA,
    MEDIAN_KERNEL_SIZE,
    WIENER_KERNEL_SIZE,
    WIENER_NOISE,
)


def add_salt_pepper(image: np.ndarray, amount: float = 0.02, seed: int = 0) -> np.ndarray:
    """Returns an image with impulse (salt-and-pepper) noise."""
    if not (0 <= amount <= 1):
        raise ValueError("amount must be in [0, 1]")
    rng = np.random.default_rng(seed)
    noisy = image.copy()
    count = int(amount * image.shape[0] * image.shape[1])
    if count == 0:
        return noisy
    coords = rng.integers(0, image.shape[0] * image.shape[1], size=count)
    rows, cols = np.unravel_index(coords, image.shape[:2])
    half = count // 2
    if image.ndim == 3:
        noisy[rows[:half], cols[:half], :] = 255
        noisy[rows[half:], cols[half:], :] = 0
    else:
        noisy[rows[:half], cols[:half]] = 255
        noisy[rows[half:], cols[half:]] = 0
    return noisy


def add_gaussian_noise(image: np.ndarray, sigma: float = 10.0, seed: int = 0) -> np.ndarray:
    """Returns an image with additive zero-mean Gaussian noise."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, sigma, image.shape)
    return np.clip(image.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def median_filter(image: np.ndarray, ksize: int = MEDIAN_KERNEL_SIZE) -> np.ndarray:
    """Returns median-filtered image (good for impulse noise)."""
    size = max(3, int(ksize))
    if size % 2 == 0:
        size += 1
    return cv2.medianBlur(image, size)


def gaussian_denoise(image: np.ndarray, sigma: float = GAUSSIAN_DENOISE_SIGMA) -> np.ndarray:
    """Returns Gaussian-smoothed image (Gaussian-noise baseline)."""
    return cv2.GaussianBlur(image, (0, 0), sigmaX=float(sigma))


def wiener_filter(
    image: np.ndarray,
    kernel_size: int = WIENER_KERNEL_SIZE,
    noise: float = WIENER_NOISE,
) -> np.ndarray:
    """Returns a per-channel Wiener-filtered image."""
    size = max(3, int(kernel_size))
    if size % 2 == 0:
        size += 1
    if image.ndim == 3:
        channels = [wiener(image[:, :, c].astype(np.float32), mysize=size, noise=noise)
                    for c in range(image.shape[2])]
        out = np.stack(channels, axis=-1)
    else:
        out = wiener(image.astype(np.float32), mysize=size, noise=noise)
    return np.clip(out, 0, 255).astype(np.uint8)
