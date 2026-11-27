# -*- coding: utf-8 -*-
"""Seed the 46 basic Japanese Katakana characters in gojuon order."""
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.db.database import get_db_connection  # noqa: E402

CHARACTERS = [
    ("ア", "a"), ("イ", "i"), ("ウ", "u"), ("エ", "e"), ("オ", "o"),
    ("カ", "ka"), ("キ", "ki"), ("ク", "ku"), ("ケ", "ke"), ("コ", "ko"),
    ("サ", "sa"), ("シ", "shi"), ("ス", "su"), ("セ", "se"), ("ソ", "so"),
    ("タ", "ta"), ("チ", "chi"), ("ツ", "tsu"), ("テ", "te"), ("ト", "to"),
    ("ナ", "na"), ("ニ", "ni"), ("ヌ", "nu"), ("ネ", "ne"), ("ノ", "no"),
    ("ハ", "ha"), ("ヒ", "hi"), ("フ", "fu"), ("ヘ", "he"), ("ホ", "ho"),
    ("マ", "ma"), ("ミ", "mi"), ("ム", "mu"), ("メ", "me"), ("モ", "mo"),
    ("ヤ", "ya"), ("ユ", "yu"), ("ヨ", "yo"),
    ("ラ", "ra"), ("リ", "ri"), ("ル", "ru"), ("レ", "re"), ("ロ", "ro"),
    ("ワ", "wa"), ("ヲ", "o"), ("ン", "n"),
]


def main():
    if len(CHARACTERS) != 46 or len({glyph for glyph, _ in CHARACTERS}) != 46:
        raise RuntimeError("The Katakana data must contain 46 unique glyphs.")
    if not all(len(glyph) == 1 and 0x30A0 <= ord(glyph) <= 0x30FF for glyph, _ in CHARACTERS):
        raise RuntimeError("A Katakana glyph is outside U+30A0-U+30FF.")
    connection = get_db_connection()
    cursor = connection.cursor()
    language_created = False
    inserted = skipped = 0
    try:
        cursor.execute("SELECT id FROM languages WHERE script_code = %s", ("ja-katakana",))
        row = cursor.fetchone()
        if row:
            language_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO languages (name, script_code) VALUES (%s, %s)",
                ("Japanese Katakana", "ja-katakana"),
            )
            language_id = cursor.lastrowid
            language_created = True
        for glyph, pronunciation in CHARACTERS:
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
                (language_id, glyph, "Japanese Katakana character", pronunciation),
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
