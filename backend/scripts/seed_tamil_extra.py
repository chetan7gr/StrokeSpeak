# -*- coding: utf-8 -*-
"""Add five verified beginner Tamil consonants without changing existing rows."""
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.db.database import get_db_connection  # noqa: E402

CHARACTERS = [
    ("க", "Tamil consonant ka", "ka"),
    ("ச", "Tamil consonant ca", "ca"),
    ("ட", "Tamil consonant ṭa", "ṭa"),
    ("த", "Tamil consonant ta", "ta"),
    ("ப", "Tamil consonant pa", "pa"),
]


def main():
    if not all(len(glyph) == 1 and 0x0B80 <= ord(glyph) <= 0x0BFF for glyph, _, _ in CHARACTERS):
        raise RuntimeError("A Tamil glyph is outside U+0B80-U+0BFF.")
    connection = get_db_connection()
    cursor = connection.cursor()
    inserted = skipped = 0
    try:
        cursor.execute("SELECT id FROM languages WHERE id = %s AND script_code = %s", (19, "ta"))
        if cursor.fetchone() is None:
            raise RuntimeError("Tamil language ID 19/script ta was not found; no characters inserted.")
        for glyph, meaning, pronunciation in CHARACTERS:
            cursor.execute(
                "SELECT id FROM characters WHERE language_id = %s AND character_text = %s",
                (19, glyph),
            )
            if cursor.fetchone():
                skipped += 1
                continue
            cursor.execute(
                "INSERT INTO characters (language_id, character_text, meaning, pronunciation_text) "
                "VALUES (%s, %s, %s, %s)",
                (19, glyph, meaning, pronunciation),
            )
            inserted += 1
        connection.commit()
        print("Tamil language ID: 19")
        print(f"Inserted: {inserted}; skipped existing: {skipped}; updated: 0")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
