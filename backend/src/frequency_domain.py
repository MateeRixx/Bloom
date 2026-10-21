"""True 2D FFT frequency-domain filtering (not spatial Gaussian/DoG).

The Gaussian band-pass removes the DC/low-frequency skin tone and keeps a
configurable mid-frequency band. Cut-offs are fractions of min(rows, cols).
"""
from __future__ import annotations

import cv2
import numpy as np

from src.config import FFT_HIGH_CUTOFF, FFT_LOW_CUTOFF


def _luminance(image: np.ndarray) -> np.ndarray:
    """Returns a float32 luminance channel from RGB or grayscale input."""
    if image.ndim == 3:
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)
    return image.astype(np.float32)


def gaussian_bandpass_mask(
    shape: tuple[int, int],
    low_cutoff: float = FFT_LOW_CUTOFF,
    high_cutoff: float = FFT_HIGH_CUTOFF,
) -> np.ndarray:
    """Returns a centered Gaussian band-pass mask with values in [0, 1]."""
    if not (0 < low_cutoff < high_cutoff <= 0.5):
        raise ValueError("Require 0 < low_cutoff < high_cutoff <= 0.5")
    rows, cols = shape
    min_side = min(rows, cols)
    low = low_cutoff * min_side
    high = high_cutoff * min_side
    u = np.arange(rows) - rows / 2
    v = np.arange(cols) - cols / 2
    dist_sq = u[:, None] ** 2 + v[None, :] ** 2
    # high-pass (remove low frequencies) * low-pass (remove high frequencies)
    high_pass = 1.0 - np.exp(-dist_sq / (2.0 * low ** 2))
    low_pass = np.exp(-dist_sq / (2.0 * high ** 2))
    return (high_pass * low_pass).astype(np.float32)


def magnitude_spectrum(channel: np.ndarray) -> np.ndarray:
    """Returns a centered log-magnitude spectrum scaled to uint8 for display only."""
    spectrum = np.abs(np.fft.fftshift(np.fft.fft2(channel)))
    log_spectrum = np.log1p(spectrum)
    peak = float(log_spectrum.max())
    if peak <= 0:
        return np.zeros_like(channel, dtype=np.uint8)
    return np.clip(log_spectrum / peak * 255.0, 0, 255).astype(np.uint8)


def gaussian_bandpass(
    image: np.ndarray,
    low_cutoff: float = FFT_LOW_CUTOFF,
    high_cutoff: float = FFT_HIGH_CUTOFF,
) -> dict:
    """Returns {filtered, mask, spectrum} for a Gaussian FFT band-pass.

    ``filtered`` is a float32 response in the original intensity scale;
    ``spectrum`` is display-normalized uint8 and must not be used as data.
    """
    channel = _luminance(image)
    if channel.size == 0:
        raise ValueError("gaussian_bandpass received an empty image")

    mask = gaussian_bandpass_mask(channel.shape, low_cutoff, high_cutoff)
    centered = np.fft.fftshift(np.fft.fft2(channel))
    filtered = np.real(np.fft.ifft2(np.fft.ifftshift(centered * mask))).astype(np.float32)

    return {
        "filtered": filtered,
        "mask": mask,
        "spectrum": magnitude_spectrum(channel),
    }


if __name__ == "__main__":
    import sys

    from src.preprocessing import load_image_from_bytes

    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m src.frequency_domain <image>")
    with open(sys.argv[1], "rb") as f:
        image = load_image_from_bytes(f.read())
    result = gaussian_bandpass(image)
    print(f"filtered shape={result['filtered'].shape} dtype={result['filtered'].dtype}")
    print(f"mask range=({result['mask'].min():.3f}, {result['mask'].max():.3f})")
    print("frequency_domain.py: OK")
