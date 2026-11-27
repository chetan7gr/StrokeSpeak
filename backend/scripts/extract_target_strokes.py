import json
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.db.database import get_db_connection

def extract_strokes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    targets = [
        (216, "char216_strokes.json", "sa-devanagari", "अ"),
        (25, "char25_strokes.json", "ta", "அ"),
        (241, "char241_strokes.json", "zh-hans", "一")
    ]

    data_dir = backend_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    for char_id, filename, script_code, char_text in targets:
        cursor.execute("SELECT id, character_text, reference_strokes FROM characters WHERE id = %s", (char_id,))
        row = cursor.fetchone()
        if not row or not row["reference_strokes"]:
            print(f"Error: no reference strokes for {char_id} ({char_text})")
            continue

        raw = row["reference_strokes"]
        parsed = json.loads(raw) if isinstance(raw, str) else raw

        out_file = data_dir / filename
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({
                "character_id": char_id,
                "character_text": char_text,
                "script_code": script_code,
                "stroke_data": parsed
            }, f, ensure_ascii=False, indent=2)

        print(f"Saved {char_text} (ID {char_id}) to {out_file} with {len(parsed)} strokes.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    extract_strokes()
