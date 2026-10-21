import numpy as np
import pytest

from src.evaluation import aggregate_metrics, compute_pixel_metrics, validate_binary_mask


def test_both_empty_is_perfect_for_overlap_but_precision_recall_undefined():
    empty = np.zeros((10, 10), np.uint8)
    metrics = compute_pixel_metrics(empty, empty)
    assert metrics["iou"] == 1.0
    assert metrics["dice"] == 1.0
    assert metrics["precision"] is None
    assert metrics["recall"] is None
    assert metrics["f1"] is None


def test_gt_empty_prediction_nonempty():
    pred = np.zeros((10, 10), np.uint8)
    pred[2:4, 2:4] = 1
    gt = np.zeros((10, 10), np.uint8)
    metrics = compute_pixel_metrics(pred, gt)
    assert metrics["iou"] == 0.0
    assert metrics["dice"] == 0.0
    assert metrics["precision"] == 0.0
    assert metrics["recall"] is None
    assert metrics["f1"] == 0.0


def test_prediction_empty_gt_nonempty():
    pred = np.zeros((10, 10), np.uint8)
    gt = np.zeros((10, 10), np.uint8)
    gt[0:2, 0:2] = 255
    metrics = compute_pixel_metrics(pred, gt)
    assert metrics["iou"] == 0.0
    assert metrics["precision"] is None
    assert metrics["recall"] == 0.0
    assert metrics["f1"] == 0.0


def test_known_overlap_values():
    pred = np.zeros((4, 4), np.uint8)
    gt = np.zeros((4, 4), np.uint8)
    pred[0:2, 0:2] = 1  # 4 px
    gt[1:3, 1:3] = 1    # 4 px, overlap 1
    metrics = compute_pixel_metrics(pred, gt)
    assert metrics["tp"] == 1
    assert metrics["fp"] == 3
    assert metrics["fn"] == 3
    assert metrics["iou"] == pytest.approx(1 / 7, abs=1e-4)
    assert metrics["precision"] == 0.25
    assert metrics["recall"] == 0.25


def test_shape_mismatch_and_bad_values_raise():
    with pytest.raises(ValueError):
        compute_pixel_metrics(np.zeros((4, 4)), np.zeros((5, 5)))
    with pytest.raises(ValueError):
        validate_binary_mask(np.full((4, 4), 7))


def test_macro_aggregation_excludes_undefined_values():
    rows = [
        {"iou": 1.0, "dice": 1.0, "precision": None, "recall": None, "f1": None,
         "tp": 0, "fp": 0, "fn": 0, "gt_pixels": 0, "pred_pixels": 0},
        {"iou": 0.5, "dice": 0.5, "precision": 0.5, "recall": 0.5, "f1": 0.5,
         "tp": 1, "fp": 1, "fn": 1, "gt_pixels": 2, "pred_pixels": 2},
    ]
    summary = aggregate_metrics(rows)
    assert summary["iou"]["macro_mean"] == 0.75
    assert summary["precision"]["macro_mean"] == 0.5
    assert summary["precision"]["n_valid"] == 1
    assert summary["precision"]["n_excluded"] == 1
    assert summary["n_pairs"] == 2
