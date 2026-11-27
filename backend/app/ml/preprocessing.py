"""
OpenCV Image Preprocessing Pipeline for Multilingual Handwriting Recognition
StrokeSpeak: Intelligent Multilingual Character & Speech Tutor
"""
import cv2
import numpy as np

TARGET_SIZE = 32  # 32x32 pixels, optimal standard for small CPU CNNs

def preprocess_handwriting_image(image_input, target_size: int = TARGET_SIZE) -> np.ndarray:
    """
    Standard OpenCV preprocessing pipeline applied consistently during training and inference:
    1. Read / decode image (bytes, path, or numpy array).
    2. Convert to grayscale.
    3. Handle foreground/background polarity (standardize to white strokes on black background).
    4. Remove noise via Gaussian filtering.
    5. Find bounding box of character strokes using Otsu thresholding.
    6. Aspect-ratio preserving crop & square padding with border margin.
    7. Resize to target_size x target_size using area interpolation.
    8. Normalize pixel intensities to [0.0, 1.0] float32 (without post-resize dilation to prevent loop bridging).
    9. Reshape to (1, 1, target_size, target_size) NCHW format for ONNX/TorchScript inference.
    """
    import os
    import base64

    if isinstance(image_input, (bytes, bytearray)):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError("Could not decode image bytes.")
    elif isinstance(image_input, str):
        # 1. Check if data URI
        if image_input.startswith("data:image"):
            image_input = image_input.split(",", 1)[-1]

        # 2. Check if valid local file path
        if os.path.isfile(image_input):
            img = cv2.imread(image_input, cv2.IMREAD_UNCHANGED)
        else:
            # 3. Attempt base64 decode
            try:
                raw_bytes = base64.b64decode(image_input)
                nparr = np.frombuffer(raw_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            except Exception:
                img = None

        if img is None:
            raise ValueError(f"Could not load image from path or decode base64 string: {image_input[:40]}...")
    elif isinstance(image_input, np.ndarray):
        img = image_input.copy()
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    # Handle Alpha channel (e.g. PNG from transparent canvas)
    if len(img.shape) == 3 and img.shape[2] == 4:
        alpha = img[:, :, 3]
        rgb = img[:, :, :3]
        white_bg = np.ones_like(rgb, dtype=np.uint8) * 255
        alpha_factor = alpha[:, :, np.newaxis] / 255.0
        img = (rgb * alpha_factor + white_bg * (1.0 - alpha_factor)).astype(np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # Noise removal
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Determine polarity: check border pixels
    h, w = gray.shape
    border_pixels = np.concatenate([
        gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1]
    ])
    if np.mean(border_pixels) > 127:
        # Light background with dark ink -> invert so strokes are bright
        binary_source = 255 - blurred
    else:
        binary_source = blurred

    # Otsu thresholding to find ink pixels
    _, thresh = cv2.threshold(binary_source, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Find bounding box of foreground pixels
    coords = cv2.findNonZero(thresh)
    if coords is not None and len(coords) > 10:
        x, y, bw, bh = cv2.boundingRect(coords)
        cropped = binary_source[y:y+bh, x:x+bw]

        # Make square with aspect ratio preservation
        max_dim = max(bw, bh)
        margin = int(max_dim * 0.15)
        square_dim = max_dim + 2 * margin
        padded = np.zeros((square_dim, square_dim), dtype=np.uint8)

        offset_y = margin + (max_dim - bh) // 2
        offset_x = margin + (max_dim - bw) // 2
        padded[offset_y:offset_y+bh, offset_x:offset_x+bw] = cropped
        processed = padded
    else:
        processed = binary_source

    # Resize to target size (32x32) using area interpolation (preserves smooth anti-aliased strokes)
    resized = cv2.resize(processed, (target_size, target_size), interpolation=cv2.INTER_AREA)

    # Normalize pixel intensities directly to [0.0, 1.0] float32.
    # Note: Post-resize 2x2 dilation is intentionally avoided on 32x32 grids because a 1-pixel kernel
    # occupies >3.1% of the entire canvas, which artificially bridges internal loops (e.g. あ vs お,
    # अ vs आ, and அ vs ஆ) and distorts fine stroke spacing.
    normalized = resized.astype(np.float32) / 255.0

    # Reshape to (1, 1, target_size, target_size) NCHW
    tensor = np.expand_dims(np.expand_dims(normalized, axis=0), axis=0)
    return tensor
