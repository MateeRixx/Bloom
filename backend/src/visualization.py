"""Annotated overlays -> base64 JPEG. API response ki saari images yahin se banti hain."""
from __future__ import annotations

import base64

import cv2
import numpy as np

from src.config import (
    ACNE_COLOUR,
    BASELINE_COLOUR,
    BLEMISH_COLOUR,
    CONTOUR_THICKNESS,
    FILL_OPACITY,
    JPEG_QUALITY,
    REDNESS_COLOUR,
    SKIN_MASK_COLOUR,
    SKIN_OVERLAY_OPACITY,
)


def encode_image_to_base64(image_rgb: np.ndarray) -> str:
    """Returns base64 JPEG string from an RGB numpy array."""
    bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)  # OpenCV encode ke liye BGR
    ok, buffer = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    if not ok:
        raise RuntimeError("JPEG encoding failed in visualization.encode_image_to_base64")
    return base64.b64encode(buffer).decode("utf-8")


def _to_bgr(colour: tuple[int, int, int]) -> tuple[int, int, int]:
    """Converts an RGB colour tuple to BGR for OpenCV drawing."""
    r, g, b = colour
    return (b, g, r)


def _fill_overlay(image: np.ndarray, mask: np.ndarray, colour: tuple[int, int, int], alpha: float) -> np.ndarray:
    """Returns image with colour blended where mask is set."""
    out = image.copy()
    sel = mask > 0
    if not sel.any():
        return out
    layer = np.zeros_like(image)
    layer[sel] = colour
    out[sel] = (1 - alpha) * out[sel] + alpha * layer[sel]
    return out.astype(np.uint8)


def _draw_contours(image: np.ndarray, mask: np.ndarray, colour: tuple[int, int, int]) -> np.ndarray:
    """Returns image with the mask outline drawn in the given RGB colour."""
    out = image.copy()
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(out, contours, -1, _to_bgr(colour), CONTOUR_THICKNESS)
    return out


def _overlay_skin_mask(image: np.ndarray, skin_mask: np.ndarray) -> np.ndarray:
    """Returns image with a translucent green skin-mask overlay."""
    return _fill_overlay(image, skin_mask, SKIN_MASK_COLOUR, SKIN_OVERLAY_OPACITY)


def annotate_concerns(image: np.ndarray, concerns: dict) -> np.ndarray:
    """Returns image with redness fill + acne/blemish contours."""
    out = _fill_overlay(image, concerns["redness"]["mask"], REDNESS_COLOUR, FILL_OPACITY)
    out = _draw_contours(out, concerns["acne"]["mask"], ACNE_COLOUR)
    out = _draw_contours(out, concerns["blemish"]["mask"], BLEMISH_COLOUR)
    return out


def annotate_mask(image: np.ndarray, mask: np.ndarray, colour: tuple[int, int, int] = BASELINE_COLOUR) -> np.ndarray:
    """Returns image with a single combined mask outlined (baseline view)."""
    return _draw_contours(image, mask, colour)


def generate_all(original: np.ndarray, enhanced: np.ndarray, skin_mask: np.ndarray,
                 concerns: dict, baseline_mask: np.ndarray) -> dict:
    """Returns VisualizationOutput dict of base64 JPEG strings."""
    # baseline aur improved dono original par => sirf detection ka farq dikhe
    return {
        "original": encode_image_to_base64(original),
        "enhanced": encode_image_to_base64(enhanced),
        "skin_mask": encode_image_to_base64(_overlay_skin_mask(original, skin_mask)),
        "baseline_annotated": encode_image_to_base64(annotate_mask(original, baseline_mask)),
        "improved_annotated": encode_image_to_base64(annotate_concerns(original, concerns)),
    }


if __name__ == "__main__":
    import sys

    from src.enhancement import run as enhance
    from src.frequency_decomposition import run as decompose
    from src.lesion_detection import naive_combined_mask
    from src.lesion_detection import run as detect
    from src.postprocessing import run as postprocess
    from src.preprocessing import run as preprocess
    from src.skin_segmentation import run as segment

    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m src.visualization <image>")
    path = sys.argv[1]
    with open(path, "rb") as f:
        image, _ = preprocess(f.read())

    enhanced = enhance(image)
    freq = decompose(enhanced["enhanced"])
    seg = segment(enhanced["enhanced"])
    concerns = postprocess(detect(freq, seg), seg)
    baseline = naive_combined_mask(enhanced["enhanced"], seg["skin_mask"])

    images = generate_all(enhanced["original"], enhanced["enhanced"], seg["skin_mask"], concerns, baseline)
    for key, b64 in images.items():
        raw = base64.b64decode(b64)
        print(f"{key:20s} b64_chars={len(b64):<8} decoded_bytes={len(raw)}")
    print("visualization.py: OK")
