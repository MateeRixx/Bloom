"""Orchestrator: src/ modules ko sahi order me chalata hai aur PipelineOutput return karta hai."""
from __future__ import annotations

import time

from src import preprocessing
from src import enhancement
from src import frequency_decomposition
from src import skin_segmentation
from src import lesion_detection
from src import postprocessing
from src import evaluation
from src import visualization


def run(image_bytes: bytes) -> dict:
    """Returns PipelineOutput dict, or {'quality': QualityResult} when the gate fails."""
    start = time.perf_counter()

    # 1. preprocess + quality gate (yahan hi BGR->RGB hota hai)
    image, quality = preprocessing.run(image_bytes)
    if not quality["passed"]:
        return {"quality": quality}

    # 2. enhancement (normalised + CLAHE)
    enhanced = enhancement.run(image)
    # 3. skin segmentation on enhanced image
    seg = skin_segmentation.run(enhanced["enhanced"])
    # 4. frequency decomposition
    freq = frequency_decomposition.run(enhanced["enhanced"])
    # 5. lesion detection
    raw = lesion_detection.run(freq, seg)
    # 6. postprocessing -> per-concern results
    concerns = postprocessing.run(raw, seg)

    # 7. baseline (naive) vs improved (refined) prediction masks
    improved_mask = evaluation.combine_masks([c["mask"] for c in concerns.values()])
    baseline_mask = lesion_detection.naive_combined_mask(enhanced["enhanced"], seg["skin_mask"])
    # 8. metrics against consensus pseudo-GT
    metrics = evaluation.run(baseline_mask, improved_mask)
    # annotated images -> base64
    images = visualization.generate_all(
        enhanced["original"], enhanced["enhanced"], seg["skin_mask"], concerns, baseline_mask
    )

    return {
        "quality": quality,
        "concerns": concerns,
        "metrics": metrics,
        "images": images,
        "processing_time_sec": round(time.perf_counter() - start, 2),
        "mediapipe_mode": seg["mediapipe_mode"],
    }


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "test_image.jpg"
    with open(path, "rb") as f:
        out = run(f.read())

    if not out["quality"]["passed"]:
        print("quality failed:", out["quality"]["issues"])
    else:
        print(f"time={out['processing_time_sec']}s mode={out['mediapipe_mode']}")
        for name, c in out["concerns"].items():
            print(f"  {name:8s} {c['severity']:<8} pct={c['area_pct']}")
        print(f"  metrics improved f1={out['metrics']['improved']['f1']}")
    print("pipeline.py: OK")
