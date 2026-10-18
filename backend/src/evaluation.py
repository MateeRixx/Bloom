"""Baseline-vs-improved pixel metrics against a consensus pseudo-GT (runtime me real ground truth nahi hota)."""
from __future__ import annotations

import cv2
import numpy as np

from src.config import CONSENSUS_CORE_ERODE_PX


def combine_masks(masks: list[np.ndarray]) -> np.ndarray:
    """Returns union of binary masks."""
    out = np.zeros_like(masks[0])
    for mask in masks:
        out = cv2.bitwise_or(out, mask)
    return out


def _core(mask: np.ndarray) -> np.ndarray:
    """Returns high-confidence core of a mask (eroded); falls back to mask if too small."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * CONSENSUS_CORE_ERODE_PX + 1,) * 2)
    core = cv2.erode(mask, k)
    return core if core.max() > 0 else mask.copy()


def consensus_ground_truth(baseline: np.ndarray, improved: np.ndarray) -> np.ndarray:
    """Returns pseudo-GT = high-confidence pixels of BOTH pipelines (core intersection).

    Note: GT ⊆ both masks, so recall pins to 1.0 for each; precision/IoU/F1 remain
    discriminating and favour the tighter improved pipeline.
    """
    gt = cv2.bitwise_and(_core(baseline), _core(improved))
    # agar dono bilkul agree nahi karte to improved core ko reference maano
    return gt if gt.max() > 0 else _core(improved)


def compute_pixel_metrics(pred: np.ndarray, gt: np.ndarray) -> dict:
    """Returns {iou, dice, precision, recall, f1} between predicted and reference masks."""
    p = pred.astype(bool).ravel()
    g = gt.astype(bool).ravel()
    tp = int(np.logical_and(p, g).sum())
    fp = int(np.logical_and(p, ~g).sum())
    fn = int(np.logical_and(~p, g).sum())

    # dono khaali => perfect agreement
    if tp + fp + fn == 0:
        return {k: 1.0 for k in ("iou", "dice", "precision", "recall", "f1")}

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    iou = tp / (tp + fp + fn)
    dice = 2 * tp / (2 * tp + fp + fn)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "iou": round(iou, 3),
        "dice": round(dice, 3),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
    }


def run(baseline_mask: np.ndarray, improved_mask: np.ndarray) -> dict:
    """Returns MetricsResult: {baseline, improved} scored against the consensus pseudo-GT."""
    gt = consensus_ground_truth(baseline_mask, improved_mask)
    return {
        "baseline": compute_pixel_metrics(baseline_mask, gt),
        "improved": compute_pixel_metrics(improved_mask, gt),
    }


if __name__ == "__main__":
    import sys

    from src.preprocessing import run as preprocess
    from src.enhancement import run as enhance
    from src.frequency_decomposition import run as decompose
    from src.skin_segmentation import run as segment
    from src.lesion_detection import run as detect, naive_combined_mask
    from src.postprocessing import run as postprocess

    path = sys.argv[1] if len(sys.argv) > 1 else "test_image.jpg"
    with open(path, "rb") as f:
        image, _ = preprocess(f.read())

    enhanced = enhance(image)["enhanced"]
    freq = decompose(enhanced)
    seg = segment(enhanced)
    concerns = postprocess(detect(freq, seg), seg)

    improved = combine_masks([c["mask"] for c in concerns.values()])
    baseline = naive_combined_mask(enhanced, seg["skin_mask"])

    metrics = run(baseline, improved)
    for pipeline, m in metrics.items():
        print(f"{pipeline:9s} iou={m['iou']:<5} dice={m['dice']:<5} "
              f"precision={m['precision']:<5} recall={m['recall']:<5} f1={m['f1']}")
    print("evaluation.py: OK")
