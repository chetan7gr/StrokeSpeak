import sys
import os
import json
import urllib.request

sys.path.insert(0, os.path.abspath("backend"))
from app.db.database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

print("=== VERIFYING STAGE 5A DATABASE STATE ===")

# 1. Total characters count
cursor.execute("SELECT COUNT(*) as c FROM characters")
total_chars = cursor.fetchone()["c"]
assert total_chars == 250, f"Expected 250 characters, found {total_chars}"
print(f" [PASS] Total characters count: {total_chars} (100% intact)")

# 2. Count characters with reference strokes per script
cursor.execute("""
    SELECT l.script_code, l.name, COUNT(c.id) as ref_count
    FROM characters c
    JOIN languages l ON l.id = c.language_id
    WHERE c.reference_strokes IS NOT NULL AND c.reference_strokes != '' AND c.reference_strokes != '[]'
    GROUP BY l.script_code, l.name
""")
rows = cursor.fetchall()
ref_counts = {r["script_code"]: r["ref_count"] for r in rows}
print("Characters with reference strokes by script:")
for r in rows:
    print(f"  {r['script_code']} ({r['name']}): {r['ref_count']}")

assert ref_counts.get("ja-hiragana") == 46, f"Japanese Hiragana reference strokes altered! {ref_counts.get('ja-hiragana')}"
assert ref_counts.get("sa-devanagari") == 10, f"Sanskrit Devanagari reference strokes mismatch! {ref_counts.get('sa-devanagari')}"
assert ref_counts.get("ta") == 10, f"Tamil reference strokes mismatch! {ref_counts.get('ta')}"
assert ref_counts.get("zh-hans") == 10, f"Simplified Chinese reference strokes mismatch! {ref_counts.get('zh-hans')}"
print(" [PASS] Exact reference counts verified across all 4 scripts!")

# 3. Verify no-reference characters still return honest pending status
# Sanskrit marker 'ं' (ID 235) has no reference strokes
cursor.execute("SELECT id, character_text, reference_strokes FROM characters WHERE id = 235")
no_ref = cursor.fetchone()
assert no_ref["reference_strokes"] is None
print(f" [PASS] No-reference character '{no_ref['character_text']}' (id={no_ref['id']}) correctly remains NULL")

cursor.close()
conn.close()

# 4. Verify HTTP API GET /api/v1/characters/{id}/reference-strokes
test_ids = [
    (2, "Japanese あ", True),
    (216, "Sanskrit अ", True),
    (25, "Tamil அ", True),
    (241, "Chinese 一", True),
    (235, "Sanskrit ं (no reference)", False),
]

print("\n--- Verifying GET /api/v1/characters/{id}/reference-strokes API ---")
for cid, label, expected_available in test_ids:
    url = f"http://127.0.0.1:8000/api/v1/characters/{cid}/reference-strokes"
    with urllib.request.urlopen(url) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        avail = data.get("reference_available")
        assert avail == expected_available, f"{label} expected available={expected_available}, got {avail}"
        if expected_available:
            strokes = data.get("stroke_data")
            source = data.get("reference_source")
            guidance = data.get("stroke_guidance")
            print(f"  [PASS] {label}: available={avail}, strokes={len(strokes)}, guidance_steps={len(guidance)}")
        else:
            print(f"  [PASS] {label}: available={avail}, message='{data.get('message')}' (honest pending)")

print("\n=== STAGE 5A DATABASE VERIFICATION COMPLETE: ALL PASS ===")
