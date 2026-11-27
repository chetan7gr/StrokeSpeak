import sys
import os
import json

sys.path.insert(0, os.path.abspath("backend"))
from app.db.database import get_db_connection

conn = get_db_connection()
c = conn.cursor(dictionary=True)
c.execute("""
    SELECT c.id, c.character_text, c.meaning, c.reference_strokes
    FROM characters c JOIN languages l ON c.language_id = l.id
    WHERE l.script_code = 'zh-hans'
    ORDER BY c.id
""")
rows = c.fetchall()
for r in rows:
    has_ref = bool(r['reference_strokes'] and r['reference_strokes'] != '[]')
    st_count = len(json.loads(r['reference_strokes'])) if has_ref else 0
    print(f"ID {r['id']:3d}: '{r['character_text']}' ({r['meaning']}) - has_ref={has_ref}, strokes={st_count}")
conn.close()
