import numpy as np

from src.histogram_processing import compare_histogram_methods, equalize_luminance, gamma_correct
from src.quality_metrics import rms_contrast


def test_equalization_increases_low_contrast():
    image = np.full((64, 64, 3), 120, np.uint8)
    image[16:48, 16:48] = 136
    equalized = equalize_luminance(image)
    assert rms_contrast(equalized) > rms_contrast(image)


def test_gamma_identity_and_brightening():
    image = np.full((8, 8, 3), 100, np.uint8)
    assert np.array_equal(gamma_correct(image, 1.0), image)
    brighter = gamma_correct(image, 0.5)
    assert brighter.mean() > image.mean()


def test_compare_methods_keys():
    image = np.full((16, 16, 3), 128, np.uint8)
    result = compare_histogram_methods(image)
    assert set(result) == {"original", "global_equalized", "clahe", "gamma"}
