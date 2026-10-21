import numpy as np

from src.restoration import (
    add_gaussian_noise,
    add_salt_pepper,
    gaussian_denoise,
    median_filter,
    wiener_filter,
)


def _mae(a, b):
    return float(np.abs(a.astype(np.float32) - b.astype(np.float32)).mean())


def test_median_filter_reduces_impulse_noise():
    clean = np.full((64, 64), 128, np.uint8)
    noisy = add_salt_pepper(clean, amount=0.05, seed=3)
    restored = median_filter(noisy, 5)
    assert _mae(restored, clean) < _mae(noisy, clean)


def test_gaussian_filter_reduces_gaussian_error():
    clean = np.full((64, 64), 128, np.uint8)
    noisy = add_gaussian_noise(clean, sigma=20, seed=3)
    restored = gaussian_denoise(noisy, sigma=2.0)
    assert _mae(restored, clean) < _mae(noisy, clean)


def test_wiener_preserves_shape_and_dtype():
    image = np.random.default_rng(0).integers(0, 256, (48, 48, 3), dtype=np.uint8)
    restored = wiener_filter(image)
    assert restored.shape == image.shape
    assert restored.dtype == np.uint8


def test_salt_pepper_amount_validation():
    import pytest
    with pytest.raises(ValueError):
        add_salt_pepper(np.zeros((8, 8), np.uint8), amount=2)
