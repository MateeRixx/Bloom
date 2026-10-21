"""Independent mask metrics. No ground truth is derived from predictions here.

Conventions
-----------
- Masks are 2D arrays; any non-zero pixel is foreground.
- Both empty: IoU = Dice = 1. Precision/recall/F1 are undefined (``None``).
- GT empty, prediction non-empty: IoU = Dice = 0, precision = 0, recall/F1 = ``None``.
- Prediction empty, GT non-empty: IoU = Dice = 0, recall = 0, precision/F1 = ``None``.
- Otherwise all five metrics are defined.
- Aggregation is a macro-average across images/classes; undefined values are
  excluded and the number excluded is reported per metric.
"""
from __future__ import annotations

import numpy as np

METRIC_KEYS = ("iou", "dice", "precision", "recall", "f1")


def validate_binary_mask(mask: np.ndarray, name: str = "mask") -> np.ndarray:
    """Returns a boolean mask after validating shape and values."""
    if mask is None:
        raise ValueError(f"{name} is None")
    arr = np.asarray(mask)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be 2D, got shape {arr.shape}")
    unique = np.unique(arr)
    allowed = {0, 1, 255}
    if not set(np.unique(unique).tolist()).issubset(allowed):
        raise ValueError(f"{name} must contain only 0/1/255, got values {unique[:10].tolist()}")
    return arr > 0


def compute_pixel_metrics(pred: np.ndarray, gt: np.ndarray) -> dict:
    """Returns pixel metrics and support counts for one prediction/GT pair."""
    p = validate_binary_mask(pred, "prediction")
    g = validate_binary_mask(gt, "ground_truth")
    if p.shape != g.shape:
        raise ValueError(f"prediction shape {p.shape} != ground_truth shape {g.shape}")

    tp = int(np.logical_and(p, g).sum())
    fp = int(np.logical_and(p, ~g).sum())
    fn = int(np.logical_and(~p, g).sum())

    if tp + fp + fn == 0:
        return {
            "iou": 1.0, "dice": 1.0,
            "precision": None, "recall": None, "f1": None,
            "tp": 0, "fp": 0, "fn": 0, "gt_pixels": 0, "pred_pixels": 0,
        }

    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    iou = tp / (tp + fp + fn)
    dice = 2 * tp / (2 * tp + fp + fn)
    f1 = (2 * precision * recall / (precision + recall)) if (precision and recall) else None
    # If one side is empty, F1 is 0 because there are no true positives.
    if precision == 0 or recall == 0:
        f1 = 0.0

    return {
        "iou": round(float(iou), 4),
        "dice": round(float(dice), 4),
        "precision": None if precision is None else round(float(precision), 4),
        "recall": None if recall is None else round(float(recall), 4),
        "f1": None if f1 is None else round(float(f1), 4),
        "tp": tp, "fp": fp, "fn": fn,
        "gt_pixels": int(g.sum()), "pred_pixels": int(p.sum()),
    }


def aggregate_metrics(rows: list[dict]) -> dict:
    """Returns macro mean/median and valid/excluded counts for each metric."""
    out: dict = {"n_pairs": len(rows)}
    for key in METRIC_KEYS:
        values = [row[key] for row in rows if row.get(key) is not None]
        out[key] = {
            "macro_mean": round(float(np.mean(values)), 4) if values else None,
            "macro_median": round(float(np.median(values)), 4) if values else None,
            "n_valid": len(values),
            "n_excluded": len(rows) - len(values),
        }
    out["support"] = {
        "tp": int(sum(row.get("tp", 0) for row in rows)),
        "fp": int(sum(row.get("fp", 0) for row in rows)),
        "fn": int(sum(row.get("fn", 0) for row in rows)),
        "gt_pixels": int(sum(row.get("gt_pixels", 0) for row in rows)),
        "pred_pixels": int(sum(row.get("pred_pixels", 0) for row in rows)),
    }
    return out


def combine_masks(masks: list[np.ndarray]) -> np.ndarray:
    """Returns union of binary masks (visualization only)."""
    if not masks:
        raise ValueError("combine_masks requires at least one mask")
    out = np.zeros_like(masks[0])
    for mask in masks:
        validate_binary_mask(mask, "mask")
        out = np.logical_or(out, mask > 0).astype(np.uint8) * 255
    return out
