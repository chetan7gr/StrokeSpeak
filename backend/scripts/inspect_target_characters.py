import sys
import os
sys.path.insert(0, os.path.abspath("backend"))
from app.db.database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

targets = {
    'sa-devanagari': ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ए', 'ऐ', 'ओ', 'औ'],
    'ta': ['அ', 'ஆ', 'இ', 'ஈ', 'உ', 'ஊ', 'எ', 'ஏ', 'ஐ', 'ஒ'],
    'zh-hans': ['一', '二', '三', '人', '口', '大', '小', '山', '日', '月']
}

print("=== TARGET CHARACTERS IN DATABASE ===")
all_found = True
for script, chars in targets.items():
    print(f"\n--- Script: {script} ({len(chars)} chars) ---")
    for ch in chars:
        cursor.execute(
            "SELECT c.id, c.character_text, c.pronunciation_text, c.meaning, l.name, l.script_code "
            "FROM characters c JOIN languages l ON l.id = c.language_id "
            "WHERE l.script_code = %s AND c.character_text = %s",
            (script, ch)
        )
        row = cursor.fetchone()
        if row:
            cid = row["id"]
            ctext = row["character_text"]
            cpron = row["pronunciation_text"] or ""
            cname = row["name"]
            print(f"  Found: id={cid:3d} | char={ctext} | pron={cpron:6s} | lang={cname}")
        else:
            print(f"  MISSING: char={ch}")
            all_found = False

print("\nAll 30 characters found in DB:", all_found)
cursor.close()
conn.close()
