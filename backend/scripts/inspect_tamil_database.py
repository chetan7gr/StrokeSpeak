import sys
import os
import json
sys.path.insert(0, os.path.abspath("backend"))
from app.db.database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

cursor.execute("""
    SELECT c.id, c.character_text, c.pronunciation_text, c.meaning, c.reference_strokes, c.reference_strokes_svg
    FROM characters c
    JOIN languages l ON l.id = c.language_id
    WHERE l.script_code = 'ta'
    ORDER BY c.id
""")
rows = cursor.fetchall()

print("=== TAMIL CHARACTERS IN DATABASE ===")
for r in rows:
    cid = r["id"]
    char = r["character_text"]
    pron = r["pronunciation_text"] or ""
    has_ref = r["reference_strokes"] is not None and r["reference_strokes"] != ""
    n_strokes = 0
    if has_ref:
        s_data = json.loads(r["reference_strokes"])
        n_strokes = len(s_data)
        svg_meta = json.loads(r["reference_strokes_svg"]) if r["reference_strokes_svg"] else {}
        svg_strokes = svg_meta.get("strokes", [])
        svg_d_list = [s.get("d", "") for s in svg_strokes]
    print(f"ID: {cid:3d} | Glyph: '{char}' (U+{ord(char):04X}) | Pron: '{pron:5s}' | Strokes: {n_strokes} | Ref: {has_ref}")
    if has_ref:
        for idx, (s, d) in enumerate(zip(s_data, svg_d_list)):
            print(f"    Stroke {idx+1}: {len(s)} pts, start=({s[0]['x']:.2f}, {s[0]['y']:.2f}), end=({s[-1]['x']:.2f}, {s[-1]['y']:.2f}) | d='{d[:45]}...'")

cursor.close()
conn.close()
