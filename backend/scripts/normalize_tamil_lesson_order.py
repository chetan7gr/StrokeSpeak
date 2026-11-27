"""Correct known Tamil course ordering anomalies without changing lesson content."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.database import get_db_connection

# lesson_id: (old level, old unit, old order, new level, new unit, new order)
LESSON_MOVES = {
    301: ("foundation", 2, 2, "beginner", 1, 5),  # polite request after the 4 beginner words
    300: ("foundation", 2, 300, "foundation", 2, 6),  # vowel contrast after consonant intro
     56: ("foundation", 3, 56, "foundation", 3, 5),  # greeting after 4 ka-family forms
    303: ("elementary", 6, 303, "elementary", 1, 1),
    304: ("advanced", 7, 304, "advanced", 1, 1),
}


def normalize_tamil_lesson_order():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        connection.start_transaction()
        for lesson_id, expected in LESSON_MOVES.items():
            cursor.execute(
                """SELECT l.script_code, ll.level, ll.unit_number, ll.lesson_order
                   FROM learning_lessons ll JOIN languages l ON l.id=ll.language_id
                   WHERE ll.id=%s FOR UPDATE""",
                (lesson_id,),
            )
            row = cursor.fetchone()
            if row is None or row["script_code"] != "ta":
                raise RuntimeError(f"Lesson {lesson_id} is missing or is not a Tamil lesson.")
            old = tuple(row[key] for key in ("level", "unit_number", "lesson_order"))
            desired = expected[3:]
            if old == desired:
                continue
            if old != expected[:3]:
                raise RuntimeError(f"Lesson {lesson_id} changed unexpectedly: {old!r}")
            cursor.execute("SELECT 1 FROM lesson_progress WHERE lesson_id=%s LIMIT 1", (lesson_id,))
            if cursor.fetchone():
                raise RuntimeError(f"Lesson {lesson_id} has saved progress; refusing to move it.")
            cursor.execute(
                "UPDATE learning_lessons SET level=%s, unit_number=%s, lesson_order=%s WHERE id=%s",
                (*desired, lesson_id),
            )
        connection.commit()
        print("Tamil lesson sequence normalized. No lesson text or learner attempts were changed.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    normalize_tamil_lesson_order()
