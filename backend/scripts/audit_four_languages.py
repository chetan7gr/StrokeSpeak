import sys
import os
sys.path.insert(0, os.path.abspath("backend"))
from app.db.database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

scripts = [
    ('Japanese Hiragana', 'ja-hiragana'),
    ('Sanskrit Devanagari', 'sa-devanagari'),
    ('Tamil', 'ta'),
    ('Simplified Chinese', 'zh-hans')
]

print("=== FOUR-LANGUAGE DATABASE AUDIT ===")
for name, code in scripts:
    cursor.execute("SELECT id, name, script_code FROM languages WHERE script_code = %s", (code,))
    lang = cursor.fetchone()
    if not lang:
        print(f"{name} ({code}): NOT FOUND IN DB!")
        continue
    lang_id = lang["id"]
    
    cursor.execute("SELECT COUNT(*) as c FROM characters WHERE language_id = %s", (lang_id,))
    char_count = cursor.fetchone()["c"]
    
    cursor.execute("SELECT COUNT(*) as c FROM characters WHERE language_id = %s AND reference_strokes IS NOT NULL AND reference_strokes != '' AND reference_strokes != '[]'", (lang_id,))
    ref_count = cursor.fetchone()["c"]
    
    cursor.execute("SELECT COUNT(*) as c FROM learning_lessons WHERE language_id = %s", (lang_id,))
    lesson_count = cursor.fetchone()["c"]
    
    cursor.execute("SELECT COUNT(*) as c FROM lesson_progress lp JOIN learning_lessons ll ON ll.id = lp.lesson_id WHERE ll.language_id = %s", (lang_id,))
    progress_count = cursor.fetchone()["c"]
    
    cursor.execute("SELECT COUNT(*) as c FROM practice_attempts pa JOIN characters c ON c.id = pa.character_id WHERE c.language_id = %s", (lang_id,))
    attempt_count = cursor.fetchone()["c"]
    
    cursor.execute("SELECT id, character_text, meaning, pronunciation_text FROM characters WHERE language_id = %s LIMIT 10", (lang_id,))
    sample_chars = cursor.fetchall()
    
    print(f"\n--- {name} (Language ID: {lang_id}, Script: {code}) ---")
    print(f"  Total Characters: {char_count}")
    print(f"  Characters with Reference Strokes: {ref_count}")
    print(f"  Total Lessons: {lesson_count}")
    print(f"  Lesson Progress Records: {progress_count}")
    print(f"  Practice Attempts in DB: {attempt_count}")
    print(f"  Sample Characters ({min(len(sample_chars), 10)}): {[c['character_text'] for c in sample_chars]}")
    for c in sample_chars[:5]:
        print(f"    id={c['id']}: char='{c['character_text']}', pronunciation='{c['pronunciation_text']}', meaning='{c['meaning']}'")

cursor.close()
conn.close()
