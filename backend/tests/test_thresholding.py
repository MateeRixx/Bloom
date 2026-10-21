import numpy as np

from src.thresholding import (
    adaptive_threshold,
    mean_std_threshold,
    otsu_threshold,
    ratio_of_max_threshold,
)


def _bimodal():
    channel = np.full((64, 64), 20, np.uint8)
    channel[20:40, 20:40] = 220
    roi = np.ones((64, 64), np.uint8)
    return channel, roi


def test_mean_std_detects_bright_region():
    channel, roi = _bimodal()
    threshold, mask = mean_std_threshold(channel, roi, 10, 1.4, high_is_foreground=True)
    assert threshold > 20
    assert mask[30, 30] == 255
    assert mask[0, 0] == 0


def test_mean_std_handles_empty_roi():
    channel, _ = _bimodal()
    empty = np.zeros((64, 64), np.uint8)
    threshold, mask = mean_std_threshold(channel, empty, 10, 1.4)
    assert threshold == 0.0
    assert mask.max() == 0


def test_otsu_separates_bimodal_region():
    channel, roi = _bimodal()
    threshold, mask = otsu_threshold(channel, roi, high_is_foreground=True)
    assert 20 < threshold < 220
    assert mask[30, 30] == 255
    assert mask[0, 0] == 0


def test_adaptive_returns_mask_and_respects_roi():
    channel, roi = _bimodal()
    roi[0:10, :] = 0
    _, mask = adaptive_threshold(channel, roi, block_size=11, c=2)
    assert mask.shape == channel.shape
    assert mask[0, 0] == 0


def test_ratio_of_max_restricts_to_roi():
    magnitude = np.zeros((32, 32), np.float32)
    magnitude[10, 10] = 100
    roi = np.zeros((32, 32), np.uint8)
    roi[8:12, 8:12] = 255
    threshold, mask = ratio_of_max_threshold(magnitude, roi, 0.5)
    assert threshold == 50.0
    assert mask[10, 10] == 255
    assert mask[0, 0] == 0
