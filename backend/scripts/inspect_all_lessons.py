import sys
sys.path.insert(0, "backend")
from app.db.database import get_db_connection

conn = get_db_connection()
c = conn.cursor(dictionary=True)

# Check lessons for Sanskrit
print("=== SANSKRIT LESSONS ===")
c.execute("""
    SELECT ll.id, ll.category, ll.level, ll.unit_number, ll.lesson_order, ll.title, ll.content_text, ll.translation_text, ll.pronunciation_text
    FROM learning_lessons ll JOIN languages l ON l.id = ll.language_id
    WHERE l.script_code = 'sa-devanagari'
    ORDER BY ll.level, ll.unit_number, ll.lesson_order, ll.id
""")
for r in c.fetchall():
    print(f"ID {r['id']:3d} | Level: {r['level']:11s} | Unit {r['unit_number']} Order {r['lesson_order']:2d} | Cat: {r['category']:10s} | Title: {r['title']} | Content: {r['content_text']}")

# Check lessons for Tamil
print("\n=== TAMIL LESSONS ===")
c.execute("""
    SELECT ll.id, ll.category, ll.level, ll.unit_number, ll.lesson_order, ll.title, ll.content_text, ll.translation_text, ll.pronunciation_text
    FROM learning_lessons ll JOIN languages l ON l.id = ll.language_id
    WHERE l.script_code = 'ta'
    ORDER BY ll.level, ll.unit_number, ll.lesson_order, ll.id
""")
for r in c.fetchall():
    print(f"ID {r['id']:3d} | Level: {r['level']:11s} | Unit {r['unit_number']} Order {r['lesson_order']:2d} | Cat: {r['category']:10s} | Title: {r['title']} | Content: {r['content_text']}")

# Check lessons for Chinese
print("\n=== CHINESE LESSONS ===")
c.execute("""
    SELECT ll.id, ll.category, ll.level, ll.unit_number, ll.lesson_order, ll.title, ll.content_text, ll.translation_text, ll.pronunciation_text
    FROM learning_lessons ll JOIN languages l ON l.id = ll.language_id
    WHERE l.script_code = 'zh-hans'
    ORDER BY ll.level, ll.unit_number, ll.lesson_order, ll.id
""")
for r in c.fetchall():
    print(f"ID {r['id']:3d} | Level: {r['level']:11s} | Unit {r['unit_number']} Order {r['lesson_order']:2d} | Cat: {r['category']:10s} | Title: {r['title']} | Content: {r['content_text']}")

conn.close()
