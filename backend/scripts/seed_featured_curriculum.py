# -*- coding: utf-8 -*-
"""
Seed featured curriculum for Sanskrit, Tamil, and Simplified Chinese.
Idempotent script: verifies language_id + title + level before any insert.
Preserves all existing rows; never updates or deletes.
"""

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.db.database import get_db_connection

# Lesson definitions
NEW_LESSONS = [
    # ----------------------------------------------------
    # SANSKRIT (Language ID 56: sa-devanagari)
    # Foundation Unit 1: Vowels अ, आ, इ, ई, उ (matching characters 216-220)
    # ----------------------------------------------------
    {
        "language_id": 56,
        "category": "character",
        "level": "foundation",
        "unit_number": 1,
        "lesson_order": 1,
        "title": "Vowel अ and its sound",
        "content_text": "अ",
        "pronunciation_text": "a",
        "translation_text": "Sanskrit short vowel a",
        "explanation": "Short open central vowel, pronounced like the 'u' in 'cup'. Base vowel of Devanagari.",
    },
    {
        "language_id": 56,
        "category": "character",
        "level": "foundation",
        "unit_number": 1,
        "lesson_order": 2,
        "title": "Vowel आ and its sound",
        "content_text": "आ",
        "pronunciation_text": "ā",
        "translation_text": "Sanskrit long vowel ā",
        "explanation": "Long open central vowel, held for twice the duration of short a, like 'a' in 'father'.",
    },
    {
        "language_id": 56,
        "category": "character",
        "level": "foundation",
        "unit_number": 1,
        "lesson_order": 3,
        "title": "Vowel इ and its sound",
        "content_text": "इ",
        "pronunciation_text": "i",
        "translation_text": "Sanskrit short vowel i",
        "explanation": "Short close front unrounded vowel, pronounced like 'i' in 'bit'.",
    },
    {
        "language_id": 56,
        "category": "character",
        "level": "foundation",
        "unit_number": 1,
        "lesson_order": 4,
        "title": "Vowel ई and its sound",
        "content_text": "ई",
        "pronunciation_text": "ī",
        "translation_text": "Sanskrit long vowel ī",
        "explanation": "Long close front unrounded vowel, held for twice the duration, like 'ee' in 'meet'.",
    },
    {
        "language_id": 56,
        "category": "character",
        "level": "foundation",
        "unit_number": 1,
        "lesson_order": 5,
        "title": "Vowel उ and its sound",
        "content_text": "उ",
        "pronunciation_text": "u",
        "translation_text": "Sanskrit short vowel u",
        "explanation": "Short close back rounded vowel, pronounced like 'u' in 'put'.",
    },
    # Sanskrit Beginner Unit 1: Essential Words
    {
        "language_id": 56,
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 1,
        "title": "Word: नमस्ते",
        "content_text": "नमस्ते",
        "pronunciation_text": "namaste",
        "translation_text": "Hello / Salutations",
        "explanation": "Common respectful Sanskrit greeting meaning 'salutations to you'.",
    },
    {
        "language_id": 56,
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 2,
        "title": "Word: जलम्",
        "content_text": "जलम्",
        "pronunciation_text": "jalam",
        "translation_text": "Water",
        "explanation": "Neuter noun meaning water (accusative/nominative singular).",
    },
    {
        "language_id": 56,
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 3,
        "title": "Word: मित्रम्",
        "content_text": "मित्रम्",
        "pronunciation_text": "mitram",
        "translation_text": "Friend",
        "explanation": "Neuter noun meaning friend.",
    },
    {
        "language_id": 56,
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 4,
        "title": "Word: पुस्तकम्",
        "content_text": "पुस्तकम्",
        "pronunciation_text": "pustakam",
        "translation_text": "Book",
        "explanation": "Neuter noun meaning book.",
    },

    # ----------------------------------------------------
    # CHINESE (Language ID 58: zh-hans)
    # Foundation Unit 1: Five prototype characters (一, 二, 三, 人, 大)
    # Tone marks: yī, èr, sān, rén, dà.
    # No Beginner unit (limited prototype).
    # ----------------------------------------------------
    {
        "language_id": 58,
        "category": "character",
        "level": "foundation",
        "unit_number": 1,
        "lesson_order": 1,
        "title": "Character 一 and its tone",
        "content_text": "一",
        "pronunciation_text": "yī",
        "translation_text": "One",
        "explanation": "Number one. High level first tone (55 pitch). Written with a single horizontal stroke (heng).",
    },
    {
        "language_id": 58,
        "category": "character",
        "level": "foundation",
        "unit_number": 1,
        "lesson_order": 2,
        "title": "Character 二 and its tone",
        "content_text": "二",
        "pronunciation_text": "èr",
        "translation_text": "Two",
        "explanation": "Number two. Falling fourth tone (51 pitch). Written with two horizontal strokes (top shorter).",
    },
    {
        "language_id": 58,
        "category": "character",
        "level": "foundation",
        "unit_number": 1,
        "lesson_order": 3,
        "title": "Character 三 and its tone",
        "content_text": "三",
        "pronunciation_text": "sān",
        "translation_text": "Three",
        "explanation": "Number three. High level first tone (55 pitch). Written with three horizontal strokes.",
    },
    {
        "language_id": 58,
        "category": "character",
        "level": "foundation",
        "unit_number": 1,
        "lesson_order": 4,
        "title": "Character 人 and its tone",
        "content_text": "人",
        "pronunciation_text": "rén",
        "translation_text": "Person / Human",
        "explanation": "Person or human. Rising second tone (35 pitch). Written with downward-left (pie) and downward-right (na).",
    },
    {
        "language_id": 58,
        "category": "character",
        "level": "foundation",
        "unit_number": 1,
        "lesson_order": 5,
        "title": "Character 大 and its tone",
        "content_text": "大",
        "pronunciation_text": "dà",
        "translation_text": "Big / Great",
        "explanation": "Big or great. Falling fourth tone (51 pitch). Depicts a person with arms outstretched.",
    },

    # ----------------------------------------------------
    # TAMIL (Language ID 19: ta)
    # Foundation: Reuses existing lessons 223, 224, 225, 226, 227 (NO INSERTS)
    # Beginner: Missing vocabulary words in Unit 5 complementing existing lesson 302
    # ----------------------------------------------------
    {
        "language_id": 19,
        "category": "word",
        "level": "beginner",
        "unit_number": 5,
        "lesson_order": 1,
        "title": "Word: வணக்கம்",
        "content_text": "வணக்கம்",
        "pronunciation_text": "vanakkam",
        "translation_text": "Hello / Greeting",
        "explanation": "Universal respectful Tamil greeting with palms joined.",
    },
    {
        "language_id": 19,
        "category": "word",
        "level": "beginner",
        "unit_number": 5,
        "lesson_order": 2,
        "title": "Word: நன்றி",
        "content_text": "நன்றி",
        "pronunciation_text": "nanri",
        "translation_text": "Thank you",
        "explanation": "Standard polite expression of gratitude in Tamil.",
    },
    {
        "language_id": 19,
        "category": "word",
        "level": "beginner",
        "unit_number": 5,
        "lesson_order": 3,
        "title": "Word: புத்தகம்",
        "content_text": "புத்தகம்",
        "pronunciation_text": "puththagam",
        "translation_text": "Book",
        "explanation": "Tamil noun meaning book.",
    },
    {
        "language_id": 19,
        "category": "word",
        "level": "beginner",
        "unit_number": 5,
        "lesson_order": 4,
        "title": "Word: தண்ணீர்",
        "content_text": "தண்ணீர்",
        "pronunciation_text": "thanneer",
        "translation_text": "Water",
        "explanation": "Noun meaning water, directly complementing sentence lesson 302 (நான் தண்ணீர் குடிக்கிறேன்.).",
    },
]


def seed():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Verify foreign keys (languages)
    cursor.execute("SELECT id, name, script_code FROM languages")
    valid_langs = {r['id']: r for r in cursor.fetchall()}
    for item in NEW_LESSONS:
        lid = item['language_id']
        if lid not in valid_langs:
            raise ValueError(f"Language ID {lid} not found in database!")

    # 2. Count before
    cursor.execute("SELECT COUNT(*) as cnt FROM learning_lessons")
    before_count = cursor.fetchone()['cnt']
    print(f"Total learning_lessons before seed: {before_count}")

    inserted = 0
    skipped = 0

    insert_sql = """
        INSERT INTO learning_lessons (
            language_id, category, title, content_text,
            translation_text, pronunciation_text, explanation,
            level, unit_number, lesson_order,
            tutorial_video_status
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            'not_started'
        )
    """

    for item in NEW_LESSONS:
        cursor.execute(
            """
            SELECT id FROM learning_lessons
            WHERE language_id = %s AND title = %s AND level = %s
            """,
            (item['language_id'], item['title'], item['level']),
        )
        existing = cursor.fetchone()
        if existing:
            skipped += 1
            print(f"[SKIPPED] Lang {item['language_id']} - '{item['title']}' (Level: {item['level']}) already exists (ID: {existing['id']})")
        else:
            cursor.execute(
                insert_sql,
                (
                    item['language_id'],
                    item['category'],
                    item['title'],
                    item['content_text'],
                    item['translation_text'],
                    item['pronunciation_text'],
                    item['explanation'],
                    item['level'],
                    item['unit_number'],
                    item['lesson_order'],
                ),
            )
            inserted += 1
            print(f"[INSERTED] Lang {item['language_id']} - '{item['title']}' (Level: {item['level']}, Unit: {item['unit_number']}, Ord: {item['lesson_order']})")

    conn.commit()

    # 3. Count after
    cursor.execute("SELECT COUNT(*) as cnt FROM learning_lessons")
    after_count = cursor.fetchone()['cnt']
    print(f"\nSeed completed:")
    print(f"- Total rows before: {before_count}")
    print(f"- Newly inserted: {inserted}")
    print(f"- Skipped (already existed): {skipped}")
    print(f"- Total rows after: {after_count}")
    print(f"- Python executable: {sys.executable}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    seed()
