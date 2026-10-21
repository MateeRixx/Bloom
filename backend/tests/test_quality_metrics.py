import numpy as np

from src.quality_metrics import (
    entropy,
    michelson_contrast,
    no_reference,
    psnr,
    rms_contrast,
    ssim,
    with_reference,
)


def test_identical_images_have_perfect_scores():
    image = np.random.default_rng(0).integers(0, 256, (32, 32, 3), dtype=np.uint8)
    assert psnr(image, image) == float("inf")
    assert ssim(image, image) == 1.0


def test_noise_lowers_scores():
    rng = np.random.default_rng(0)
    clean = np.full((32, 32), 128, np.uint8)
    noisy = np.clip(clean.astype(np.int16) + rng.integers(-30, 30, clean.shape), 0, 255).astype(np.uint8)
    assert psnr(clean, noisy) < 50
    assert ssim(clean, noisy) < 1.0


def test_entropy_and_contrast():
    constant = np.full((16, 16), 50, np.uint8)
    assert entropy(constant) == 0.0
    assert rms_contrast(constant) == 0.0
    assert michelson_contrast(constant) == 0.0


def test_reference_and_no_reference_dicts():
    image = np.full((16, 16, 3), 100, np.uint8)
    reference = with_reference(image, image)
    assert reference["psnr_db"] == float("inf")
    assert reference["ssim"] == 1.0
    no_ref = no_reference(image)
    assert set(no_ref) == {"entropy", "rms_contrast", "michelson_contrast"}
