"""Generate blank 512x512 ground-truth templates for manual annotation.

These files are empty templates, not ground truth. Paint white (255) over visible
lesions and leave background black (0), then mark the manifest row annotated.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from src.config import RESIZE_TARGET

CONCERNS = ("acne", "redness", "blemish")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="evaluation", help="Evaluation dataset directory")
    parser.add_argument("--image-id", required=True, help="Manifest image_id (no extension)")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing masks")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    gt_dir = Path(args.dataset) / "ground_truth"
    gt_dir.mkdir(parents=True, exist_ok=True)
    blank = np.zeros((RESIZE_TARGET[1], RESIZE_TARGET[0]), dtype=np.uint8)
    for concern in CONCERNS:
        target = gt_dir / f"{args.image_id}_{concern}.png"
        if target.exists() and not args.overwrite:
            print(f"skip existing: {target}")
            continue
        if not cv2.imwrite(str(target), blank):
            raise RuntimeError(f"failed to write {target}")
        print(f"wrote blank template: {target}")


if __name__ == "__main__":
    main()
