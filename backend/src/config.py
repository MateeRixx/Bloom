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

# --- Lesion detection (contrast-adaptive: offset = max(floor, mult * skin std)) ---
REDNESS_A_MIN_DELTA = 10           # Min A offset above skin mean (guards low-contrast/uniform skin)
REDNESS_A_STD_MULT = 1.4           # A offset scales with skin redness spread
BLEMISH_L_MIN_DELTA = 25           # Min L offset below skin mean (guards dark spots vs shadow)
BLEMISH_L_STD_MULT = 1.5           # L offset scales with skin luminance spread
ACNE_DOG_THRESHOLD_RATIO = 0.30    # Fraction of DoG max used as threshold
LESION_MORPH_KERNEL = (3, 3)       # Small close kernel to join speckled lesion px
MIN_LESION_AREA_PX = 50            # Contours smaller than this = noise, ignored

# --- Watershed ---
WATERSHED_DIST_THRESHOLD = 0.4    # Fraction of dist max used as sure-fg seed
WATERSHED_MIN_DISTANCE = 10        # Min px between local maxima (spot separation)

# --- Severity thresholds (area as % of skin region) ---
SEVERITY = {
    "acne":    {"Mild": 1.0, "Moderate": 3.0},   # >3 = Severe
    "redness": {"Mild": 4.0, "Moderate": 12.0},
    "blemish": {"Mild": 2.0, "Moderate": 6.0},
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

# --- Overlay colours (RGB, per schema) ---
ACNE_COLOUR = (59, 130, 246)       # blue contours
REDNESS_COLOUR = (239, 68, 68)     # red fill
BLEMISH_COLOUR = (234, 179, 8)     # yellow contours
BASELINE_COLOUR = (148, 163, 184)  # slate contours for baseline
SKIN_MASK_COLOUR = (16, 185, 129)  # green skin-mask overlay
FILL_OPACITY = 0.4                 # redness fill alpha
SKIN_OVERLAY_OPACITY = 0.4         # skin-mask overlay alpha
CONTOUR_THICKNESS = 2              # contour line width (px)

# --- API ---
RATE_LIMIT = "10/minute"           # per-IP rate limit on /api/analyse

# --- Output ---
JPEG_QUALITY = 85                  # Base64 output image compression quality
