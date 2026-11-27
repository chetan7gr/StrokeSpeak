import sys
import os
import base64
sys.path.insert(0, os.path.abspath("backend"))

from starlette.testclient import TestClient
import main

client = TestClient(main.app)

print("--- 1. Testing GET /api/v1/ml/models ---")
r1 = client.get("/api/v1/ml/models")
print("Status code:", r1.status_code)
scripts = r1.json().get("scripts", {})
for sc, info in scripts.items():
    print(f"  {sc}: status={info['status']}, has_model={info['has_trained_model']}")
assert scripts["ja-hiragana"]["has_trained_model"] is True
assert scripts["sa-devanagari"]["has_trained_model"] is False

print("\n--- 2. Testing POST /api/v1/ml/recognize (ja-hiragana) ---")
test_img_path = r"backend\data\hiragana_dataset\kanaA\kanaA19.jpg"
with open(test_img_path, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("utf-8")

r2 = client.post("/api/v1/ml/recognize", json={
    "image_base64": img_b64,
    "script_code": "ja-hiragana",
    "expected_character": "あ"
})
print("Status code:", r2.status_code)
res2 = r2.json()
print("Predicted:", res2.get("predicted_character"), "Confidence:", res2.get("confidence"), "% Match:", res2.get("is_match"))
assert res2.get("predicted_character") == "あ"
assert res2.get("is_match") is True

print("\n--- 3. Testing POST /api/v1/ml/recognize Boundary Isolation (sa-devanagari) ---")
r3 = client.post("/api/v1/ml/recognize", json={
    "image_base64": img_b64,
    "script_code": "sa-devanagari",
    "expected_character": "अ"
})
print("Status code:", r3.status_code)
res3 = r3.json()
print("Result status:", res3.get("status"))
print("Detail message:", res3.get("detail"))
assert res3.get("status") == "script_not_trained"
assert "not yet trained" in res3.get("detail", "")

print("\n--- 4. Testing POST /api/v1/characters/2/recognize (Character 2 is 'あ') ---")
r4 = client.post("/api/v1/characters/2/recognize", json={
    "image_base64": img_b64
})
print("Status code:", r4.status_code)
res4 = r4.json()
print("Predicted:", res4.get("predicted_character"), "Confidence:", res4.get("confidence"), "% Match:", res4.get("is_match"))
assert res4.get("predicted_character") == "あ"
assert res4.get("is_match") is True

print("\n--- ALL ENDPOINT TESTS PASSED SUCCESSFULLY! ---")
