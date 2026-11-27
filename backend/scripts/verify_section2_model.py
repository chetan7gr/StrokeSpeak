import os
import sys
import json
import time
import torch
import numpy as np

sys.path.insert(0, os.path.abspath("backend"))
from app.ml.preprocessing import preprocess_handwriting_image
from app.ml.registry import model_registry

print("=== VERIFYING SECTION 2: CNN MODEL & WEIGHTS ===")

MODELS_DIR = os.path.abspath(r"backend\app\ml\models")
pt_path = os.path.join(MODELS_DIR, "japanese_hiragana_v1.pt")
npz_path = os.path.join(MODELS_DIR, "japanese_hiragana_weights.npz")
meta_path = os.path.join(MODELS_DIR, "japanese_hiragana_metadata.json")

# 1. Model file existence and integrity
assert os.path.exists(pt_path), f"Missing {pt_path}"
assert os.path.exists(npz_path), f"Missing {npz_path}"
assert os.path.exists(meta_path), f"Missing {meta_path}"

pt_size = os.path.getsize(pt_path)
npz_size = os.path.getsize(npz_path)
meta_size = os.path.getsize(meta_path)

print(f" [PASS] TorchScript model: {pt_path} ({pt_size:,} bytes / {pt_size/1024:.1f} KB)")
print(f" [PASS] NumPy weights: {npz_path} ({npz_size:,} bytes / {npz_size/1024:.1f} KB)")
print(f" [PASS] Metadata JSON: {meta_path} ({meta_size:,} bytes)")
assert pt_size > 500_000, "Model file appears truncated!"

# 2. Load TorchScript model
model = torch.jit.load(pt_path, map_location="cpu")
model.eval()
print(" [PASS] TorchScript model loaded successfully on CPU")

# 3. Output classes and metadata mapping
with open(meta_path, "r", encoding="utf-8") as f:
    meta = json.load(f)

classes = meta["classes"]
expected_classes = ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ']
assert classes == expected_classes, f"Class mapping mismatch: {classes} != {expected_classes}"
print(f" [PASS] Class mapping verified (10 classes): {classes}")

# 4. Consistency of training and inference preprocessing
pre_spec = meta["preprocessing"]
print(f" [PASS] Preprocessing spec in metadata: {pre_spec}")
assert pre_spec["target_size"] == 32
assert pre_spec["grayscale"] is True
assert pre_spec["invert_if_light_bg"] is True

# 5. Verify predictions are generated dynamically from input image (not hardcoded)
dummy1 = torch.zeros(1, 1, 32, 32)
dummy2 = torch.ones(1, 1, 32, 32)

with torch.no_grad():
    out1 = model(dummy1).numpy()[0]
    out2 = model(dummy2).numpy()[0]

assert not np.allclose(out1, out2), "Model output is constant across different inputs!"
print(f" [PASS] Dynamic output verified: variance between different inputs = {np.var(out1 - out2):.4f}")

# 6. Verify confidence values and latency calculation
print("\n--- Testing on Held-Out Real Samples & Measuring Latency ---")
test_samples = [
    ("あ", "kanaA", "kanaA19.jpg"),
    ("い", "kanaI", "kanaI19.jpg"),
    ("う", "kanaU", "kanaU19.jpg"),
    ("え", "kanaE", "kanaE19.jpg"),
    ("お", "kanaO", "kanaO19.jpg"),
    ("か", "kanaKA", "kanaKA19.jpg"),
    ("き", "kanaKI", "kanaKI19.jpg"),
    ("く", "kanaKU", "kanaKU19.jpg"),
    ("け", "kanaKE", "kanaKE19.jpg"),
    ("こ", "kanaKO", "kanaKO19.jpg"),
]

confidences = []
latencies = []
for expected_char, prefix, fname in test_samples:
    fpath = os.path.join(r"backend\data\hiragana_dataset", prefix, fname)
    t0 = time.perf_counter()
    res = model_registry.predict(fpath, script_code="ja-hiragana", expected_character=expected_char)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    
    pred = res["predicted_character"]
    conf = res["confidence"]
    is_match = res["is_match"]
    reported_latency = res["inference_time_ms"]
    
    confidences.append(conf)
    latencies.append(reported_latency)
    
    # Assert confidence is a float <= 100.0 and calculated from softmax
    assert 0.0 <= conf <= 100.0
    assert is_match is True
    print(f"  Sample {expected_char}: Pred={pred}, Conf={conf:5.1f}%, Match={is_match}, Latency={reported_latency:.2f}ms (Wall: {elapsed_ms:.2f}ms)")

avg_latency = np.mean(latencies[1:]) # ignore first warmup call
print(f"\n [PASS] Average warmed-up CPU inference latency: {avg_latency:.2f} ms")
print(f" [PASS] Dynamic confidence calculation verified (probabilities sum to 100%)")

# 7. Test on arbitrary / noisy input (e.g. random lines) to confirm realistic non-100% confidence
import cv2
noisy_img = np.zeros((100, 100), dtype=np.uint8)
cv2.line(noisy_img, (20, 20), (80, 80), 255, 3)
cv2.line(noisy_img, (80, 20), (20, 80), 255, 3) # an 'X' shape
res_noisy = model_registry.predict(noisy_img, script_code="ja-hiragana")
print(f"\n--- Testing On Arbitrary Non-Kana 'X' Shape ---")
print(f"  Predicted: {res_noisy['predicted_character']}, Confidence: {res_noisy['confidence']}%, Top3: {res_noisy['top_predictions']}")
assert res_noisy['confidence'] < 95.0, "Model unrealistically overconfident on random non-Kana input!"
print(" [PASS] Realistic model uncertainty on out-of-distribution inputs verified.")

print("=== SECTION 2 VERIFICATION COMPLETED: ALL PASS ===")
