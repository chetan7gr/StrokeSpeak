import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from app.ml.registry import model_registry

classes = ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ']
prefixes = ['kanaA', 'kanaI', 'kanaU', 'kanaE', 'kanaO', 'kanaKA', 'kanaKI', 'kanaKU', 'kanaKE', 'kanaKO']

print("--- Testing All 10 Classes on Held-out Samples ---")
all_passed = True
for char, prefix in zip(classes, prefixes):
    img_path = f"backend/data/hiragana_dataset/{prefix}/{prefix}19.jpg"
    res = model_registry.predict(img_path, script_code="ja-hiragana", expected_character=char)
    is_match = res["is_match"]
    if not is_match:
        all_passed = False
    pred = res["predicted_character"]
    conf = res["confidence"]
    t = res["inference_time_ms"]
    print(f"Char: {char} | Predicted: {pred} | Conf: {conf:5.1f}% | Match: {is_match} | Latency: {t:.2f} ms")

print("\nAll 10 classes correctly predicted:", all_passed)
