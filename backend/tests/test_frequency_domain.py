import numpy as np
import pytest

from src.frequency_domain import gaussian_bandpass, gaussian_bandpass_mask


def test_constant_image_is_removed_by_bandpass():
    image = np.full((64, 64, 3), 128, np.uint8)
    result = gaussian_bandpass(image)
    assert np.abs(result["filtered"]).max() < 1e-3
    assert result["spectrum"].dtype == np.uint8


def test_impulse_has_nonzero_bandpass_response():
    image = np.zeros((64, 64), np.uint8)
    image[32, 32] = 255
    result = gaussian_bandpass(image)
    assert np.abs(result["filtered"]).max() > 0


def test_in_band_sinusoid_passes_bandpass():
    size = 128
    x = np.arange(size)
    frequency = 0.1  # cycles/pixel, inside 0.02-0.25 band
    sinusoid = (127.5 + 100 * np.sin(2 * np.pi * frequency * x)).astype(np.uint8)
    image = np.tile(sinusoid, (size, 1))
    result = gaussian_bandpass(image, low_cutoff=0.02, high_cutoff=0.25)
    input_rms = float(image.astype(np.float32).std())
    output_rms = float(result["filtered"].std())
    assert output_rms > 0.5 * input_rms


def test_invalid_cutoffs_raise():
    with pytest.raises(ValueError):
        gaussian_bandpass_mask((32, 32), low_cutoff=0.3, high_cutoff=0.2)
    with pytest.raises(ValueError):
        gaussian_bandpass_mask((32, 32), low_cutoff=0.0, high_cutoff=0.2)
