"""Add the three omitted traditional Sanskrit vowel lessons in alphabet order.

Preserves all existing lesson/progress IDs. Refuses to move an affected lesson if it
has progress and validates exact source/target state before committing.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.database import get_db_connection

BACKEND_DIR = Path(__file__).resolve().parents[1]
BACKUP_PATH = BACKEND_DIR / "data" / "backups" / "before_sanskrit_complete_vowel_set.json"
EXPECTED_EXISTING = {359: 8, 360: 9, 361: 10, 362: 11}
FINAL_EXISTING = {359: 11, 360: 12, 361: 13, 362: 14}
NEW_GLYPHS = {
    "ॠ": {
        "meaning": "Long vocalic r (IAST ṝ); rare classical Sanskrit vowel",
        "pronunciation": "ṝ",
        "explanation": "Long vocalic r, the long counterpart of ऋ. It is retained in the Sanskrit vowel inventory but occurs rarely. Compare it with ऋ. Transliteration follows the Library of Congress Sanskrit and Prakrit Romanization Table (2012). Sanskrit reference audio is an approximation and should be checked with a Sanskrit teacher.",
    },
    "ऌ": {
        "meaning": "Vocalic l (IAST ḷ); rare classical Sanskrit vowel",
        "pronunciation": "ḷ",
        "explanation": "Vocalic l, written l̥ in the Library of Congress Sanskrit and Prakrit Romanization Table (2012), and commonly transliterated ḷ. It is a rare vowel, distinct from the consonant ल. Sanskrit reference audio is an approximation and should be checked with a Sanskrit teacher.",
    },
    "ॡ": {
        "meaning": "Long vocalic l (IAST ḹ); rare classical Sanskrit vowel",
        "pronunciation": "ḹ",
        "explanation": "Long vocalic l, the long counterpart of ऌ. The Library of Congress Sanskrit and Prakrit Romanization Table (2012) transliterates it l̥̄; IAST commonly uses ḹ. It is very rare. Sanskrit reference audio is an approximation and should be checked with a Sanskrit teacher.",
    },
}


def migrate():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        connection.start_transaction()
        cursor.execute("SELECT id FROM languages WHERE script_code='sa-devanagari' FOR UPDATE")
        language = cursor.fetchone()
        if not language:
            raise RuntimeError("Sanskrit language row not found.")
        language_id = language["id"]
        cursor.execute(
            "SELECT id,character_text,meaning,pronunciation_text FROM characters WHERE language_id=%s AND character_text IN (%s,%s,%s) ORDER BY character_text FOR UPDATE",
            (language_id, *NEW_GLYPHS.keys()),
        )
        chars = {row["character_text"]: row for row in cursor.fetchall()}
        if set(chars) != set(NEW_GLYPHS):
            raise RuntimeError("Expected character-table rows for ॠ, ऌ, and ॡ; refusing partial migration.")

        cursor.execute(
            "SELECT id,title,content_text,level,unit_number,lesson_order FROM learning_lessons WHERE language_id=%s AND content_text IN (%s,%s,%s) FOR UPDATE",
            (language_id, *NEW_GLYPHS.keys()),
        )
        existing_new = cursor.fetchall()
        if existing_new:
            if len(existing_new) != len(NEW_GLYPHS) or any(
                row["level"] != "foundation" or row["unit_number"] != 1 or
                row["lesson_order"] != {"ॠ": 8, "ऌ": 9, "ॡ": 10}.get(row["content_text"])
                for row in existing_new
            ):
                raise RuntimeError("Some rare-vowel lessons exist in an unexpected state; refusing to alter them.")
            cursor.execute(
                "SELECT id,lesson_order FROM learning_lessons WHERE id IN (%s,%s,%s,%s) FOR UPDATE",
                tuple(EXPECTED_EXISTING),
            )
            current = {r["id"]: r["lesson_order"] for r in cursor.fetchall()}
            if current != FINAL_EXISTING:
                raise RuntimeError(f"Existing Sanskrit vowel lesson orders are unexpected: {current}")
            connection.commit()
            print("Sanskrit Foundation already contains the complete ordered vowel set.")
            return

        cursor.execute(
            "SELECT id,level,unit_number,lesson_order,title,content_text FROM learning_lessons WHERE id IN (%s,%s,%s,%s) ORDER BY id FOR UPDATE",
            tuple(EXPECTED_EXISTING),
        )
        rows = cursor.fetchall()
        current = {row["id"]: row["lesson_order"] for row in rows}
        if len(rows) != 4 or current != EXPECTED_EXISTING or any(
            row["level"] != "foundation" or row["unit_number"] != 1 for row in rows
        ):
            raise RuntimeError(f"Sanskrit vowel lessons changed unexpectedly: {current}")
        cursor.execute(
            "SELECT lesson_id FROM lesson_progress WHERE lesson_id IN (%s,%s,%s,%s) LIMIT 1",
            tuple(EXPECTED_EXISTING),
        )
        if cursor.fetchone():
            raise RuntimeError("A lesson that must move has learner progress; refusing to reorder it.")

        BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not BACKUP_PATH.exists():
            BACKUP_PATH.write_text(json.dumps({
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "purpose": "Before inserting ॠ, ऌ, ॡ and shifting the three following Sanskrit vowel lessons",
                "existing_lessons": rows,
                "new_characters": list(chars.values()),
            }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

        cursor.execute(
            "UPDATE learning_lessons SET lesson_order=10000+id WHERE id IN (%s,%s,%s,%s)",
            tuple(EXPECTED_EXISTING),
        )
        for lesson_id, order in FINAL_EXISTING.items():
            cursor.execute("UPDATE learning_lessons SET lesson_order=%s WHERE id=%s", (order, lesson_id))

        for glyph, content in NEW_GLYPHS.items():
            ordinal = {"ॠ": 8, "ऌ": 9, "ॡ": 10}[glyph]
            cursor.execute(
                """INSERT INTO learning_lessons
                   (language_id,category,title,content_text,translation_text,pronunciation_text,explanation,level,unit_number,lesson_order)
                   VALUES (%s,'character',%s,%s,%s,%s,%s,'foundation',1,%s)""",
                (language_id, f"स्वर · {glyph} ({content['pronunciation']} rare vowel)", glyph,
                 content["meaning"], content["pronunciation"], content["explanation"], ordinal),
            )
        connection.commit()
        print("Added ॠ, ऌ, ॡ between ऋ and ए; shifted existing lessons to preserve traditional order.")
        print("Existing learner progress and all attempt/score/quiz rows were preserved.")
        print(f"Pre-migration lesson backup: {BACKUP_PATH}")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    migrate()
