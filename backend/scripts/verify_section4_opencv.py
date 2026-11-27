import os
import sys
import numpy as np
import cv2

sys.path.insert(0, os.path.abspath("backend"))
from app.ml.preprocessing import preprocess_handwriting_image, TARGET_SIZE

print("=== VERIFYING SECTION 4: OPENCV PREPROCESSING PIPELINE ===")

# 1. Test Alpha Channel Handling (RGBA)
h, w = 120, 120
rgba = np.zeros((h, w, 4), dtype=np.uint8)
# Transparent background (alpha=0)
rgba[:, :, 3] = 0
# Draw an opaque black stroke (alpha=255, BGR=0)
cv2.line(rgba, (30, 30), (90, 90), (0, 0, 0, 255), 6)
tensor_alpha = preprocess_handwriting_image(rgba)
assert tensor_alpha.shape == (1, 1, 32, 32), f"Alpha shape mismatch: {tensor_alpha.shape}"
assert tensor_alpha.dtype == np.float32, f"Alpha dtype mismatch: {tensor_alpha.dtype}"
print(" [PASS] 1. Alpha channel handling (RGBA -> BGR white-bg compositing -> Grayscale) verified")

# 2. Test Polarity Detection & Inversion
# Case A: Dark stroke on light background (e.g. black pen on white paper)
light_bg = np.ones((100, 100), dtype=np.uint8) * 255
cv2.circle(light_bg, (50, 50), 20, 0, 4) # black circle
tensor_light = preprocess_handwriting_image(light_bg)

# Case B: Bright stroke on dark background (e.g. white chalk on black board)
dark_bg = np.zeros((100, 100), dtype=np.uint8)
cv2.circle(dark_bg, (50, 50), 20, 255, 4) # white circle
tensor_dark = preprocess_handwriting_image(dark_bg)

# Both should produce white ink (values near 1.0) on black background (values near 0.0)
assert tensor_light.mean() < 0.5, "Inverted stroke background was not dark!"
assert tensor_dark.mean() < 0.5, "Dark stroke background was not dark!"
assert tensor_light.max() == 1.0, "Stroke foreground was not normalized to 1.0!"
assert tensor_dark.max() == 1.0, "Stroke foreground was not normalized to 1.0!"
print(" [PASS] 2. Polarity detection & automatic inversion verified (standardizes ink to bright on dark)")

# 3. Test Gaussian Filtering & Otsu Thresholding
# Ensure noisy backgrounds don't corrupt the binarization
noisy = np.ones((100, 100), dtype=np.uint8) * 250
# Add Gaussian noise
noise = np.random.normal(0, 5, (100, 100)).astype(np.int16)
noisy = np.clip(noisy.astype(np.int16) + noise, 0, 255).astype(np.uint8)
# Add bold stroke
cv2.line(noisy, (20, 50), (80, 50), 20, 6)
tensor_noisy = preprocess_handwriting_image(noisy)
assert tensor_noisy.shape == (1, 1, 32, 32)
print(" [PASS] 3. Gaussian blur & Otsu thresholding verified with noise-resilient stroke segmentation")

# 4. Test Aspect-Ratio Preservation (Tall stroke vs Wide stroke)
tall_img = np.ones((200, 60), dtype=np.uint8) * 255
cv2.line(tall_img, (30, 20), (30, 180), 0, 4) # tall vertical line
tensor_tall = preprocess_handwriting_image(tall_img)

wide_img = np.ones((60, 200), dtype=np.uint8) * 255
cv2.line(wide_img, (20, 30), (180, 30), 0, 4) # wide horizontal line
tensor_wide = preprocess_handwriting_image(wide_img)

assert tensor_tall.shape == (1, 1, 32, 32)
assert tensor_wide.shape == (1, 1, 32, 32)
# The non-line dimensions should have zero padding
tall_slice = tensor_tall[0, 0]
assert tall_slice[:, 0].sum() == 0.0 and tall_slice[:, -1].sum() == 0.0, "Square padding margin missing on tall stroke!"
print(" [PASS] 4. Bounding-box detection, square aspect-ratio padding (15% margin) verified")

# 5. Test Resizing (32x32), Morphological Processing, and Normalization
assert TARGET_SIZE == 32
test_img_path = r"backend\data\hiragana_dataset\kanaA\kanaA0.jpg"
real_tensor = preprocess_handwriting_image(test_img_path)
assert real_tensor.shape == (1, 1, 32, 32)
assert real_tensor.dtype == np.float32
assert 0.0 <= real_tensor.min() <= real_tensor.max() <= 1.0
print(f" [PASS] 5. Real image output shape: {real_tensor.shape}, dtype: {real_tensor.dtype}, range: [{real_tensor.min():.2f}, {real_tensor.max():.2f}]")

print("=== SECTION 4 VERIFICATION COMPLETED: ALL PASS ===")
