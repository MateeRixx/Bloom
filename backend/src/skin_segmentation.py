"""Skin colour mask + MediaPipe face ROI + eye/lip/brow/nose exclusion. Sab RGB in/out."""
from __future__ import annotations

import cv2
import numpy as np

from src.config import (
    SKIN_CR_MIN, SKIN_CR_MAX,
    SKIN_CB_MIN, SKIN_CB_MAX,
    SKIN_H_MIN, SKIN_H_MAX,
    SKIN_S_MIN, SKIN_S_MAX,
    SKIN_V_MIN, SKIN_V_MAX,
    SKIN_MORPH_KERNEL,
    ROI_EROSION_PX,
    EXCLUSION_DILATE_PX,
    FALLBACK_MARGIN,
    FACE_MESH_MAX_FACES,
    FACE_MESH_MIN_DETECTION_CONFIDENCE,
)

# FaceMesh bhaari hai, lazy-load karenge.
_face_mesh = None


def _get_face_mesh():
    """Returns lazily-built MediaPipe FaceMesh instance."""
    global _face_mesh
    if _face_mesh is None:
        import mediapipe as mp
        _face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=FACE_MESH_MAX_FACES,
            refine_landmarks=False,
            min_detection_confidence=FACE_MESH_MIN_DETECTION_CONFIDENCE,
        )
    return _face_mesh


def _run_face_mesh(image: np.ndarray):
    """Returns normalized landmarks [(x, y), ...] for first face, or None."""
    result = _get_face_mesh().process(image)
    if not result.multi_face_landmarks:
        return None
    return [(lm.x, lm.y) for lm in result.multi_face_landmarks[0].landmark]


def _group_indices(connections) -> np.ndarray:
    """Returns unique landmark indices referenced by a MediaPipe connection set."""
    return np.unique(np.asarray(list(connections), dtype=np.int32).reshape(-1))


def _points_px(landmarks, shape, indices) -> np.ndarray:
    """Converts normalized landmark indices to integer pixel points."""
    h, w = shape[:2]
    return np.array([[int(landmarks[i][0] * w), int(landmarks[i][1] * h)] for i in indices], np.int32)


def _fallback_face_mask(shape) -> np.ndarray:
    """Returns centre-region rectangle mask when no face is detected."""
    h, w = shape[:2]
    mask = np.zeros((h, w), np.uint8)
    m = FALLBACK_MARGIN
    mask[int(h * m):int(h * (1 - m)), int(w * m):int(w * (1 - m))] = 255
    return mask


def _face_oval_mask(landmarks, shape) -> np.ndarray:
    """Returns filled face-oval polygon mask from landmarks."""
    import mediapipe as mp
    idx = _group_indices(mp.solutions.face_mesh.FACEMESH_FACE_OVAL)
    mask = np.zeros(shape[:2], np.uint8)
    cv2.fillConvexPoly(mask, cv2.convexHull(_points_px(landmarks, shape, idx)), 255)
    return mask


def _exclusion_mask(landmarks, shape) -> np.ndarray:
    """Returns combined eyes + brows + lips + nose mask (with slight dilation)."""
    import mediapipe as mp
    fm = mp.solutions.face_mesh
    mask = np.zeros(shape[:2], np.uint8)
    for conn in (fm.FACEMESH_LEFT_EYE, fm.FACEMESH_RIGHT_EYE,
                 fm.FACEMESH_LEFT_EYEBROW, fm.FACEMESH_RIGHT_EYEBROW,
                 fm.FACEMESH_LIPS, fm.FACEMESH_NOSE):
        pts = _points_px(landmarks, shape, _group_indices(conn))
        cv2.fillConvexPoly(mask, cv2.convexHull(pts), 255)
    return cv2.dilate(mask, None, iterations=EXCLUSION_DILATE_PX)


def _skin_colour_mask(image: np.ndarray) -> np.ndarray:
    """Returns binary skin-colour mask using YCrCb AND HSV in-range detection."""
    ycrcb = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    in_ycrcb = cv2.inRange(ycrcb, (0, SKIN_CR_MIN, SKIN_CB_MIN), (255, SKIN_CR_MAX, SKIN_CB_MAX))
    in_hsv = cv2.inRange(hsv, (SKIN_H_MIN, SKIN_S_MIN, SKIN_V_MIN), (SKIN_H_MAX, SKIN_S_MAX, SKIN_V_MAX))
    mask = cv2.bitwise_and(in_ycrcb, in_hsv)
    # speckle hatao, holes bharo
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, SKIN_MORPH_KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


def _build_face_and_exclusion(image: np.ndarray):
    """Returns (face_mask, exclusion_mask, mode). Single FaceMesh inference."""
    landmarks = _run_face_mesh(image)
    if landmarks is None:
        # No face => centre fallback, koi exclusion nahi
        return _fallback_face_mask(image.shape), np.zeros(image.shape[:2], np.uint8), "fallback"
    return _face_oval_mask(landmarks, image.shape), _exclusion_mask(landmarks, image.shape), "mediapipe"


def get_face_mask(image: np.ndarray) -> tuple[np.ndarray, str]:
    """Returns (binary face mask, mode) where mode is 'mediapipe' or 'fallback'."""
    mask, _, mode = _build_face_and_exclusion(image)
    return mask, mode


def run(image: np.ndarray) -> dict:
    """Returns SegmentationMasks dict: skin_mask, analysis_zone, face_mask, exclusion_mask, mediapipe_mode."""
    if image is None or image.size == 0:
        raise ValueError("skin_segmentation.run received empty image array")

    face_mask, exclusion_mask, mode = _build_face_and_exclusion(image)
    # face boundary se ROI_EROSION_PX andar tak hi analyse karenge
    roi = cv2.erode(face_mask, None, iterations=ROI_EROSION_PX)
    skin_mask = cv2.bitwise_and(_skin_colour_mask(image), roi)
    analysis_zone = cv2.bitwise_and(skin_mask, cv2.bitwise_not(exclusion_mask))

    return {
        "skin_mask": skin_mask,
        "analysis_zone": analysis_zone,
        "face_mask": face_mask,
        "exclusion_mask": exclusion_mask,
        "mediapipe_mode": mode,
    }


if __name__ == "__main__":
    import sys

    from src.preprocessing import run as preprocess

    path = sys.argv[1] if len(sys.argv) > 1 else "test_image.jpg"
    with open(path, "rb") as f:
        image, _ = preprocess(f.read())

    masks = run(image)
    print(f"mediapipe_mode: {masks['mediapipe_mode']}")
    for key in ("skin_mask", "analysis_zone", "face_mask", "exclusion_mask"):
        m = masks[key]
        print(f"{key:15s} shape={m.shape} dtype={m.dtype} nonzero={int((m > 0).sum())}")
    print("skin_segmentation.py: OK")
