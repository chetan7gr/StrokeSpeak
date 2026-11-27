import sys
import json
sys.path.insert(0, "backend")
from app.db.database import get_db_connection

conn = get_db_connection()
c = conn.cursor(dictionary=True)
c.execute("""
    SELECT c.id, c.character_text, c.pronunciation_text, c.meaning, l.name,
           c.reference_strokes, c.reference_strokes_svg
    FROM characters c
    JOIN languages l ON l.id = c.language_id
    WHERE l.script_code = 'ta'
    ORDER BY c.id
""")
rows = c.fetchall()
print(f"Total Tamil characters: {len(rows)}")
for r in rows:
    ref_pts = json.loads(r['reference_strokes']) if r['reference_strokes'] else None
    ref_svg = json.loads(r['reference_strokes_svg']) if r['reference_strokes_svg'] else None
    stroke_count = len(ref_pts) if ref_pts else 0
    svg_strokes = len(ref_svg['strokes']) if ref_svg and 'strokes' in ref_svg else 0
    print(f"ID: {r['id']:3d} | Char: {r['character_text']} | Pron: {str(r['pronunciation_text']):6s} | Meaning: {str(r['meaning'])[:30]} | Strokes: {stroke_count} (SVG: {svg_strokes})")
conn.close()
