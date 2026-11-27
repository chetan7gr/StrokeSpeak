# -*- coding: utf-8 -*-
"""Seed a modest Sanskrit Devanagari starter set (not a complete inventory)."""
import json
from datetime import datetime
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.db.database import get_db_connection  # noqa: E402

CHARACTERS = [
    ("अ", "Sanskrit short vowel a", "a"),
    ("आ", "Sanskrit long vowel ā", "ā"),
    ("इ", "Sanskrit short vowel i", "i"),
    ("ई", "Sanskrit long vowel ī", "ī"),
    ("उ", "Sanskrit short vowel u", "u"),
    ("ऊ", "Sanskrit long vowel ū", "ū"),
    ("ऋ", "Sanskrit vocalic r vowel", "ṛ"),
    ("ॠ", "Sanskrit long vocalic r vowel", "ṝ"),
    ("ऌ", "Sanskrit vocalic l vowel", "ḷ"),
    ("ॡ", "Sanskrit long vocalic l vowel", "ḹ"),
    ("ए", "Sanskrit vowel e", "e"),
    ("ऐ", "Sanskrit diphthong ai", "ai"),
    ("ओ", "Sanskrit vowel o", "o"),
    ("औ", "Sanskrit diphthong au", "au"),
    ("क", "Sanskrit velar consonant ka", "ka"),
    ("ख", "Sanskrit velar consonant kha", "kha"),
    ("ग", "Sanskrit velar consonant ga", "ga"),
    ("घ", "Sanskrit velar consonant gha", "gha"),
    ("ङ", "Sanskrit velar nasal ṅa", "ṅa"),
    ("ं", "Sanskrit anusvara nasal marker", "ṃ"),
]


def main():
    if len({glyph for glyph, _, _ in CHARACTERS}) != len(CHARACTERS):
        raise RuntimeError("Duplicate Sanskrit glyph in seed data.")
    if not all(all(0x0900 <= ord(ch) <= 0x097F for ch in glyph) for glyph, _, _ in CHARACTERS):
        raise RuntimeError("A Sanskrit glyph is outside U+0900-U+097F.")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    language_created = False
    language_updated = False
    name_backup = None
    inserted = skipped = 0
    try:
        cursor.execute("SELECT id, name, script_code, created_at FROM languages WHERE script_code = %s", ("sa-devanagari",))
        row = cursor.fetchone()
        if row:
            language_id = row["id"]
            if row["name"] != "Sanskrit":
                backup_dir = BACKEND / "db_backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
                name_backup = backup_dir / f"sanskrit-language-before-name-update-{stamp}.json"
                cursor.execute("SELECT COUNT(*) AS n FROM languages")
                language_count = cursor.fetchone()["n"]
                payload = {
                    "created_at_local": datetime.now().astimezone().isoformat(),
                    "purpose": "Pre-update backup for seed_sanskrit.py language-name correction",
                    "table_counts_before_update": {"languages": language_count},
                    "affected_rows": {"languages": [row]},
                }
                name_backup.write_text(
                    json.dumps(payload, ensure_ascii=False, default=str, indent=2),
                    encoding="utf-8",
                )
                cursor.execute(
                    "UPDATE languages SET name = %s WHERE id = %s AND script_code = %s",
                    ("Sanskrit", language_id, "sa-devanagari"),
                )
                language_updated = cursor.rowcount == 1
        else:
            cursor.execute(
                "INSERT INTO languages (name, script_code) VALUES (%s, %s)",
                ("Sanskrit", "sa-devanagari"),
            )
            language_id = cursor.lastrowid
            language_created = True
        for glyph, meaning, pronunciation in CHARACTERS:
            cursor.execute(
                "SELECT id FROM characters WHERE language_id = %s AND character_text = %s",
                (language_id, glyph),
            )
            if cursor.fetchone():
                skipped += 1
                continue
            cursor.execute(
                "INSERT INTO characters (language_id, character_text, meaning, pronunciation_text) "
                "VALUES (%s, %s, %s, %s)",
                (language_id, glyph, meaning, pronunciation),
            )
            inserted += 1
        connection.commit()
        print(f"Language ID: {language_id}; inserted language: {language_created}; updated name: {language_updated}")
        print(f"Inserted characters: {inserted}; skipped existing: {skipped}; updated characters: 0")
        if name_backup:
            print(f"Language row backup: {name_backup}")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
