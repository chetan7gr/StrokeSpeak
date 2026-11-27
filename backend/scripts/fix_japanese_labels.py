# -*- coding: utf-8 -*-
"""Correct the old Japanese Katakana labels on the Hiragana rows, if present."""
import json
from datetime import datetime
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.db.database import get_db_connection  # noqa: E402

OLD_LABEL = "Japanese Katakana character"
NEW_LABEL = "Japanese Hiragana character"


def main():
    backup_dir = BACKEND / "db_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    backup_path = None
    try:
        cursor.execute("SELECT id FROM languages WHERE script_code = %s", ("ja-hiragana",))
        language = cursor.fetchone()
        if language is None:
            raise RuntimeError("Language ja-hiragana was not found; no rows changed.")
        language_id = language["id"]
        cursor.execute(
            "SELECT id, language_id, character_text, meaning, pronunciation_text, reference_strokes "
            "FROM characters WHERE language_id = %s ORDER BY id",
            (language_id,),
        )
        all_rows = cursor.fetchall()
        cursor.execute(
            "SELECT id, language_id, character_text, meaning, pronunciation_text, reference_strokes "
            "FROM characters WHERE language_id = %s AND meaning = %s ORDER BY id",
            (language_id, OLD_LABEL),
        )
        affected = cursor.fetchall()
        before_count = len(all_rows)
        updated = 0
        if affected:
            cursor.execute("SELECT COUNT(*) AS n FROM characters")
            total_before = cursor.fetchone()["n"]
            stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
            backup_path = backup_dir / f"japanese-hiragana-labels-before-update-{stamp}.json"
            backup_payload = {
                "created_at_local": datetime.now().astimezone().isoformat(),
                "purpose": "Pre-update backup for fix_japanese_labels.py",
                "table_counts_before_update": {"characters": total_before, "ja_hiragana": before_count},
                "affected_rows": {"characters": affected},
            }
            backup_path.write_text(
                json.dumps(backup_payload, ensure_ascii=False, default=str, indent=2),
                encoding="utf-8",
            )
            cursor.execute(
                "UPDATE characters SET meaning = %s WHERE language_id = %s AND meaning = %s",
                (NEW_LABEL, language_id, OLD_LABEL),
            )
            updated = cursor.rowcount
            if updated != len(affected):
                connection.rollback()
                raise RuntimeError(
                    f"Expected to update {len(affected)} rows, matched {updated}; transaction rolled back."
                )
            connection.commit()
        cursor.execute("SELECT COUNT(*) AS n FROM characters WHERE language_id = %s", (language_id,))
        after_count = cursor.fetchone()["n"]
        cursor.execute(
            "SELECT COUNT(*) AS n FROM characters WHERE language_id = %s AND meaning = %s",
            (language_id, NEW_LABEL),
        )
        correct_count = cursor.fetchone()["n"]
        cursor.execute(
            "SELECT COUNT(*) AS n FROM characters WHERE language_id = %s AND meaning = %s",
            (language_id, OLD_LABEL),
        )
        wrong_remaining = cursor.fetchone()["n"]
        cursor.execute("SELECT COUNT(*) AS n FROM characters")
        total_after = cursor.fetchone()["n"]
        print(f"Updated: {updated}")
        print(f"Skipped (already corrected): {before_count - len(affected)}")
        print(f"Japanese character count: before={before_count}, after={after_count}")
        print(f"Correct Hiragana labels: {correct_count}; old Katakana labels remaining: {wrong_remaining}")
        print(f"Character table count: before={total_before if backup_path else total_after}, after={total_after}")
        print(f"Backup: {backup_path if backup_path else 'not needed; no rows required an update'}")
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
