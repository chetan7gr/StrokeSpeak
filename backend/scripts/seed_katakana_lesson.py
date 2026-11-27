# -*- coding: utf-8 -*-
"""Create the first beginner Katakana vowel lesson used by the progress flow."""
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.db.database import get_db_connection  # noqa: E402

LANGUAGE_CODE = "ja-katakana"
TITLE = "Katakana: first five vowels"


def main():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id FROM languages WHERE script_code = %s", (LANGUAGE_CODE,))
        language = cursor.fetchone()
        if language is None:
            raise RuntimeError("Japanese Katakana language is missing; no lesson inserted.")
        language_id = language[0]
        cursor.execute(
            "SELECT id FROM learning_lessons WHERE language_id = %s AND title = %s",
            (language_id, TITLE),
        )
        existing = cursor.fetchone()
        if existing:
            connection.commit()
            print(f"Lesson ID: {existing[0]}; inserted: False; skipped existing: 1; updated: 0")
            return
        cursor.execute(
            "INSERT INTO learning_lessons "
            "(language_id, category, title, content_text, translation_text, pronunciation_text, "
            "explanation, level, unit_number, lesson_order) "
            "VALUES (%s, 'character', %s, %s, %s, %s, %s, 'foundation', 1, 1)",
            (
                language_id,
                TITLE,
                "ア イ ウ エ オ",
                "a, i, u, e, o",
                "a, i, u, e, o",
                "Practise the first five Katakana vowel characters in gojūon order.",
            ),
        )
        lesson_id = cursor.lastrowid
        connection.commit()
        print(f"Lesson ID: {lesson_id}; inserted: True; skipped existing: 0; updated: 0")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
