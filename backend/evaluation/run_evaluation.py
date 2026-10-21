"""Run baseline and improved methods on independently annotated images.

Usage (from backend/):
    python -m evaluation.run_evaluation --dataset evaluation --out evaluation/results/run_001

The script never derives ground truth from predictions. If no annotated images
exist, it writes a pending status file and exits without performance numbers.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path

import cv2
import numpy as np

import pipeline
from src import config
from src.errors import FaceLandmarkError, InvalidImageError
from src.evaluation import aggregate_metrics, compute_pixel_metrics, validate_binary_mask
from src.image_validation import inspect_image

CONCERNS = ("acne", "redness", "blemish")
METHODS = ("baseline", "improved")
REQUIRED_COLUMNS = {
    "image_id", "image_file", "source", "license", "width", "height",
    "annotation_status", "concerns", "notes",
}
METRIC_FIELDS = [
    "image_id", "concern", "method", "iou", "dice", "precision", "recall", "f1",
    "tp", "fp", "fn", "gt_pixels", "pred_pixels",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="evaluation", help="Dataset root directory")
    parser.add_argument("--out", default="evaluation/results/latest", help="Output directory")
    return parser.parse_args()


def read_manifest(path: Path) -> list[dict]:
    """Returns manifest rows, validating required columns."""
    if not path.exists():
        raise FileNotFoundError(f"manifest not found: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"manifest missing columns: {sorted(missing)}")
        return [row for row in reader if row.get("image_id")]


def load_ground_truth(path: Path, expected_shape: tuple[int, int]) -> np.ndarray:
    """Loads and validates a binary mask at exactly the prediction resolution."""
    if not path.exists():
        raise FileNotFoundError(f"missing ground truth: {path}")
    mask = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise ValueError(f"could not read ground truth: {path}")
    if mask.shape != expected_shape:
        raise ValueError(
            f"ground truth {path.name} is {mask.shape}, expected {expected_shape}; "
            "do not silently resize annotations"
        )
    validate_binary_mask(mask, path.name)
    return np.where(mask > 0, 255, 0).astype(np.uint8)


def save_mask(path: Path, mask: np.ndarray) -> None:
    """Writes a binary prediction mask."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), np.where(mask > 0, 255, 0).astype(np.uint8)):
        raise RuntimeError(f"failed to write {path}")


def dataset_version(manifest_path: Path, gt_files: list[Path]) -> str:
    """Returns a SHA-256 over the manifest and all ground-truth masks."""
    digest = hashlib.sha256()
    digest.update(manifest_path.read_bytes())
    for path in sorted(gt_files):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def config_snapshot() -> dict:
    """Returns JSON-serializable uppercase config values."""
    allowed = (int, float, str, bool, tuple, list, dict, type(None))
    return {
        key: value for key, value in vars(config).items()
        if key.isupper() and isinstance(value, allowed)
    }


def software_versions() -> dict:
    """Returns interpreter and package versions used for the run."""
    from importlib.metadata import PackageNotFoundError, version

    packages = {}
    for name in ("numpy", "opencv-contrib-python", "scikit-image", "scipy", "Pillow", "mediapipe"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    return {"python": sys.version.split()[0], "platform": platform.platform(), "packages": packages}


def write_json(path: Path, payload: dict) -> None:
    """Writes deterministic JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    dataset = Path(args.dataset)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = dataset / "manifest.csv"
    rows = read_manifest(manifest_path)

    annotated = [row for row in rows if row.get("annotation_status") == "annotated"]
    gt_files = [
        dataset / "ground_truth" / f"{row['image_id']}_{concern}.png"
        for row in annotated for concern in CONCERNS
    ]
    version = dataset_version(manifest_path, [path for path in gt_files if path.exists()])

    if not annotated:
        write_json(out / "status.json", {
            "status": "pending",
            "reason": "No rows with annotation_status=annotated in manifest.csv",
            "dataset": str(dataset),
            "dataset_version": version,
            "n_images": len(rows),
            "n_annotated": 0,
        })
        print("PENDING: no annotated images. Add manual masks and mark manifest rows annotated.")
        print(f"Wrote {out / 'status.json'}")
        return

    per_image: list[dict] = []
    errors: list[dict] = []
    used_images = 0

    for row in annotated:
        image_id = row["image_id"]
        image_path = dataset / "images" / row["image_file"]
        try:
            if not image_path.exists():
                raise FileNotFoundError(f"missing image: {image_path}")
            inspect_image(image_path.read_bytes())
            stages = pipeline.run_stages(image_path.read_bytes())
            if not stages["quality"]["passed"]:
                raise ValueError(f"quality gate failed: {stages['quality']['issues']}")
        except (FaceLandmarkError, InvalidImageError, ValueError, FileNotFoundError, RuntimeError) as exc:
            errors.append({"image_id": image_id, "error": str(exc), "type": type(exc).__name__})
            continue

        expected_shape = stages["concerns"]["acne"]["mask"].shape
        try:
            for concern in CONCERNS:
                gt = load_ground_truth(
                    dataset / "ground_truth" / f"{image_id}_{concern}.png", expected_shape
                )
                methods = {
                    "baseline": stages["baseline_masks"][concern],
                    "improved": stages["concerns"][concern]["mask"],
                }
                for method, prediction in methods.items():
                    save_mask(
                        out / "predictions" / f"{image_id}_{concern}_{method}.png",
                        prediction,
                    )
                    metrics = compute_pixel_metrics(prediction, gt)
                    per_image.append({
                        "image_id": image_id,
                        "concern": concern,
                        "method": method,
                        **metrics,
                    })
        except (FileNotFoundError, ValueError) as exc:
            errors.append({"image_id": image_id, "error": str(exc), "type": type(exc).__name__})
            continue
        used_images += 1

    csv_path = out / "metrics_per_image.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDS)
        writer.writeheader()
        for row in per_image:
            writer.writerow({key: row.get(key) for key in METRIC_FIELDS})

    summary: dict = {
        "status": "complete" if used_images else "pending",
        "dataset": {
            "path": str(dataset),
            "version": version,
            "n_manifest_rows": len(rows),
            "n_annotated": len(annotated),
            "n_used": used_images,
        },
        "config": config_snapshot(),
        "software": software_versions(),
        "errors": errors,
        "groups": {},
    }
    for method in METHODS:
        for concern in CONCERNS + ("all",):
            subset = [
                row for row in per_image
                if row["method"] == method and (concern == "all" or row["concern"] == concern)
            ]
            if subset:
                summary["groups"][f"{method}_{concern}"] = aggregate_metrics(subset)

    write_json(out / "summary.json", summary)
    write_json(out / "status.json", {
        "status": summary["status"],
        "dataset": summary["dataset"],
        "errors": errors,
        "metrics_per_image": str(csv_path),
        "summary": str(out / "summary.json"),
    })
    print(f"Processed {used_images}/{len(annotated)} annotated images")
    print(f"per-image metrics: {csv_path}")
    print(f"summary: {out / 'summary.json'}")
    if errors:
        print(f"WARNING: {len(errors)} image(s) could not be evaluated; see summary.json")


if __name__ == "__main__":
    main()
