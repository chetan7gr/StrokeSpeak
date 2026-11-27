import sys
import json
sys.path.insert(0, "backend")
from app.db.database import get_db_connection

conn = get_db_connection()
c = conn.cursor(dictionary=True)

c.execute("""
    SELECT c.id, c.character_text, c.pronunciation_text, c.reference_strokes, c.reference_strokes_svg
    FROM characters c JOIN languages l ON l.id = c.language_id
    WHERE l.script_code = 'sa-devanagari' AND c.reference_strokes IS NOT NULL
    ORDER BY c.id
""")
rows = c.fetchall()
print(f"Total Sanskrit characters with reference: {len(rows)}")
for r in rows:
    strokes = json.loads(r['reference_strokes'])
    svg = json.loads(r['reference_strokes_svg'])
    print(f"\nID {r['id']:3d}: '{r['character_text']}' ({r['pronunciation_text']}) | Strokes: {len(strokes)} | SVG strokes: {len(svg.get('strokes', []))}")
    print(f"  viewBox: {svg.get('viewBox')} | Source: {svg.get('source')}")
    for s_idx, s in enumerate(svg.get('strokes', [])):
        print(f"    Stroke {s['order']}: {s['d'][:70]}...")

conn.close()
