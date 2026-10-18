"""Central config. Yahi ek jagah hai jahan numeric constants rehte hain — kisi aur module me literal number nahi."""

# --- Image preprocessing ---
RESIZE_TARGET = (512, 512)         # All images normalised to this before processing
TARGET_L_MEAN = 130                # LAB L-channel normalisation target

# --- Quality gate ---
MIN_BRIGHTNESS = 60                # Below this: image too dark
MAX_BRIGHTNESS = 210               # Above this: image overexposed
MIN_BLUR_SCORE = 80                # Laplacian variance below this: too blurry
MAX_IMAGE_SIZE_MB = 10

# --- Enhancement ---
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID = (8, 8)
BILATERAL_D = 9
BILATERAL_SIGMA_COLOR = 75
BILATERAL_SIGMA_SPACE = 75

# --- Skin segmentation ---
SKIN_CR_MIN, SKIN_CR_MAX = 133, 180    # YCrCb Cr channel range (widened for coverage)
SKIN_CB_MIN, SKIN_CB_MAX = 77, 135     # YCrCb Cb channel range (widened for coverage)
SKIN_H_MIN, SKIN_H_MAX = 0, 30         # HSV Hue range (widened)
SKIN_S_MIN, SKIN_S_MAX = 15, 210       # HSV Saturation range (widened)
SKIN_V_MIN, SKIN_V_MAX = 40, 255       # HSV Value range (widened)
SKIN_MORPH_KERNEL = (5, 5)             # Open/close kernel for skin mask cleanup
ROI_EROSION_PX = 15                    # Pixels to erode from face boundary
EXCLUSION_DILATE_PX = 5                # Extra margin around eyes/lips/brows/nose

# --- MediaPipe face ---
MEDIAPIPE_MODEL_SELECTION = 1          # FaceDetection: 1 = full-range (works near + far)
FACE_MIN_DETECTION_CONFIDENCE = 0.5
FACE_MESH_MAX_FACES = 1
FACE_MESH_MIN_DETECTION_CONFIDENCE = 0.5
FALLBACK_MARGIN = 0.2                  # Fallback ROI = centre (1 - 2*margin) of image

# --- Frequency decomposition ---
DOG_SIGMA_1 = 1.0                  # Fine-detail Gaussian
DOG_SIGMA_2 = 3.0                  # Coarse Gaussian; DoG = sigma1 - sigma2
LP_KERNEL_SIZE = (21, 21)          # Low-pass Gaussian kernel
HP_KERNEL_SIZE = (21, 21)          # High-pass = original - LP

# --- Lesion detection ---
REDNESS_A_DELTA = 12               # LAB A above (mean_skin_A + delta) = redness (adaptive)
BLEMISH_L_DELTA = 30               # L below (mean_skin_L - delta) = dark spot
ACNE_DOG_THRESHOLD_RATIO = 0.15    # Fraction of DoG max used as threshold
LESION_MORPH_KERNEL = (3, 3)       # Small close kernel to join speckled lesion px
MIN_LESION_AREA_PX = 50            # Contours smaller than this = noise, ignored

# --- Watershed ---
WATERSHED_DIST_THRESHOLD = 0.4    # Fraction of dist max used as sure-fg seed
WATERSHED_MIN_DISTANCE = 10        # Min px between local maxima (spot separation)

# --- Severity thresholds (area as % of skin region) ---
SEVERITY = {
    "acne":    {"Mild": 1.0, "Moderate": 3.0},   # >3 = Severe
    "redness": {"Mild": 5.0, "Moderate": 15.0},
    "blemish": {"Mild": 1.0, "Moderate": 3.0},
}

# --- Naive baseline (comparison only) ---
NAIVE_REDNESS_A_THRESHOLD = 135    # fixed absolute A threshold (doc default, over-detects)
NAIVE_BLEMISH_L_THRESHOLD = 100    # fixed absolute dark threshold

# --- Evaluation ---
CONSENSUS_CORE_ERODE_PX = 2        # Erode each mask to its "high-confidence core" for pseudo-GT

# --- Confidence scoring ---
CONF_HIGH_AREA_MULT = 3.0          # region area >= 3x min area => High
CONF_MED_AREA_MULT = 1.5           # >= 1.5x min area => Medium, else Low
CONF_HIGH_REGION_COUNT = 5         # >= this many regions => High confidence
CONF_MED_REGION_COUNT = 2          # >= this many regions => Medium confidence

# --- Output ---
JPEG_QUALITY = 85                  # Base64 output image compression quality
