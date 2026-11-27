import os
import sys
import json
import base64
import urllib.request

API_BASE = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 80)
    print("STAGE 5B-B2 API INTEGRATION TESTS ACROSS ALL 4 SCRIPTS")
    print("=" * 80)

    # 1. Test GET /api/v1/ml/models
    print("\n--- 1. Testing GET /api/v1/ml/models ---")
    req = urllib.request.Request(f"{API_BASE}/api/v1/ml/models")
    with urllib.request.urlopen(req) as resp:
        models_data = json.loads(resp.read().decode())
    scripts = models_data["scripts"]
    for sc in ["ja-hiragana", "sa-devanagari", "ta", "zh-hans"]:
        assert sc in scripts, f"Missing script {sc}"
        assert scripts[sc]["status"] == "TRAINED", f"Script {sc} not TRAINED"
        assert scripts[sc]["has_trained_model"] is True, f"Script {sc} has_trained_model is False"
        print(f"  [OK] {sc}: status={scripts[sc]['status']}, classes={len(scripts[sc]['trained_classes'])}")

    # 2. Test POST /api/v1/ml/recognize for each script
    print("\n--- 2. Testing POST /api/v1/ml/recognize ---")
    test_cases = [
        {
            "script_code": "ja-hiragana",
            "img_path": "backend/data/hiragana_dataset/kanaA/kanaA19.jpg",
            "expected": "あ",
        },
        {
            "script_code": "sa-devanagari",
            "img_path": "backend/data/sanskrit_dataset/vowel_A/vowel_A_19.jpg",
            "expected": "अ",
        },
        {
            "script_code": "ta",
            "img_path": "backend/data/tamil_dataset/vowel_A/vowel_A_19.jpg",
            "expected": "அ",
        },
        {
            "script_code": "zh-hans",
            "img_path": "backend/data/chinese_dataset/char_YI/char_YI_19.jpg",
            "expected": "一",
        },
    ]

    for tc in test_cases:
        with open(tc["img_path"], "rb") as f:
            b64_img = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "image_base64": b64_img,
            "script_code": tc["script_code"],
            "expected_character": tc["expected"],
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{API_BASE}/api/v1/ml/recognize",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode())

        print(f"\n  Script: {tc['script_code']} ({res['language']})")
        print(f"    Expected: '{tc['expected']}', Predicted: '{res['predicted_character']}'")
        print(f"    Confidence: {res['confidence']}%, Match: {res['is_match']}")
        print(f"    Top predictions: {res['top_predictions']}")
        print(f"    Inference latency: {res['inference_time_ms']} ms")
        assert res["status"] == "success"
        assert res["is_match"] is True
        assert res["predicted_character"] == tc["expected"]
        print(f"    [PASS] POST /api/v1/ml/recognize successful for {tc['script_code']}")

    # 3. Test POST /api/v1/characters/{character_id}/recognize
    print("\n--- 3. Testing POST /api/v1/characters/{id}/recognize ---")
    char_test_cases = [
        {
            "char_id": 216,  # Sanskrit 'अ'
            "expected": "अ",
            "script_code": "sa-devanagari",
            "img_path": "backend/data/sanskrit_dataset/vowel_A/vowel_A_19.jpg",
        },
        {
            "char_id": 25,   # Tamil 'அ'
            "expected": "அ",
            "script_code": "ta",
            "img_path": "backend/data/tamil_dataset/vowel_A/vowel_A_19.jpg",
        },
        {
            "char_id": 241,  # Chinese '一'
            "expected": "一",
            "script_code": "zh-hans",
            "img_path": "backend/data/chinese_dataset/char_YI/char_YI_19.jpg",
        },
    ]

    for tc in char_test_cases:
        with open(tc["img_path"], "rb") as f:
            b64_img = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "image_base64": b64_img,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{API_BASE}/api/v1/characters/{tc['char_id']}/recognize",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode())

        print(f"\n  Character ID {tc['char_id']}: Expected '{tc['expected']}', Got '{res['predicted_character']}'")
        print(f"    Confidence: {res['confidence']}%, Match: {res['is_match']}, Latency: {res['inference_time_ms']} ms")
        assert res["status"] == "success"
        assert res["is_match"] is True
        assert res["predicted_character"] == tc["expected"]
        print(f"    [PASS] Character recognize endpoint passed for ID {tc['char_id']}")

    print("\n" + "=" * 80)
    print("ALL API INTEGRATION TESTS PASSED 100% ACROSS ALL 4 SCRIPTS!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
