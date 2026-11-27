"""Additive, repeat-safe setup for course quizzes.

Run dry first:
  python backend/scripts/create_section_quizzes.py
Apply only after reviewing the dry-run summary:
  python backend/scripts/create_section_quizzes.py --apply

This adds missing Foundation end-of-level assessments and Beginner unit quizzes.
It never updates or deletes existing language, lesson, practice, or progress rows.
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.abspath("backend"))
from app.db.database import get_db_connection

PUBLIC_SCRIPT_CODES = ("ja-hiragana", "ja-katakana", "sa-devanagari", "ta", "zh-hans")
PLACEHOLDERS = ", ".join(["%s"] * len(PUBLIC_SCRIPT_CODES))

CREATE_SQL = [
    """CREATE TABLE IF NOT EXISTS section_quizzes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        language_id INT NOT NULL,
        level VARCHAR(20) NOT NULL DEFAULT 'beginner',
        unit_number INT NOT NULL,
        pass_percentage DECIMAL(5,2) NOT NULL DEFAULT 70.00,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uq_section_quiz (language_id, level, unit_number),
        CONSTRAINT fk_section_quiz_language FOREIGN KEY (language_id) REFERENCES languages(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS section_quiz_questions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        quiz_id INT NOT NULL,
        source_lesson_id INT NULL,
        question_order INT NOT NULL,
        prompt TEXT NOT NULL,
        options_json JSON NOT NULL,
        correct_option_index TINYINT UNSIGNED NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uq_section_quiz_question_order (quiz_id, question_order),
        CONSTRAINT fk_section_question_quiz FOREIGN KEY (quiz_id) REFERENCES section_quizzes(id) ON DELETE CASCADE,
        CONSTRAINT fk_section_question_lesson FOREIGN KEY (source_lesson_id) REFERENCES learning_lessons(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS section_quiz_attempts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        quiz_id INT NOT NULL,
        user_id INT NOT NULL,
        score DECIMAL(5,2) NOT NULL,
        correct_count SMALLINT UNSIGNED NOT NULL,
        question_count SMALLINT UNSIGNED NOT NULL,
        passed TINYINT(1) NOT NULL DEFAULT 0,
        answers_json JSON NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        KEY ix_section_quiz_attempt_history (quiz_id, user_id, created_at),
        CONSTRAINT fk_section_attempt_quiz FOREIGN KEY (quiz_id) REFERENCES section_quizzes(id),
        CONSTRAINT fk_section_attempt_user FOREIGN KEY (user_id) REFERENCES users(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
]


def clean(value):
    return str(value or "").strip()


def unique_values(rows, field):
    values = []
    seen = set()
    for row in rows:
        value = clean(row.get(field))
        if value and value not in seen:
            values.append(value)
            seen.add(value)
    return values


def build_candidates(section_rows, language_rows):
    pronunciations = unique_values(language_rows, "pronunciation_text")
    content_values = unique_values(language_rows, "content_text")
    translations = unique_values(language_rows, "translation_text")
    candidates = []
    seen = set()

    for lesson in section_rows:
        content = clean(lesson.get("content_text"))
        pronunciation = clean(lesson.get("pronunciation_text"))
        translation = clean(lesson.get("translation_text"))
        explanation = clean(lesson.get("explanation"))
        lesson_id = lesson["id"]

        candidate_rows = []
        if content and pronunciation:
            candidate_rows.append((f"Which pronunciation matches “{content}”?", pronunciation, pronunciations))
            candidate_rows.append((f"Which written item is read as “{pronunciation}”?", content, content_values))
        if content and translation:
            candidate_rows.append((f"What does “{content}” mean?", translation, translations))
        if content and explanation and not translation:
            candidate_rows.append((f"Which item is described here: {explanation[:180]}?", content, content_values))

        for prompt, correct, pool in candidate_rows:
            key = (prompt, correct)
            if key in seen:
                continue
            distractors = [value for value in pool if value != correct]
            if len(distractors) < 3:
                continue
            candidates.append({
                "source_lesson_id": lesson_id,
                "prompt": prompt,
                "correct": correct,
                "distractors": distractors,
            })
            seen.add(key)

    return candidates


def choose_options(candidate, seed):
    distractors = list(candidate["distractors"])
    rng = random.Random(seed)
    rng.shuffle(distractors)
    options = [candidate["correct"], *distractors[:3]]
    rng.shuffle(options)
    return options, options.index(candidate["correct"])


def spread_questions(candidates, limit=10):
    """Pick a deterministic sample across the full Foundation lesson sequence."""
    if len(candidates) <= limit:
        return candidates
    return [candidates[(index * (len(candidates) - 1)) // (limit - 1)] for index in range(limit)]


def load_sections(cursor):
    cursor.execute(
        f"""SELECT ll.id, ll.language_id, l.name AS language_name, l.script_code,
                   ll.level, ll.unit_number, ll.lesson_order, ll.category, ll.title,
                   ll.content_text, ll.translation_text, ll.pronunciation_text, ll.explanation
            FROM learning_lessons ll
            JOIN languages l ON l.id=ll.language_id
            WHERE l.script_code IN ({PLACEHOLDERS})
            ORDER BY ll.language_id, ll.unit_number, ll.lesson_order, ll.id""",
        PUBLIC_SCRIPT_CODES,
    )
    rows = cursor.fetchall()
    language_rows = {}
    sections = {}
    foundation_levels = {}
    for row in rows:
        language_rows.setdefault(row["language_id"], []).append(row)
        if row["level"] == "beginner":
            key = (row["language_id"], row["unit_number"])
            sections.setdefault(key, []).append(row)
        elif row["level"] == "foundation":
            foundation_levels.setdefault(row["language_id"], []).append(row)
    return language_rows, sections, foundation_levels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Create quiz tables and insert missing course quizzes.")
    args = parser.parse_args()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        language_rows, sections, foundation_levels = load_sections(cursor)
        planned = []
        for (language_id, unit_number), rows in sorted(sections.items()):
            language = rows[0]["language_name"]
            code = rows[0]["script_code"]
            candidates = build_candidates(rows, language_rows.get(language_id, []))
            questions = candidates[:5]
            planned.append((language_id, "beginner", unit_number, language, code, len(rows), questions))
            print(f"{language} [{code}] beginner unit {unit_number}: {len(rows)} lessons, {len(questions)} quiz questions")
            for question in questions:
                print(f"  - {ascii(question['prompt'][:100])}")

        for language_id, rows in sorted(foundation_levels.items()):
            language = rows[0]["language_name"]
            code = rows[0]["script_code"]
            candidates = build_candidates(rows, language_rows.get(language_id, []))
            questions = spread_questions(candidates, 10)
            planned.append((language_id, "foundation", 0, language, code, len(rows), questions))
            print(f"{language} [{code}] Foundation level end: {len(rows)} lessons, {len(questions)} quiz questions")
            for question in questions:
                print(f"  - {ascii(question['prompt'][:100])}")

        if not args.apply:
            print("\nDry run only. No database tables or rows were changed. Re-run with --apply to add the quiz tables and questions.")
            return

        for statement in CREATE_SQL:
            cursor.execute(statement)
        connection.commit()

        inserted_quizzes = 0
        inserted_questions = 0
        skipped = 0
        for language_id, level, unit_number, language, code, lesson_count, questions in planned:
            if len(questions) < 3:
                label = "Foundation level" if level == "foundation" else f"{level} unit {unit_number}"
                print(f"SKIP {language} [{code}] {label}: fewer than 3 usable questions.")
                continue
            cursor.execute(
                "SELECT id FROM section_quizzes WHERE language_id=%s AND level=%s AND unit_number=%s",
                (language_id, level, unit_number),
            )
            quiz_row = cursor.fetchone()
            if quiz_row:
                quiz_id = int(quiz_row["id"])
            else:
                cursor.execute(
                    "INSERT INTO section_quizzes (language_id, level, unit_number, pass_percentage) VALUES (%s,%s,%s,70.00)",
                    (language_id, level, unit_number),
                )
                quiz_id = cursor.lastrowid
                inserted_quizzes += 1

            cursor.execute("SELECT COUNT(*) AS n FROM section_quiz_questions WHERE quiz_id=%s", (quiz_id,))
            if int(cursor.fetchone()["n"]) > 0:
                skipped += 1
                continue
            for order, question in enumerate(questions, start=1):
                options, correct_index = choose_options(question, f"{language_id}:{unit_number}:{order}")
                cursor.execute(
                    """INSERT INTO section_quiz_questions
                       (quiz_id, source_lesson_id, question_order, prompt, options_json, correct_option_index)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (quiz_id, question["source_lesson_id"], order, question["prompt"],
                     json.dumps(options, ensure_ascii=False), correct_index),
                )
                inserted_questions += 1

        connection.commit()
        print(f"Applied successfully. New quizzes: {inserted_quizzes}; new questions: {inserted_questions}; existing quizzes preserved: {skipped}.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
