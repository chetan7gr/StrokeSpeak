"""Place the Tamil vowel introduction before its twelve ordered vowel lessons.

Only lesson ordering changes. Existing progress rows remain attached to the same IDs.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.database import get_db_connection

SCRIPT_CODE = "ta"
INTRO_ID = 55
VOWEL_IDS = tuple(range(223, 235))
EXPECTED_OLD_ORDERS = {INTRO_ID: 13, **{lesson_id: lesson_id - 222 for lesson_id in VOWEL_IDS}}
DESIRED_ORDERS = {INTRO_ID: 1, **{lesson_id: lesson_id - 221 for lesson_id in VOWEL_IDS}}


def normalize():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        connection.start_transaction()
        ids = (INTRO_ID, *VOWEL_IDS)
        placeholders = ",".join(["%s"] * len(ids))
        cursor.execute(
            f"""SELECT ll.id,ll.level,ll.unit_number,ll.lesson_order,ll.title,l.script_code
                FROM learning_lessons ll JOIN languages l ON l.id=ll.language_id
                WHERE ll.id IN ({placeholders}) ORDER BY ll.id FOR UPDATE""",
            ids,
        )
        rows = cursor.fetchall()
        by_id = {row["id"]: row for row in rows}
        if set(by_id) != set(ids):
            raise RuntimeError("Expected Tamil intro and all 12 vowel lessons; refusing partial update.")
        for lesson_id, row in by_id.items():
            if row["script_code"] != SCRIPT_CODE or row["level"] != "foundation" or row["unit_number"] != 1:
                raise RuntimeError(f"Lesson {lesson_id} no longer belongs to Tamil Foundation unit 1.")
            current = row["lesson_order"]
            if current not in (EXPECTED_OLD_ORDERS[lesson_id], DESIRED_ORDERS[lesson_id]):
                raise RuntimeError(f"Unexpected order for lesson {lesson_id}: {current}.")
        if all(row["lesson_order"] == DESIRED_ORDERS[lesson_id] for lesson_id, row in by_id.items()):
            connection.commit()
            print("Tamil vowel introduction order is already normalized.")
            return

        cursor.execute(
            f"UPDATE learning_lessons SET lesson_order=10000+id WHERE id IN ({placeholders})",
            ids,
        )
        for lesson_id, desired in DESIRED_ORDERS.items():
            cursor.execute("UPDATE learning_lessons SET lesson_order=%s WHERE id=%s", (desired, lesson_id))
        connection.commit()
        cursor.execute("SELECT COUNT(*) AS progress_rows FROM lesson_progress WHERE lesson_id IN (" + placeholders + ")", ids)
        preserved = cursor.fetchone()["progress_rows"]
        print(f"Moved Tamil vowel introduction to lesson 1 and sequenced vowels through lesson 13. Preserved {preserved} progress row(s).")
        print("No lesson content, scores, attempts, quiz results, or learner progress rows were changed.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    normalize()
