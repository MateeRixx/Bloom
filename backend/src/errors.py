"""Typed pipeline errors mapped to structured API responses."""
from __future__ import annotations


class InvalidImageError(ValueError):
    """Raised when an upload cannot be safely decoded as a supported image."""


class FaceLandmarkError(ValueError):
    """Raised when FaceMesh cannot detect a usable face/landmark set."""

    def __init__(self, message: str, reason_code: str = "no_face_landmarks") -> None:
        super().__init__(message)
        self.reason_code = reason_code
