import os
import json

backend_dir = os.path.abspath("backend")
model_extensions = (".pt", ".pth", ".torchscript", ".onnx", ".npz")
found = []

for root, dirs, files in os.walk(backend_dir):
    if ".venv" in root or "__pycache__" in root:
        continue
    for f in files:
        f_lower = f.lower()
        if f_lower.endswith(model_extensions) or ("metadata" in f_lower and f_lower.endswith(".json")):
            full_path = os.path.join(root, f)
            size = os.path.getsize(full_path)
            
            # Identify script / language association
            assoc = "Unknown"
            if "japanese" in f_lower or "hiragana" in f_lower or "kana" in f_lower:
                assoc = "Japanese (Hiragana) [ja-hiragana]"
            elif "sanskrit" in f_lower or "devanagari" in f_lower:
                assoc = "Sanskrit (Devanagari) [sa-devanagari]"
            elif "tamil" in f_lower:
                assoc = "Tamil [ta]"
            elif "chinese" in f_lower or "hanzi" in f_lower:
                assoc = "Simplified Chinese [zh-hans]"

            found.append({
                "filename": f,
                "path": full_path,
                "size_bytes": size,
                "size_kb": round(size / 1024, 2),
                "script_language": assoc
            })

found.sort(key=lambda x: x["path"])
for item in found:
    print(f"{item['filename']} --- {item['size_kb']} KB ({item['size_bytes']} bytes) --- {item['script_language']}")
    print(f"  Path: {item['path']}")

# Save as json
with open("backend/scripts/found_ml_models.json", "w", encoding="utf-8") as out:
    json.dump(found, out, indent=2, ensure_ascii=False)
