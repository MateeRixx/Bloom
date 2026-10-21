"""Image-quality metrics with explicit reference assumptions.

PSNR/SSIM are only reported when a clean reference exists (e.g. controlled
synthetic corruption). Entropy/contrast need no reference but are not proof of
better diagnostic quality.
"""
from __future__ import annotations

import cv2
import numpy as np
from skimage.measure import shannon_entropy
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def _gray(image: np.ndarray) -> np.ndarray:
    """Returns uint8 grayscale."""
    if image.ndim == 3:
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return image.astype(np.uint8)


def psnr(reference: np.ndarray, test: np.ndarray, data_range: int = 255) -> float:
    """Returns PSNR in dB; ``inf`` when the images are identical."""
    if reference.shape != test.shape:
        raise ValueError("reference and test must have the same shape")
    return float(peak_signal_noise_ratio(reference, test, data_range=data_range))


def ssim(reference: np.ndarray, test: np.ndarray, data_range: int = 255) -> float:
    """Returns mean SSIM; channel axis is handled for RGB inputs."""
    if reference.shape != test.shape:
        raise ValueError("reference and test must have the same shape")
    channel_axis = -1 if reference.ndim == 3 else None
    return float(structural_similarity(reference, test, data_range=data_range, channel_axis=channel_axis))


def entropy(image: np.ndarray) -> float:
    """Returns Shannon entropy of the grayscale histogram."""
    return float(shannon_entropy(_gray(image)))


def rms_contrast(image: np.ndarray) -> float:
    """Returns root-mean-square contrast (standard deviation of luminance)."""
    return float(_gray(image).astype(np.float32).std())


def michelson_contrast(image: np.ndarray) -> float:
    """Returns Michelson contrast (max-min)/(max+min) for luminance."""
    gray = _gray(image).astype(np.float32)
    high, low = float(gray.max()), float(gray.min())
    if high + low == 0:
        return 0.0
    return (high - low) / (high + low)


def with_reference(reference: np.ndarray, test: np.ndarray) -> dict:
    """Returns PSNR/SSIM/entropy/contrast for a reference-backed comparison."""
    return {
        "psnr_db": psnr(reference, test),
        "ssim": round(ssim(reference, test), 4),
        "entropy": round(entropy(test), 4),
        "rms_contrast": round(rms_contrast(test), 4),
        "michelson_contrast": round(michelson_contrast(test), 4),
    }


def no_reference(image: np.ndarray) -> dict:
    """Returns reference-free entropy/contrast descriptors."""
    return {
        "entropy": round(entropy(image), 4),
        "rms_contrast": round(rms_contrast(image), 4),
        "michelson_contrast": round(michelson_contrast(image), 4),
    }
