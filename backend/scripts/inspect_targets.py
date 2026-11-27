import json
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.db.database import get_db_connection

def inspect_targets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    targets = [
        ("sa-devanagari", "अ"),
        ("ta", "அ"),
        ("zh-hans", "一")
    ]

    results = {}

    for script_code, char_text in targets:
        # Find character
        cursor.execute("""
            SELECT c.id, c.character_text, c.pronunciation_text, c.meaning,
                   c.reference_strokes IS NOT NULL AS has_ref,
                   c.reference_strokes_svg IS NOT NULL AS has_svg,
                   c.reference_strokes
            FROM characters c
            JOIN languages l ON l.id = c.language_id
            WHERE l.script_code = %s AND c.character_text = %s
        """, (script_code, char_text))
        char_row = cursor.fetchone()

        # Find lesson
        cursor.execute("""
            SELECT ll.id, ll.language_id, ll.category, ll.level, ll.unit_number,
                   ll.lesson_order, ll.title, ll.content_text, ll.translation_text,
                   ll.pronunciation_text, ll.explanation, ll.tutorial_video_url,
                   ll.tutorial_video_status
            FROM learning_lessons ll
            JOIN languages l ON l.id = ll.language_id
            WHERE l.script_code = %s AND ll.content_text = %s
            ORDER BY ll.level, ll.unit_number, ll.lesson_order, ll.id
        """, (script_code, char_text))
        lesson_rows = cursor.fetchall()

        strokes = None
        if char_row and char_row.get("reference_strokes"):
            ref = char_row["reference_strokes"]
            if isinstance(ref, str):
                try:
                    strokes = json.loads(ref)
                except Exception as e:
                    strokes = f"JSON parse error: {e}"
            else:
                strokes = ref

        results[char_text] = {
            "script_code": script_code,
            "character_id": char_row["id"] if char_row else None,
            "pronunciation": char_row["pronunciation_text"] if char_row else None,
            "meaning": char_row["meaning"] if char_row else None,
            "has_ref": char_row["has_ref"] if char_row else False,
            "stroke_count": len(strokes) if isinstance(strokes, list) else None,
            "sample_stroke_points": len(strokes[0]) if isinstance(strokes, list) and len(strokes) > 0 and isinstance(strokes[0], list) else None,
            "lessons": [
                {
                    "id": l["id"],
                    "level": l["level"],
                    "unit": l["unit_number"],
                    "order": l["lesson_order"],
                    "title": l["title"],
                    "video_url": l["tutorial_video_url"],
                    "video_status": l["tutorial_video_status"]
                }
                for l in lesson_rows
            ]
        }

    cursor.close()
    conn.close()

    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    inspect_targets()
