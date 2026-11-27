"""Seed Japanese beginner words, grammar, and sentences in beginner order.

Idempotent: preserves existing lesson IDs, lesson text, and user progress.
Exports affected pre-existing rows to backend/db_backups before any UPDATE.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.db.database import get_db_connection  # noqa: E402

JAPANESE_LANGUAGE_ID = 5

# Beginner Unit 1: Essential everyday words (category: word)
BEGINNER_WORDS = [
    {
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 1,
        "title": "Word: Thank you",
        "content_text": "ありがとう",
        "translation_text": "Thank you",
        "pronunciation_text": "arigatou",
        "explanation": "A standard, friendly phrase to express gratitude in daily Japanese.",
    },
    {
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 2,
        "title": "Word: Yes",
        "content_text": "はい",
        "translation_text": "Yes",
        "pronunciation_text": "hai",
        "explanation": "Polite affirmative response; also used to acknowledge hearing someone speak.",
    },
    {
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 3,
        "title": "Word: No",
        "content_text": "いいえ",
        "translation_text": "No",
        "pronunciation_text": "iie",
        "explanation": "Polite negative response meaning 'no' or 'not at all / don't mention it'.",
    },
    {
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 4,
        "title": "Word: Excuse me / I'm sorry",
        "content_text": "すみません",
        "translation_text": "Excuse me / I'm sorry",
        "pronunciation_text": "sumimasen",
        "explanation": "An essential polite phrase used to get attention, apologise, or express polite gratitude.",
    },
    {
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 5,
        "title": "Word: Goodbye",
        "content_text": "さようなら",
        "translation_text": "Goodbye",
        "pronunciation_text": "sayounara",
        "explanation": "A traditional farewell greeting used when parting for a longer time.",
    },
    {
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 6,
        "title": "Word: Book",
        "content_text": "ほん",
        "translation_text": "Book",
        "pronunciation_text": "hon",
        "explanation": "A basic Japanese noun meaning book.",
    },
    {
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 7,
        "title": "Word: Green tea",
        "content_text": "おちゃ",
        "translation_text": "Green tea",
        "pronunciation_text": "ocha",
        "explanation": "The polite prefix お (o) is attached to ちゃ (cha, tea).",
    },
    {
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 8,
        "title": "Word: Meal / Rice",
        "content_text": "ごはん",
        "translation_text": "Rice / meal",
        "pronunciation_text": "gohan",
        "explanation": "Literally cooked rice; widely used to mean a meal (breakfast, lunch, or dinner).",
    },
    {
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 9,
        "title": "Word: Teacher",
        "content_text": "せんせい",
        "translation_text": "Teacher",
        "pronunciation_text": "sensei",
        "explanation": "Honorific title and noun used for teachers, doctors, and instructors.",
    },
    {
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 10,
        "title": "Word: Student",
        "content_text": "がくせい",
        "translation_text": "Student",
        "pronunciation_text": "gakusei",
        "explanation": "A general Japanese noun for student.",
    },
    {
        "category": "word",
        "level": "beginner",
        "unit_number": 1,
        "lesson_order": 11,
        "title": "Word: Friend",
        "content_text": "ともだち",
        "translation_text": "Friend",
        "pronunciation_text": "tomodachi",
        "explanation": "A common Japanese noun meaning friend.",
    },
]

# Beginner Unit 2: Basic grammar and particles (category: grammar)
BEGINNER_GRAMMAR = [
    {
        "category": "grammar",
        "level": "beginner",
        "unit_number": 2,
        "lesson_order": 1,
        "title": "Topic particle: は (wa)",
        "content_text": "は",
        "translation_text": "Topic marker (wa)",
        "pronunciation_text": "wa",
        "explanation": "When used as a grammatical particle marking the topic of a sentence, the Hiragana letter は is pronounced 'wa', not 'ha'.",
    },
    {
        "category": "grammar",
        "level": "beginner",
        "unit_number": 2,
        "lesson_order": 2,
        "title": "Polite copula: です (desu)",
        "content_text": "です",
        "translation_text": "is / am / are (polite)",
        "pronunciation_text": "desu",
        "explanation": "です (desu) is placed after a noun or adjective to make a polite statement meaning 'is', 'am', or 'are'.",
    },
    {
        "category": "grammar",
        "level": "beginner",
        "unit_number": 2,
        "lesson_order": 3,
        "title": "Question particle: か (ka)",
        "content_text": "か",
        "translation_text": "Question marker (ka)",
        "pronunciation_text": "ka",
        "explanation": "Adding か (ka) to the end of a polite sentence turns it into a question, acting like a spoken question mark.",
    },
    {
        "category": "grammar",
        "level": "beginner",
        "unit_number": 2,
        "lesson_order": 4,
        "title": "Object particle: を (o)",
        "content_text": "を",
        "translation_text": "Object marker (o)",
        "pronunciation_text": "o",
        "explanation": "The particle を is pronounced 'o' and follows the noun that directly receives the action of a verb.",
    },
    {
        "category": "grammar",
        "level": "beginner",
        "unit_number": 2,
        "lesson_order": 5,
        "title": "Inclusive particle: も (mo)",
        "content_text": "も",
        "translation_text": "also / too (mo)",
        "pronunciation_text": "mo",
        "explanation": "The particle も (mo) replaces the topic marker は to indicate that someone or something also shares the same quality or action.",
    },
    {
        "category": "grammar",
        "level": "beginner",
        "unit_number": 2,
        "lesson_order": 6,
        "title": "Direction particle: へ (e)",
        "content_text": "へ",
        "translation_text": "toward / to (direction particle e)",
        "pronunciation_text": "e",
        "explanation": "When used as a particle indicating direction toward a place, the Hiragana letter へ is pronounced 'e', not 'he'.",
    },
]

# Beginner Unit 3: First Japanese sentences (category: sentence)
# Note: Existing lessons 7 ("I drink water") and 287 ("Sentence practice: I read a book")
# belong in Unit 3 as orders 1 and 2.
NEW_BEGINNER_SENTENCES = [
    {
        "category": "sentence",
        "level": "beginner",
        "unit_number": 3,
        "lesson_order": 3,
        "title": "Sentence: I am a student",
        "content_text": "わたしは がくせいです。",
        "translation_text": "I am a student.",
        "pronunciation_text": "watashi wa gakusei desu",
        "explanation": "The fundamental identification sentence pattern: [Topic] は [Noun] です.",
    },
    {
        "category": "sentence",
        "level": "beginner",
        "unit_number": 3,
        "lesson_order": 4,
        "title": "Sentence: Mr./Ms. Tanaka is a teacher",
        "content_text": "たなかさんは せんせいです。",
        "translation_text": "Mr./Ms. Tanaka is a teacher.",
        "pronunciation_text": "tanaka-san wa sensei desu",
        "explanation": "さん (san) is a respectful title attached to names; せんせい (sensei) means teacher.",
    },
    {
        "category": "sentence",
        "level": "beginner",
        "unit_number": 3,
        "lesson_order": 5,
        "title": "Sentence: Are you a student?",
        "content_text": "がくせいですか。",
        "translation_text": "Are you a student?",
        "pronunciation_text": "gakusei desu ka",
        "explanation": "The question particle か at the end creates a polite question without repeating the subject.",
    },
    {
        "category": "sentence",
        "level": "beginner",
        "unit_number": 3,
        "lesson_order": 6,
        "title": "Sentence: I am also a student",
        "content_text": "わたしも がくせいです。",
        "translation_text": "I am also a student.",
        "pronunciation_text": "watashi mo gakusei desu",
        "explanation": "The particle も replaces は to express 'I am also a student'.",
    },
    {
        "category": "sentence",
        "level": "beginner",
        "unit_number": 3,
        "lesson_order": 7,
        "title": "Sentence: I drink green tea",
        "content_text": "おちゃを のみます。",
        "translation_text": "I drink green tea.",
        "pronunciation_text": "ocha o nomimasu",
        "explanation": "Polite sentence using the object particle を and the verb のみます (drink).",
    },
    {
        "category": "sentence",
        "level": "beginner",
        "unit_number": 3,
        "lesson_order": 8,
        "title": "Sentence: I eat a meal",
        "content_text": "ごはんを たべます。",
        "translation_text": "I eat a meal / rice.",
        "pronunciation_text": "gohan o tabemasu",
        "explanation": "Polite sentence using the object particle を and the verb たべます (eat).",
    },
]


def get_table_counts(cursor):
    tables = ["users", "languages", "characters", "learning_lessons", "lesson_progress", "practice_attempts"]
    counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) AS n FROM {table}")
        counts[table] = cursor.fetchone()["n"]
    return counts


def main():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        before_counts = get_table_counts(cursor)
        print("Table counts BEFORE seeding:")
        print(json.dumps(before_counts, indent=2))

        # Check existing beginner lessons (ID 7 and 287)
        cursor.execute(
            "SELECT id, language_id, category, level, unit_number, lesson_order, title, content_text, translation_text, pronunciation_text, explanation "
            "FROM learning_lessons WHERE language_id = %s AND level = 'beginner' ORDER BY id",
            (JAPANESE_LANGUAGE_ID,),
        )
        existing_beginner = cursor.fetchall()
        existing_by_id = {row["id"]: row for row in existing_beginner}
        existing_by_title = {row["title"]: row for row in existing_beginner}

        # Step 1: Pre-update backup if existing rows 7 or 287 need unit/order adjustment
        needs_resequence = []
        target_seq = {7: (3, 1), 287: (3, 2)}
        for lid, (target_unit, target_order) in target_seq.items():
            if lid in existing_by_id:
                curr = existing_by_id[lid]
                if (curr["unit_number"], curr["lesson_order"]) != (target_unit, target_order):
                    needs_resequence.append(curr)

        if needs_resequence:
            backup_dir = BACKEND / "db_backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")
            backup_file = backup_dir / f"japanese-beginner-lessons-before-seed-{stamp}.json"
            backup_payload = {
                "created_at_local": datetime.now().astimezone().isoformat(),
                "purpose": "Pre-UPDATE backup of existing Japanese beginner lessons before assigning Unit 3 order.",
                "table_counts_before": before_counts,
                "affected_rows": needs_resequence,
                "target_unit_and_order": {str(k): {"unit_number": v[0], "lesson_order": v[1]} for k, v in target_seq.items()},
            }
            backup_file.write_text(json.dumps(backup_payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            print(f"Pre-UPDATE JSON backup saved: {backup_file}")

            for lid, (target_unit, target_order) in target_seq.items():
                if lid in existing_by_id:
                    cursor.execute(
                        "UPDATE learning_lessons SET unit_number = %s, lesson_order = %s WHERE id = %s AND language_id = %s",
                        (target_unit, target_order, lid, JAPANESE_LANGUAGE_ID),
                    )
                    print(f"Updated existing lesson ID {lid} ('{existing_by_id[lid]['title']}') -> Unit {target_unit}, Order {target_order}")
            connection.commit()

        # Step 2: Insert new beginner lessons (idempotent, checking by (language_id, title))
        lessons_to_insert = BEGINNER_WORDS + BEGINNER_GRAMMAR + NEW_BEGINNER_SENTENCES
        inserted_count = 0
        skipped_count = 0

        insert_sql = """
            INSERT INTO learning_lessons
            (language_id, category, level, unit_number, lesson_order, title, content_text, translation_text, pronunciation_text, explanation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for lesson in lessons_to_insert:
            cursor.execute(
                "SELECT id, unit_number, lesson_order FROM learning_lessons WHERE language_id = %s AND title = %s",
                (JAPANESE_LANGUAGE_ID, lesson["title"]),
            )
            found = cursor.fetchone()
            if found:
                skipped_count += 1
                # If unit or order differs, keep it synchronized
                if (found["unit_number"], found["lesson_order"]) != (lesson["unit_number"], lesson["lesson_order"]):
                    cursor.execute(
                        "UPDATE learning_lessons SET unit_number = %s, lesson_order = %s WHERE id = %s",
                        (lesson["unit_number"], lesson["lesson_order"], found["id"]),
                    )
            else:
                cursor.execute(
                    insert_sql,
                    (
                        JAPANESE_LANGUAGE_ID,
                        lesson["category"],
                        lesson["level"],
                        lesson["unit_number"],
                        lesson["lesson_order"],
                        lesson["title"],
                        lesson["content_text"],
                        lesson["translation_text"],
                        lesson["pronunciation_text"],
                        lesson["explanation"],
                    ),
                )
                inserted_count += 1

        connection.commit()
        print(f"Seeding completed: {inserted_count} new lessons inserted, {skipped_count} existing lessons skipped.")

        # Step 3: Verification & counts after
        after_counts = get_table_counts(cursor)
        print("Table counts AFTER seeding:")
        print(json.dumps(after_counts, indent=2))

        # Check beginner lessons breakdown by unit
        cursor.execute(
            "SELECT unit_number, category, COUNT(*) AS count, MIN(lesson_order) AS min_order, MAX(lesson_order) AS max_order "
            "FROM learning_lessons WHERE language_id = %s AND level = 'beginner' "
            "GROUP BY unit_number, category ORDER BY unit_number, category",
            (JAPANESE_LANGUAGE_ID,),
        )
        units_summary = cursor.fetchall()
        print("Beginner units breakdown:")
        print(json.dumps(units_summary, indent=2))

        # Total Japanese lessons in database
        cursor.execute(
            "SELECT level, COUNT(*) AS count FROM learning_lessons WHERE language_id = %s GROUP BY level ORDER BY level",
            (JAPANESE_LANGUAGE_ID,),
        )
        levels_summary = cursor.fetchall()
        print("All Japanese lessons by level:")
        print(json.dumps(levels_summary, indent=2))

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
