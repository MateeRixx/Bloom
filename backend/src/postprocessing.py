"""Mask cleanup -> min-area filter -> region props -> severity + confidence. Raw masks ko ConcernResult banata hai."""
from __future__ import annotations

import cv2
import numpy as np
from skimage.measure import label as sk_label, regionprops

from src.config import (
    MIN_LESION_AREA_PX,
    LESION_MORPH_KERNEL,
    SEVERITY,
    CONF_HIGH_AREA_MULT,
    CONF_MED_AREA_MULT,
    CONF_HIGH_REGION_COUNT,
    CONF_MED_REGION_COUNT,
)


def _region_confidence(area_px: int) -> str:
    """Returns per-region confidence from its pixel area."""
    if area_px >= CONF_HIGH_AREA_MULT * MIN_LESION_AREA_PX:
        return "High"
    if area_px >= CONF_MED_AREA_MULT * MIN_LESION_AREA_PX:
        return "Medium"
    return "Low"


def _severity(concern: str, area_pct: float) -> str:
    """Returns 'Mild' | 'Moderate' | 'Severe' from area percentage."""
    band = SEVERITY[concern]
    if area_pct >= band["Moderate"]:
        return "Severe"
    if area_pct >= band["Mild"]:
        return "Moderate"
    return "Mild"


def _confidence(concern: str, count: int, area_pct: float) -> str:
    """Returns overall 'High' | 'Medium' | 'Low' confidence for a concern."""
    band = SEVERITY[concern]
    if count >= CONF_HIGH_REGION_COUNT or area_pct >= band["Moderate"]:
        return "High"
    if count >= CONF_MED_REGION_COUNT or area_pct >= band["Mild"]:
        return "Medium"
    return "Low"


def process_concern(raw_mask: np.ndarray, concern: str, skin_area: int) -> dict:
    """Returns ConcernResult (mask, count, area_px, area_pct, severity, confidence, regions)."""
    # speckle hatao
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, LESION_MORPH_KERNEL)
    cleaned = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel)

    # connected components + per-region props
    labels = sk_label(cleaned > 0, connectivity=2)
    kept = np.zeros_like(cleaned)
    regions: list[dict] = []
    for prop in regionprops(labels):
        if prop.area < MIN_LESION_AREA_PX:
            continue  # noise
        kept[labels == prop.label] = 255
        regions.append({
            "id": len(regions) + 1,
            "area_px": int(prop.area),
            "centroid": (float(prop.centroid[0]), float(prop.centroid[1])),
            "bbox": (int(prop.bbox[0]), int(prop.bbox[1]), int(prop.bbox[2]), int(prop.bbox[3])),
            "confidence": _region_confidence(int(prop.area)),
        })

    area_px = int((kept > 0).sum())
    area_pct = round(100.0 * area_px / skin_area, 2) if skin_area else 0.0
    # redness ek diffuse region hai, isliye count N/A (-1)
    count = -1 if concern == "redness" else len(regions)

    return {
        "mask": kept,
        "count": count,
        "area_px": area_px,
        "area_pct": area_pct,
        "severity": _severity(concern, area_pct),
        "confidence": _confidence(concern, count, area_pct),
        "regions": regions,
    }


def run(raw_masks: dict, segmentation: dict) -> dict:
    """Returns {acne, redness, blemish} ConcernResult dicts."""
    skin_area = int((segmentation["analysis_zone"] > 0).sum())
    return {name: process_concern(mask, name, skin_area) for name, mask in raw_masks.items()}


if __name__ == "__main__":
    import sys

    from src.preprocessing import run as preprocess
    from src.enhancement import run as enhance
    from src.frequency_decomposition import run as decompose
    from src.skin_segmentation import run as segment
    from src.lesion_detection import run as detect

    path = sys.argv[1] if len(sys.argv) > 1 else "test_image.jpg"
    with open(path, "rb") as f:
        image, _ = preprocess(f.read())

    enhanced = enhance(image)["enhanced"]
    results = run(detect(decompose(enhanced), segment(enhanced)), segment(enhanced))
    for name, res in results.items():
        print(f"{name:8s} count={res['count']:<3} area_px={res['area_px']:<5} "
              f"area_pct={res['area_pct']:<5} severity={res['severity']:<8} "
              f"confidence={res['confidence']} regions={len(res['regions'])}")
    print("postprocessing.py: OK")
