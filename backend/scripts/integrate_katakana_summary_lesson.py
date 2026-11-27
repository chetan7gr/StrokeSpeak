"""Move the existing Katakana vowel summary into the combined Japanese tutor.

This migration changes only learning_lessons.id=315. It preserves the lesson ID,
content, and all lesson_progress rows. It is safe to re-run after successful
application.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import get_db_connection


LESSON_ID = 315
KATAKANA_LANGUAGE_ID = 57
JAPANESE_LANGUAGE_ID = 5
EXPECTED_TITLE = "Katakana: first five vowels"
EXPECTED_CONTENT = "ア イ ウ エ オ"


def integrate_lesson():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT ll.id, ll.language_id, ll.level, ll.unit_number,
                      ll.lesson_order, ll.category, ll.title, ll.content_text,
                      l.script_code
               FROM learning_lessons ll
               JOIN languages l ON l.id = ll.language_id
               WHERE ll.id = %s""",
            (LESSON_ID,),
        )
        lesson = cursor.fetchone()
        if lesson is None:
            raise RuntimeError(f"Expected lesson {LESSON_ID} was not found.")
        if lesson["title"] != EXPECTED_TITLE or lesson["content_text"] != EXPECTED_CONTENT:
            raise RuntimeError("Lesson content differs from the reviewed Katakana summary; refusing to move it.")
        if lesson["category"] != "character" or lesson["level"] != "foundation":
            raise RuntimeError("Lesson category or level changed; refusing to move it.")

        if (
            lesson["language_id"] == JAPANESE_LANGUAGE_ID
            and lesson["script_code"] == "ja-hiragana"
            and lesson["unit_number"] == 3
            and lesson["lesson_order"] == 6
        ):
            print(f"Lesson {LESSON_ID} is already integrated into Japanese Foundation, Katakana unit.")
            return

        if not (
            lesson["language_id"] == KATAKANA_LANGUAGE_ID
            and lesson["script_code"] == "ja-katakana"
            and lesson["unit_number"] == 1
            and lesson["lesson_order"] == 1
        ):
            raise RuntimeError("Lesson is not in its expected original location; refusing to move it.")

        cursor.execute(
            "SELECT id FROM languages WHERE id=%s AND script_code='ja-hiragana'",
            (JAPANESE_LANGUAGE_ID,),
        )
        if cursor.fetchone() is None:
            raise RuntimeError("Combined Japanese tutor language row was not found.")

        cursor.execute(
            """SELECT COUNT(*) AS lesson_count, MAX(lesson_order) AS max_order
               FROM learning_lessons
               WHERE language_id=%s AND level='foundation' AND unit_number=3""",
            (JAPANESE_LANGUAGE_ID,),
        )
        unit = cursor.fetchone()
        if int(unit["lesson_count"] or 0) != 5 or int(unit["max_order"] or 0) != 5:
            raise RuntimeError("Japanese Katakana-vowel unit changed; expected five lessons ordered 1–5.")

        cursor.execute("SELECT COUNT(*) AS progress_count FROM lesson_progress WHERE lesson_id=%s", (LESSON_ID,))
        progress_count = int(cursor.fetchone()["progress_count"] or 0)
        cursor.execute(
            """UPDATE learning_lessons
               SET language_id=%s, unit_number=3, lesson_order=6
               WHERE id=%s AND language_id=%s AND unit_number=1 AND lesson_order=1""",
            (JAPANESE_LANGUAGE_ID, LESSON_ID, KATAKANA_LANGUAGE_ID),
        )
        if cursor.rowcount != 1:
            raise RuntimeError("Expected exactly one lesson row to move; transaction will roll back.")
        connection.commit()
        print(
            f"Integrated lesson {LESSON_ID} into Japanese Foundation Katakana unit at order 6. "
            f"Preserved {progress_count} existing lesson progress row(s)."
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    integrate_lesson()
