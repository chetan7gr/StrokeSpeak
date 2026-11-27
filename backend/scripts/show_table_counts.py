"""
StrokeSpeak Read-Only Table Counts Inspector
Queries MySQL database using project connection code and reports row counts.
Does not print credentials or modify any rows.
"""

import os
import sys

# Ensure backend directory is in python module search path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.db.database import get_db_connection

def main():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    print("==================================================")
    print("STROKESPEAK DATABASE TABLE ROW COUNTS")
    print("==================================================")

    tables = [
        'users',
        'languages',
        'characters',
        'learning_lessons',
        'lesson_progress',
        'practice_attempts'
    ]

    total_rows = 0
    table_counts = {}

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        count = cursor.fetchone()['cnt']
        table_counts[table] = count
        total_rows += count
        print(f"Table '{table}': {count} rows")

    print(f"--------------------------------------------------")
    print(f"Total Rows across all 6 tables: {total_rows}")
    print("==================================================")

    print("\nLEARNING LESSONS PER PUBLIC LANGUAGE:")
    print("--------------------------------------------------")
    public_scripts = ['ja-hiragana', 'sa-devanagari', 'ta', 'zh-hans']
    
    cursor.execute("""
        SELECT l.id, l.name, l.script_code, COUNT(ll.id) as lesson_count
        FROM languages l
        LEFT JOIN learning_lessons ll ON ll.language_id = l.id
        WHERE l.script_code IN ('ja-hiragana', 'sa-devanagari', 'ta', 'zh-hans', 'ja-katakana')
        GROUP BY l.id, l.name, l.script_code
        ORDER BY l.id
    """)
    public_rows = cursor.fetchall()
    public_total = 0
    for r in public_rows:
        public_total += r['lesson_count']
        print(f"  - {r['name']} ({r['script_code']}): {r['lesson_count']} lessons (Language ID: {r['id']})")

    print(f"Total public language lessons: {public_total}")

    # Legacy languages count
    cursor.execute("""
        SELECT COUNT(ll.id) as legacy_count
        FROM learning_lessons ll
        JOIN languages l ON ll.language_id = l.id
        WHERE l.script_code NOT IN ('ja-hiragana', 'sa-devanagari', 'ta', 'zh-hans', 'ja-katakana')
    """)
    legacy_count = cursor.fetchone()['legacy_count']
    print(f"Legacy script lessons (internal/unlisted): {legacy_count}")
    print(f"Overall learning_lessons total in DB: {public_total + legacy_count}")
    print("==================================================")

    cursor.close()
    connection.close()

if __name__ == '__main__':
    main()
