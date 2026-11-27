import sys
import os
import urllib.request
import json
import base64

sys.path.insert(0, os.path.abspath("backend"))

print("=== VERIFYING SECTION 1: LANGUAGE/SCRIPT CNN STATUS ===")

# 1. Check GET /api/v1/ml/models
with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/ml/models") as response:
    assert response.status == 200, f"Expected 200, got {response.status}"
    data = json.loads(response.read().decode())

scripts = data.get("scripts", {})
expected_statuses = {
    "ja-hiragana": {"status": "TRAINED", "has_trained_model": True, "classes_count": 10},
    "sa-devanagari": {"status": "ARCHITECTURE_READY", "has_trained_model": False, "classes_count": 0},
    "ta": {"status": "ARCHITECTURE_READY", "has_trained_model": False, "classes_count": 0},
    "zh-hans": {"status": "ARCHITECTURE_READY", "has_trained_model": False, "classes_count": 0},
}

for code, expected in expected_statuses.items():
    actual = scripts.get(code)
    assert actual is not None, f"Script {code} missing from registry"
    assert actual["status"] == expected["status"], f"{code} status mismatch: {actual['status']} != {expected['status']}"
    assert actual["has_trained_model"] == expected["has_trained_model"], f"{code} has_trained_model mismatch"
    assert len(actual["trained_classes"]) == expected["classes_count"], f"{code} classes count mismatch"
    print(f" [PASS] Script {code:14s}: Status={actual['status']}, HasModel={actual['has_trained_model']}, Classes={len(actual['trained_classes'])}")

# Check the 10 Japanese Hiragana characters
expected_kana = ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ']
actual_kana = scripts["ja-hiragana"]["trained_classes"]
assert actual_kana == expected_kana, f"Kana mismatch: {actual_kana} != {expected_kana}"
print(f" [PASS] Japanese Hiragana 10 classes verified: {', '.join(actual_kana)}")

# 2. Check strict boundary isolation via POST /api/v1/ml/recognize
# Generate dummy base64 32x32 image
import numpy as np
import cv2
dummy_img = np.zeros((32, 32), dtype=np.uint8)
cv2.line(dummy_img, (10, 10), (20, 20), 255, 2)
_, buf = cv2.imencode(".png", dummy_img)
b64_dummy = base64.b64encode(buf).decode("utf-8")

for untrained_script in ["sa-devanagari", "ta", "zh-hans"]:
    req_body = json.dumps({
        "image_base64": b64_dummy,
        "script_code": untrained_script,
        "expected_character": "X"
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/ml/recognize",
        data=req_body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        res_data = json.loads(resp.read().decode())
        assert res_data.get("status") == "script_not_trained", f"Did not return script_not_trained for {untrained_script}"
        assert "not yet trained" in res_data.get("detail", ""), f"Detail message not clear for {untrained_script}"
        assert res_data.get("predicted_character") is None, f"Silent fallback detected for {untrained_script}!"
        print(f" [PASS] Boundary Check {untrained_script:14s}: Returned status='script_not_trained', no silent fallback")

print("=== SECTION 1 VERIFICATION COMPLETED: ALL PASS ===")
