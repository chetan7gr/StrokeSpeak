"""Resequence the Japanese foundation Kana course without changing lesson identities."""
import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.db.database import get_db_connection  # noqa: E402

HIRAGANA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
KATAKANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
VOWELS_HIRA = set("あいうえお")
VOWELS_KATA = set("アイウエオ")
EXPECTED = {1: 5, 2: 41, 3: 5, 4: 41, 5: 1, 6: 6}


def counts(cursor):
    result = {}
    for table in ("learning_lessons", "lesson_progress", "practice_attempts"):
        cursor.execute(f"SELECT COUNT(*) AS n FROM {table}")
        result[table] = cursor.fetchone()["n"]
    return result


def main():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, language_id, level, unit_number, lesson_order, category, title, content_text "
            "FROM learning_lessons WHERE language_id=%s AND level=%s ORDER BY unit_number, lesson_order, id",
            (5, "foundation"),
        )
        rows = cursor.fetchall()
        if len(rows) != 99:
            raise RuntimeError(f"Expected 99 Japanese foundation lessons, found {len(rows)}; no changes made.")

        hira_order = {character: index for index, character in enumerate(HIRAGANA, start=1)}
        kata_order = {character: index for index, character in enumerate(KATAKANA, start=1)}
        groups = {unit: [] for unit in EXPECTED}
        assigned = []
        for row in rows:
            character = row["content_text"]
            title = row["title"] or ""
            if title.startswith("Hiragana ") and character in hira_order:
                unit = 1 if character in VOWELS_HIRA else 2
                order = hira_order[character] if unit == 1 else [c for c in HIRAGANA if c not in VOWELS_HIRA].index(character) + 1
            elif title.startswith("Katakana ") and character in kata_order:
                unit = 3 if character in VOWELS_KATA else 4
                order = kata_order[character] if unit == 3 else [c for c in KATAKANA if c not in VOWELS_KATA].index(character) + 1
            elif title.startswith("Sound contrast:"):
                unit, order = 5, 1
            else:
                unit = 6
                groups[unit].append(row)
                continue
            assigned.append((row, unit, order))
            groups[unit].append(row)

        actual = {unit: len(group) for unit, group in groups.items()}
        if actual != EXPECTED:
            raise RuntimeError(f"Expected unit counts {EXPECTED}, classified {actual}; no changes made.")

        # Keep the existing relative sequence for words and phrases.
        for order, row in enumerate(sorted(groups[6], key=lambda item: (item["unit_number"], item["lesson_order"], item["id"])), start=1):
            assigned.append((row, 6, order))
        planned = {row["id"]: (unit, order) for row, unit, order in assigned}
        if len(planned) != len(rows):
            raise RuntimeError("Some lessons were not assigned exactly once; no changes made.")

        before_counts = counts(cursor)
        changed = [row for row in rows if (row["unit_number"], row["lesson_order"]) != planned[row["id"]]]
        if not changed:
            print("Japanese foundation lessons already have the requested unit order; no database updates needed.")
            print("Counts:", json.dumps(before_counts, sort_keys=True))
            return

        backup_dir = BACKEND / "db_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")
        backup_path = backup_dir / f"japanese-foundation-lessons-before-resequence-{timestamp}.json"
        backup_payload = {
            "created_at_local": datetime.now().astimezone().isoformat(),
            "purpose": "Pre-update snapshot before reorganizing Japanese foundation lesson units and order.",
            "table_counts_before_change": before_counts,
            "affected_rows": rows,
            "planned_unit_and_order_by_lesson_id": {str(key): {"unit_number": value[0], "lesson_order": value[1]} for key, value in planned.items()},
        }
        backup_path.write_text(json.dumps(backup_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Pre-UPDATE JSON backup: {backup_path}")
        print(f"Before UPDATE counts: {json.dumps(before_counts, sort_keys=True)}; affected rows={len(changed)}")

        try:
            for row in changed:
                unit, order = planned[row["id"]]
                cursor.execute(
                    "UPDATE learning_lessons SET unit_number=%s, lesson_order=%s WHERE id=%s AND language_id=%s AND level=%s",
                    (unit, order, row["id"], 5, "foundation"),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError(f"Lesson {row['id']} was not updated exactly once; rolling back.")
            connection.commit()
        except Exception:
            connection.rollback()
            raise

        after_counts = counts(cursor)
        cursor.execute(
            "SELECT unit_number, COUNT(*) AS n, MIN(lesson_order) AS first_order, MAX(lesson_order) AS last_order "
            "FROM learning_lessons WHERE language_id=%s AND level=%s GROUP BY unit_number ORDER BY unit_number",
            (5, "foundation"),
        )
        summary = cursor.fetchall()
        if after_counts != before_counts:
            raise RuntimeError(f"Table counts changed unexpectedly: before={before_counts}, after={after_counts}.")
        verified = {row["unit_number"]: row["n"] for row in summary}
        if verified != EXPECTED:
            raise RuntimeError(f"Post-update unit counts mismatch: expected {EXPECTED}, got {verified}.")
        print("After UPDATE counts:", json.dumps(after_counts, sort_keys=True))
        print("Verified Japanese foundation units:", json.dumps(summary, ensure_ascii=False))
        print("Lesson IDs, lesson text, progress rows, and practice attempts were preserved.")
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
