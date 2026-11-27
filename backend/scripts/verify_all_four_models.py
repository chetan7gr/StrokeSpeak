import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath("backend"))
from app.ml.registry import model_registry

def test_models():
    print("=" * 75)
    print("VERIFYING MODEL REGISTRY AND CPU INFERENCE ACROSS ALL 4 SCRIPTS")
    print("=" * 75)

    scripts = model_registry.get_registered_scripts()
    for sc, info in scripts.items():
        print(f"  [{sc}] {info['language_name']}: status={info['status']}, has_model={info['has_trained_model']}, num_classes={len(info['trained_classes'])}")
        print(f"    Classes: {info['trained_classes']}")

    print("\nTesting inference on representative real test samples for each script:")

    sample_tests = [
        ("ja-hiragana", "backend/data/hiragana_dataset/kanaA/kanaA19.jpg", "あ"),
        ("sa-devanagari", "backend/data/sanskrit_dataset/vowel_A/vowel_A_19.jpg", "अ"),
        ("ta", "backend/data/tamil_dataset/vowel_A/vowel_A_19.jpg", "அ"),
        ("zh-hans", "backend/data/chinese_dataset/char_YI/char_YI_19.jpg", "一"),
    ]

    for script_code, img_path, expected_char in sample_tests:
        assert os.path.exists(img_path), f"Sample image {img_path} not found"
        res = model_registry.predict(img_path, script_code=script_code, expected_character=expected_char)
        print(f"\n  Script: {script_code} ({res['language']})")
        print(f"    Image: {img_path}")
        print(f"    Expected: '{expected_char}', Predicted: '{res['predicted_character']}'")
        print(f"    Confidence: {res['confidence']}%, Match: {res['is_match']}")
        print(f"    Top 3: {res['top_predictions']}")
        print(f"    Inference time: {res['inference_time_ms']} ms")
        assert res["status"] == "success"
        assert res["is_match"] is True

    print("\n" + "=" * 75)
    print("FOUR TRAINED MODELS MATCHED ONE SMOKE SAMPLE EACH; THIS IS NOT AN ACCURACY ESTIMATE.")
    print("=" * 75)

if __name__ == "__main__":
    test_models()
