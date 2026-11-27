import sys
import json
sys.path.insert(0, "backend")
from app.db.database import get_db_connection

conn = get_db_connection()
c = conn.cursor(dictionary=True)

# 1. Languages
c.execute("SELECT id, name, script_code FROM languages ORDER BY id")
langs = c.fetchall()
print("=== LANGUAGES ===")
for l in langs:
    print(f"ID {l['id']:2d}: {l['name']} ({l['script_code']})")

# 2. Sanskrit Characters
print("\n=== SANSKRIT CHARACTERS ===")
c.execute("""
    SELECT c.id, c.character_text, c.pronunciation_text, c.meaning,
           c.reference_strokes IS NOT NULL as has_ref
    FROM characters c JOIN languages l ON l.id = c.language_id
    WHERE l.script_code = 'sa-devanagari'
    ORDER BY c.id
""")
for r in c.fetchall():
    print(f"ID {r['id']:3d}: '{r['character_text']}' ({r['pronunciation_text']}) - {r['meaning']} | has_ref: {r['has_ref']}")

# 3. Sanskrit Lessons
print("\n=== SANSKRIT LESSONS ===")
c.execute("""
    SELECT ll.id, ll.category, ll.level, ll.unit_number, ll.lesson_order, ll.title, ll.content_text, ll.translation_text
    FROM learning_lessons ll JOIN languages l ON l.id = ll.language_id
    WHERE l.script_code = 'sa-devanagari'
    ORDER BY ll.unit_number, ll.lesson_order, ll.id
""")
for r in c.fetchall():
    print(f"ID {r['id']:3d} | Unit {r['unit_number']} Order {r['lesson_order']:2d} | Cat: {r['category']:10s} | Level: {r['level']:10s} | Title: {r['title']} | Content: {r['content_text']}")

# 4. Tamil Characters
print("\n=== TAMIL CHARACTERS ===")
c.execute("""
    SELECT c.id, c.character_text, c.pronunciation_text, c.meaning,
           c.reference_strokes IS NOT NULL as has_ref
    FROM characters c JOIN languages l ON l.id = c.language_id
    WHERE l.script_code = 'ta'
    ORDER BY c.id
""")
for r in c.fetchall():
    print(f"ID {r['id']:3d}: '{r['character_text']}' ({r['pronunciation_text']}) - {r['meaning']} | has_ref: {r['has_ref']}")

# 5. Tamil Lessons
print("\n=== TAMIL LESSONS ===")
c.execute("""
    SELECT ll.id, ll.category, ll.level, ll.unit_number, ll.lesson_order, ll.title, ll.content_text, ll.translation_text
    FROM learning_lessons ll JOIN languages l ON l.id = ll.language_id
    WHERE l.script_code = 'ta'
    ORDER BY ll.unit_number, ll.lesson_order, ll.id
""")
for r in c.fetchall():
    print(f"ID {r['id']:3d} | Unit {r['unit_number']} Order {r['lesson_order']:2d} | Cat: {r['category']:10s} | Level: {r['level']:10s} | Title: {r['title']} | Content: {r['content_text']}")

# 6. Chinese Lessons
print("\n=== CHINESE LESSONS ===")
c.execute("""
    SELECT ll.id, ll.category, ll.level, ll.unit_number, ll.lesson_order, ll.title, ll.content_text, ll.translation_text
    FROM learning_lessons ll JOIN languages l ON l.id = ll.language_id
    WHERE l.script_code = 'zh-hans'
    ORDER BY ll.unit_number, ll.lesson_order, ll.id
""")
for r in c.fetchall():
    print(f"ID {r['id']:3d} | Unit {r['unit_number']} Order {r['lesson_order']:2d} | Cat: {r['category']:10s} | Level: {r['level']:10s} | Title: {r['title']} | Content: {r['content_text']}")

# 7. Japanese Lessons structure summary
print("\n=== JAPANESE LESSONS SUMMARY ===")
c.execute("""
    SELECT ll.level, ll.unit_number, ll.category, COUNT(*) as count
    FROM learning_lessons ll JOIN languages l ON l.id = ll.language_id
    WHERE l.script_code = 'ja-hiragana'
    GROUP BY ll.level, ll.unit_number, ll.category
    ORDER BY ll.level, ll.unit_number
""")
for r in c.fetchall():
    print(f"Level: {r['level']:12s} | Unit {r['unit_number']} | Cat: {r['category']:10s} | Count: {r['count']}")

conn.close()
