"""Normalize Japanese lesson numbering within each learning level."""
import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.db.database import get_db_connection  # noqa: E402
LEVELS = {"beginner": 2, "elementary": 2, "advanced": 1}


def get_counts(cursor):
    output = {}
    for table in ("learning_lessons", "lesson_progress", "practice_attempts"):
        cursor.execute(f"SELECT COUNT(*) AS n FROM {table}")
        output[table] = cursor.fetchone()["n"]
    return output


def main():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, language_id, level, unit_number, lesson_order, category, title, content_text "
            "FROM learning_lessons WHERE language_id=%s AND level IN (%s,%s,%s) ORDER BY level, lesson_order, id",
            (5, "beginner", "elementary", "advanced"),
        )
        rows = cursor.fetchall()
        actual = {level: sum(row["level"] == level for row in rows) for level in LEVELS}
        if actual != LEVELS:
            raise RuntimeError(f"Expected levels {LEVELS}, found {actual}; no changes made.")
        planned = {}
        for level in LEVELS:
            group = sorted((row for row in rows if row["level"] == level), key=lambda row: (row["lesson_order"], row["id"]))
            for order, row in enumerate(group, start=1):
                planned[row["id"]] = (1, order)
        changed = [row for row in rows if (row["unit_number"], row["lesson_order"]) != planned[row["id"]]]
        before = get_counts(cursor)
        if not changed:
            print("Japanese non-foundation lessons already start at Unit 1; no updates needed.")
            print("Counts:", json.dumps(before, sort_keys=True))
            return
        backup_dir = BACKEND / "db_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")
        backup = backup_dir / f"japanese-levels-before-unit-normalization-{stamp}.json"
        backup.write_text(json.dumps({
            "created_at_local": datetime.now().astimezone().isoformat(),
            "purpose": "Pre-update backup before normalizing Japanese units per course level.",
            "table_counts_before_change": before,
            "affected_rows": rows,
            "planned_unit_and_order_by_lesson_id": {str(key): {"unit_number": value[0], "lesson_order": value[1]} for key, value in planned.items()},
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Pre-UPDATE JSON backup: {backup}")
        print(f"Before UPDATE counts: {json.dumps(before, sort_keys=True)}; affected rows={len(changed)}")
        try:
            for row in changed:
                unit, order = planned[row["id"]]
                cursor.execute(
                    "UPDATE learning_lessons SET unit_number=%s, lesson_order=%s WHERE id=%s AND language_id=%s AND level=%s",
                    (unit, order, row["id"], 5, row["level"]),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError(f"Lesson {row['id']} was not updated exactly once; rolling back.")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        after = get_counts(cursor)
        if after != before:
            raise RuntimeError(f"Table counts changed unexpectedly: before={before}, after={after}.")
        cursor.execute(
            "SELECT level, unit_number, COUNT(*) AS n, MIN(lesson_order) AS first_order, MAX(lesson_order) AS last_order "
            "FROM learning_lessons WHERE language_id=%s AND level IN (%s,%s,%s) GROUP BY level,unit_number ORDER BY level",
            (5, "beginner", "elementary", "advanced"),
        )
        print("After UPDATE counts:", json.dumps(after, sort_keys=True))
        print("Verified course levels:", json.dumps(cursor.fetchall(), ensure_ascii=False))
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
