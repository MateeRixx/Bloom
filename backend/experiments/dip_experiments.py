"""DIP experiment runner: FFT, edges, thresholding, restoration, histogram, features.

Synthetic runs have a known clean reference, so PSNR/SSIM are valid there.
Real-image runs report reference-free descriptors only. No detection accuracy is
claimed without independent ground-truth masks.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np

from src import (
    edge_detection,
    features,
    frequency_domain,
    histogram_processing,
    quality_metrics,
    restoration,
    thresholding,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", help="Optional real RGB image; defaults to a synthetic scene")
    parser.add_argument("--out", default="experiments/output", help="Output directory")
    return parser.parse_args()


def synthetic_scene(size: int = 256) -> tuple[np.ndarray, np.ndarray]:
    """Returns (RGB scene, circle mask) with known geometry for experiments."""
    yy, xx = np.mgrid[0:size, 0:size]
    base = np.clip(120 + 40 * np.sin(xx / 18.0) + 20 * np.cos(yy / 27.0), 0, 255)
    image = np.dstack([base, base * 0.85, base * 0.75]).astype(np.uint8)
    mask = np.zeros((size, size), np.uint8)
    for center, radius, colour in (
        ((70, 80), 18, (180, 90, 90)),
        ((160, 140), 24, (90, 120, 190)),
        ((200, 60), 12, (210, 190, 90)),
    ):
        cv2.circle(image, center, radius, colour, -1)
        cv2.circle(mask, center, radius, 255, -1)
    cv2.line(image, (20, 230), (235, 210), (40, 40, 40), 2)
    return image, mask


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_csv(path: Path, rows: list[dict]) -> None:
    """Writes rows using the union of keys, preserving first-seen order."""
    if not rows:
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_fft(image: np.ndarray, out: Path) -> None:
    result = frequency_domain.gaussian_bandpass(image)
    filtered = result["filtered"]
    peak = float(np.abs(filtered).max()) or 1.0
    display = np.clip(filtered / peak * 127.0 + 128.0, 0, 255).astype(np.uint8)
    cv2.imwrite(str(out / "fft_filtered.png"), display)
    cv2.imwrite(str(out / "fft_spectrum.png"), result["spectrum"])
    cv2.imwrite(str(out / "fft_mask.png"), (result["mask"] * 255).astype(np.uint8))


def run_edges(image: np.ndarray, out: Path) -> None:
    sobel = edge_detection.sobel_gradient(image)
    canny = edge_detection.canny_edges(image)
    laplacian = edge_detection.laplacian_map(image)
    cv2.imwrite(str(out / "edge_sobel.png"), sobel["display"])
    cv2.imwrite(str(out / "edge_canny.png"), canny)
    cv2.imwrite(str(out / "edge_laplacian.png"), laplacian["display"])


def run_thresholds(image: np.ndarray, out: Path) -> list[dict]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    roi = np.ones(gray.shape, np.uint8) * 255
    methods = {
        "mean_std": thresholding.mean_std_threshold(gray, roi, 10, 1.4, True),
        "otsu": thresholding.otsu_threshold(gray, roi, True),
        "adaptive": thresholding.adaptive_threshold(gray, roi, high_is_foreground=True),
    }
    rows = []
    for name, (threshold, mask) in methods.items():
        cv2.imwrite(str(out / f"threshold_{name}.png"), mask)
        rows.append({
            "method": name,
            "threshold": round(float(threshold), 4),
            "foreground_px": int((mask > 0).sum()),
            "foreground_pct": round(100.0 * float((mask > 0).mean()), 2),
        })
    return rows


def run_restoration(image: np.ndarray, out: Path) -> list[dict]:
    clean = image
    corruptions = {
        "salt_pepper": restoration.add_salt_pepper(clean, amount=0.03, seed=7),
        "gaussian": restoration.add_gaussian_noise(clean, sigma=15.0, seed=7),
    }
    filters = {
        "median": restoration.median_filter,
        "gaussian": restoration.gaussian_denoise,
        "wiener": restoration.wiener_filter,
    }
    rows = []
    for noise_name, noisy in corruptions.items():
        cv2.imwrite(str(out / f"restore_{noise_name}_noisy.png"), noisy)
        rows.append({"noise": noise_name, "filter": "none", **_safe_metrics(clean, noisy)})
        for filter_name, function in filters.items():
            restored = function(noisy)
            cv2.imwrite(str(out / f"restore_{noise_name}_{filter_name}.png"), restored)
            rows.append({"noise": noise_name, "filter": filter_name, **_safe_metrics(clean, restored)})
    return rows


def _safe_metrics(reference: np.ndarray, test: np.ndarray) -> dict:
    metrics = quality_metrics.with_reference(reference, test)
    if not np.isfinite(metrics["psnr_db"]):
        metrics["psnr_db"] = "inf"
    return metrics


def run_histogram(image: np.ndarray, out: Path) -> list[dict]:
    methods = histogram_processing.compare_histogram_methods(image)
    rows = []
    for name, result in methods.items():
        cv2.imwrite(str(out / f"hist_{name}.png"), cv2.cvtColor(result, cv2.COLOR_RGB2BGR))
        rows.append({"method": name, **quality_metrics.no_reference(result)})
    return rows


def run_features(image: np.ndarray, mask: np.ndarray, out: Path) -> list[dict]:
    rows = features.region_features(image, mask, concern="synthetic_circles")
    features.export_features_csv(rows, out / "features.csv")
    return rows


def main() -> None:
    args = parse_args()
    out = ensure_dir(Path(args.out))

    if args.image:
        bgr = cv2.imread(args.image, cv2.IMREAD_COLOR)
        if bgr is None:
            raise SystemExit(f"could not read image: {args.image}")
        image = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        _, synthetic_mask = synthetic_scene(256)
        synthetic_mask = cv2.resize(
            synthetic_mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST
        )
        source = args.image
    else:
        image, synthetic_mask = synthetic_scene(256)
        source = "synthetic"

    run_fft(image, out)
    run_edges(image, out)
    write_csv(out / "threshold_comparison.csv", run_thresholds(image, out))
    write_csv(out / "restoration_comparison.csv", run_restoration(image, out))
    write_csv(out / "histogram_comparison.csv", run_histogram(image, out))
    run_features(image, synthetic_mask, out)

    print(f"source: {source}")
    print(f"artifacts: {out.resolve()}")
    print("Synthetic PSNR/SSIM use the clean synthetic scene as reference.")
    print("No detection accuracy is claimed without independent ground truth.")


if __name__ == "__main__":
    main()
