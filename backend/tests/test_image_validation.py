import io

import pytest
from PIL import Image

from src import image_validation
from src.errors import InvalidImageError
from src.image_validation import inspect_image


def _png(width=512, height=512, colour=(120, 120, 120), image_format="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), colour).save(buffer, format=image_format)
    return buffer.getvalue()


def test_valid_png_passes():
    info = inspect_image(_png())
    assert info["format"] == "PNG"
    assert info["width"] == 512
    assert info["pixels"] == 512 * 512


def test_small_image_rejected():
    with pytest.raises(InvalidImageError):
        inspect_image(_png(100, 100))


def test_unsupported_format_rejected():
    with pytest.raises(InvalidImageError):
        inspect_image(_png(image_format="GIF"))


def test_corrupt_bytes_rejected():
    with pytest.raises(InvalidImageError):
        inspect_image(b"not an image")


def test_width_limit_rejected(monkeypatch):
    monkeypatch.setattr(image_validation, "MAX_IMAGE_WIDTH", 100)
    with pytest.raises(InvalidImageError):
        inspect_image(_png(200, 200))


def test_pixel_limit_rejected(monkeypatch):
    monkeypatch.setattr(image_validation, "MAX_IMAGE_PIXELS", 1000)
    with pytest.raises(InvalidImageError):
        inspect_image(_png(200, 200))
