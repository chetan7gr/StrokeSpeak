"""
Inspect validation targets for Japanese 'い', Sanskrit 'अ', Tamil 'அ', Chinese '一'
"""
import sys
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.db.database import get_db_connection

def main():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    targets = [
        ("ja-hiragana", "い"),
        ("sa-devanagari", "अ"),
        ("ta", "அ"),
        ("zh-hans", "一"),
    ]

    print("=== TARGET CHARACTERS & LESSONS ===")
    for script, char in targets:
        cursor.execute("""
            SELECT c.id as char_id, c.character_text, c.pronunciation_text, c.meaning,
                   c.reference_strokes IS NOT NULL as has_ref,
                   c.reference_strokes
            FROM characters c
            JOIN languages l ON l.id = c.language_id
            WHERE l.script_code = %s AND c.character_text = %s
        """, (script, char))
        crow = cursor.fetchone()
        
        cursor.execute("""
            SELECT ll.id as lesson_id, ll.level, ll.unit_number, ll.lesson_order, ll.title
            FROM learning_lessons ll
            JOIN languages l ON l.id = ll.language_id
            WHERE l.script_code = %s AND ll.content_text = %s
        """, (script, char))
        lrows = cursor.fetchall()

        strokes = json.loads(crow['reference_strokes']) if crow and crow.get('reference_strokes') else []
        print(f"\nScript: {script} -> Character '{char}'")
        print(f"  Character ID: {crow['char_id'] if crow else 'None'}")
        print(f"  Pronunciation: {crow['pronunciation_text'] if crow else 'None'}, Meaning: {crow['meaning'] if crow else 'None'}")
        print(f"  Ref Stroke Count: {len(strokes)}")
        print(f"  Associated Lessons:")
        for l in lrows:
            print(f"    - Lesson ID {l['lesson_id']}: [{l['level']} u{l['unit_number']} o{l['lesson_order']}] '{l['title']}'")

    print("\n=== RECENT PRACTICE ATTEMPTS (Last 5) ===")
    cursor.execute("DESCRIBE practice_attempts")
    cols = [r['Field'] for r in cursor.fetchall()]
    print(f"Columns: {cols}")

    cursor.execute("""
        SELECT pa.*
        FROM practice_attempts pa
        ORDER BY pa.id DESC
        LIMIT 5
    """)
    for r in cursor.fetchall():
        print(f"Attempt #{r['id']} (User {r.get('user_id')}): Char {r.get('character_id')}")
        print(f"  Geom: {r.get('geometry_score')}%, Order: {r.get('stroke_order_score')}%, CNN: '{r.get('cnn_prediction')}' ({r.get('confidence')}%)")
        print(f"  Created: {r.get('created_at')}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
