"""Per-region texture, colour, edge, and shape features (CSV-exportable).

Features describe image regions; they do not identify a medical condition.
"""
from __future__ import annotations

import csv
from pathlib import Path

import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
from skimage.measure import label as sk_label
from skimage.measure import regionprops

from src.config import (
    GLCM_ANGLES,
    GLCM_DISTANCES,
    GLCM_LEVELS,
    LBP_POINTS,
    LBP_RADIUS,
)
from src.edge_detection import canny_edges, edge_density

FEATURE_FIELDS = [
    "concern", "region_id", "area_px", "perimeter_px", "circularity",
    "aspect_ratio", "extent", "solidity", "mean_l", "mean_a", "mean_b",
    "edge_density", "glcm_contrast", "glcm_homogeneity", "glcm_energy",
    "glcm_correlation", "lbp_entropy",
]


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Returns numerator/denominator or 0 when the denominator is zero."""
    return float(numerator / denominator) if denominator else 0.0


def _glcm_features(gray_crop: np.ndarray) -> dict:
    """Returns GLCM properties for a grayscale crop, or Nones when too small."""
    if gray_crop.shape[0] < 2 or gray_crop.shape[1] < 2:
        return {key: None for key in ("glcm_contrast", "glcm_homogeneity", "glcm_energy", "glcm_correlation")}
    scale = 256.0 / GLCM_LEVELS
    quantized = np.clip(gray_crop.astype(np.float32) / scale, 0, GLCM_LEVELS - 1).astype(np.uint8)
    matrix = graycomatrix(quantized, GLCM_DISTANCES, GLCM_ANGLES, levels=GLCM_LEVELS, symmetric=True, normed=True)
    return {
        "glcm_contrast": round(float(graycoprops(matrix, "contrast").mean()), 4),
        "glcm_homogeneity": round(float(graycoprops(matrix, "homogeneity").mean()), 4),
        "glcm_energy": round(float(graycoprops(matrix, "energy").mean()), 4),
        "glcm_correlation": round(float(graycoprops(matrix, "correlation").mean()), 4),
    }


def _lbp_entropy(gray_crop: np.ndarray) -> float | None:
    """Returns Shannon entropy of a uniform LBP histogram, or None when too small."""
    if gray_crop.shape[0] < 3 or gray_crop.shape[1] < 3:
        return None
    lbp = local_binary_pattern(gray_crop, LBP_POINTS, LBP_RADIUS, method="uniform")
    hist, _ = np.histogram(lbp.ravel(), bins=LBP_POINTS + 2, range=(0, LBP_POINTS + 2), density=False)
    total = hist.sum()
    if total == 0:
        return None
    probabilities = hist / total
    probabilities = probabilities[probabilities > 0]
    return round(float(-(probabilities * np.log2(probabilities)).sum()), 4)


def region_features(image: np.ndarray, mask: np.ndarray, concern: str = "region") -> list[dict]:
    """Returns one feature row per connected component in ``mask``."""
    if image.ndim != 3:
        raise ValueError("region_features expects an RGB image")
    if image.shape[:2] != mask.shape[:2]:
        raise ValueError("image and mask dimensions do not match")

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    edges = canny_edges(image)
    labels = sk_label(mask > 0, connectivity=2)
    rows: list[dict] = []

    for region_id, prop in enumerate(regionprops(labels), start=1):
        min_row, min_col, max_row, max_col = prop.bbox
        height = max_row - min_row
        width = max_col - min_col
        box_area = float(height * width)
        perimeter = float(prop.perimeter) if hasattr(prop, "perimeter") else 0.0
        circularity = _safe_ratio(4.0 * np.pi * prop.area, perimeter ** 2)
        aspect = _safe_ratio(max(height, width), min(height, width))
        extent = _safe_ratio(prop.area, box_area)
        solidity = float(prop.solidity)
        region_mask = labels == prop.label

        gray_crop = gray[min_row:max_row, min_col:max_col]
        color_crop = lab[min_row:max_row, min_col:max_col]
        region_pixels = color_crop[region_mask[min_row:max_row, min_col:max_col]]
        if region_pixels.size:
            mean_l, mean_a, mean_b = [round(float(v), 4) for v in region_pixels.mean(axis=0)]
        else:
            mean_l = mean_a = mean_b = 0.0

        row = {
            "concern": concern,
            "region_id": region_id,
            "area_px": int(prop.area),
            "perimeter_px": round(perimeter, 4),
            "circularity": round(circularity, 4),
            "aspect_ratio": round(aspect, 4),
            "extent": round(extent, 4),
            "solidity": round(solidity, 4),
            "mean_l": mean_l,
            "mean_a": mean_a,
            "mean_b": mean_b,
            "edge_density": round(edge_density(edges, region_mask), 4),
        }
        row.update(_glcm_features(gray_crop))
        row["lbp_entropy"] = _lbp_entropy(gray_crop)
        rows.append(row)

    return rows


def concern_features(image: np.ndarray, masks: dict) -> dict:
    """Returns {concern: [feature rows]} for every mask."""
    return {name: region_features(image, mask, concern=name) for name, mask in masks.items()}


def export_features_csv(rows: list[dict], path: str | Path) -> Path:
    """Writes feature rows to CSV and returns the path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FEATURE_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in FEATURE_FIELDS})
    return target
