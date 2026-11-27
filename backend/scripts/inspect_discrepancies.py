"""
Deep inspection script for Video QA and Database Discrepancies
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

    print("=== 1. Sanskrit 'अ' Stroke Discrepancy Investigation ===")
    cursor.execute("""
        SELECT id, language_id, character_text, pronunciation_text, meaning,
               reference_strokes IS NOT NULL as has_ref,
               reference_strokes_svg IS NOT NULL as has_svg,
               reference_strokes
        FROM characters
        WHERE character_text = 'अ'
    """)
    rows = cursor.fetchall()
    for r in rows:
        strokes = json.loads(r['reference_strokes']) if r.get('reference_strokes') else []
        print(f"Char ID {r['id']}, Lang ID {r['language_id']}, Text: '{r['character_text']}', Pron: '{r['pronunciation_text']}', Stroke Count: {len(strokes)}")
        if len(strokes) > 0:
            print(f"  Stroke lengths: {[len(s) for s in strokes]}")

    print("\nCheck if any other Devanagari characters have reference strokes:")
    cursor.execute("""
        SELECT c.id, c.character_text, c.pronunciation_text, c.reference_strokes IS NOT NULL as has_ref,
               LENGTH(c.reference_strokes) as ref_len
        FROM characters c
        JOIN languages l ON l.id = c.language_id
        WHERE l.script_code = 'sa-devanagari'
        LIMIT 10
    """)
    for r in cursor.fetchall():
        print(f"  ID {r['id']}: '{r['character_text']}' ({r['pronunciation_text']}), has_ref={r['has_ref']}, len={r['ref_len']}")

    print("\n=== 2. Tamil Lessons 55 and 223 Investigation ===")
    cursor.execute("""
        SELECT id, language_id, category, level, unit_number, lesson_order,
               title, content_text, pronunciation_text, explanation,
               tutorial_video_url, tutorial_video_status
        FROM learning_lessons
        WHERE id IN (55, 223)
    """)
    for r in cursor.fetchall():
        print(f"Lesson ID {r['id']}: Level={r['level']}, Unit={r['unit_number']}, Order={r['lesson_order']}")
        print(f"  Category: {r['category']}, Title: {r['title']}")
        print(f"  Content: '{r['content_text']}', Pron: '{r['pronunciation_text']}'")
        print(f"  Video URL: {r['tutorial_video_url']}, Status: {r['tutorial_video_status']}")

    print("\n=== 3. Chinese '一' First-Tone Investigation ===")
    cursor.execute("""
        SELECT id, language_id, character_text, pronunciation_text, meaning,
               reference_strokes IS NOT NULL as has_ref,
               reference_strokes
        FROM characters
        WHERE character_text = '一'
    """)
    for r in cursor.fetchall():
        strokes = json.loads(r['reference_strokes']) if r.get('reference_strokes') else []
        print(f"Char ID {r['id']}, Text: '{r['character_text']}', Pron: '{r['pronunciation_text']}', Meaning: '{r['meaning']}', Strokes: {len(strokes)}")

    cursor.execute("""
        SELECT id, title, content_text, pronunciation_text, explanation,
               tutorial_video_url, tutorial_video_status
        FROM learning_lessons
        WHERE id = 348
    """)
    for r in cursor.fetchall():
        print(f"Lesson 348: Title: '{r['title']}', Content: '{r['content_text']}', Pron: '{r['pronunciation_text']}'")
        print(f"  Explanation: {r['explanation'][:100]}...")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
