"""Safe image inspection before OpenCV decode (format, dimensions, pixel budget)."""
from __future__ import annotations

import io
import warnings

from PIL import Image, UnidentifiedImageError

from src.config import (
    MAX_IMAGE_HEIGHT,
    MAX_IMAGE_PIXELS,
    MAX_IMAGE_WIDTH,
    MIN_IMAGE_SIDE,
)
from src.errors import InvalidImageError

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
ALLOWED_FORMATS = {"JPEG", "PNG"}


def inspect_image(content: bytes) -> dict:
    """Returns {format, width, height, pixels} after validating a compressed upload.

    Raises InvalidImageError with an actionable message for invalid, truncated,
    oversized, or undersized images. This inspects headers without allocating the
    full pixel array.
    """
    if not content:
        raise InvalidImageError("Empty file.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                image_format = image.format
                width, height = image.size
                image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise InvalidImageError("Could not read image — unsupported, corrupted, or truncated file.") from exc
    except Image.DecompressionBombError as exc:
        raise InvalidImageError("Image dimensions are too large to process safely.") from exc
    except Image.DecompressionBombWarning as exc:
        raise InvalidImageError("Image dimensions are too large to process safely.") from exc

    if image_format not in ALLOWED_FORMATS:
        raise InvalidImageError(f"Unsupported image format: {image_format}. Use JPEG or PNG.")
    if width < MIN_IMAGE_SIDE or height < MIN_IMAGE_SIDE:
        raise InvalidImageError(
            f"Image is too small ({width}x{height}). Minimum side is {MIN_IMAGE_SIDE}px."
        )
    if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
        raise InvalidImageError(
            f"Image is too large ({width}x{height}). Maximum dimensions are "
            f"{MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}."
        )
    if width * height > MAX_IMAGE_PIXELS:
        raise InvalidImageError(
            f"Image has {width * height:,} pixels; maximum is {MAX_IMAGE_PIXELS:,}."
        )

    return {"format": image_format, "width": width, "height": height, "pixels": width * height}
