# -*- coding: utf-8 -*-
"""Seed a small Simplified Chinese Hanzi starter set (not a complete inventory)."""
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.db.database import get_db_connection  # noqa: E402

CHARACTERS = [
    ("一", "one", "yī"),
    ("二", "two", "èr"),
    ("三", "three", "sān"),
    ("人", "person", "rén"),
    ("大", "big", "dà"),
    ("小", "small", "xiǎo"),
    ("口", "mouth", "kǒu"),
    ("日", "sun; day", "rì"),
    ("月", "moon; month", "yuè"),
    ("水", "water", "shuǐ"),
    ("火", "fire", "huǒ"),
    ("山", "mountain", "shān"),
]


def main():
    if len({glyph for glyph, _, _ in CHARACTERS}) != len(CHARACTERS):
        raise RuntimeError("Duplicate Hanzi in seed data.")
    if not all(len(glyph) == 1 and 0x4E00 <= ord(glyph) <= 0x9FFF for glyph, _, _ in CHARACTERS):
        raise RuntimeError("A Hanzi is outside CJK Unified Ideographs U+4E00-U+9FFF.")
    connection = get_db_connection()
    cursor = connection.cursor()
    language_created = False
    inserted = skipped = 0
    try:
        cursor.execute("SELECT id FROM languages WHERE script_code = %s", ("zh-hans",))
        row = cursor.fetchone()
        if row:
            language_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO languages (name, script_code) VALUES (%s, %s)",
                ("Chinese (Simplified)", "zh-hans"),
            )
            language_id = cursor.lastrowid
            language_created = True
        for glyph, meaning, pinyin in CHARACTERS:
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
                (language_id, glyph, meaning, pinyin),
            )
            inserted += 1
        connection.commit()
        print(f"Language ID: {language_id}; inserted language: {language_created}")
        print(f"Inserted: {inserted}; skipped existing: {skipped}; updated: 0")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
