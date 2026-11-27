"""Section quiz APIs for the public StrokeSpeak beginner curricula.

The quiz tables are additive and are created by scripts/create_section_quizzes.py.
This module never changes existing lesson or progress rows.
"""
import json
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from mysql.connector import Error
from pydantic import BaseModel, Field

from app.db.database import get_db_connection
from app.security import (
    get_current_admin_user_id,
    get_current_user_id,
    has_demo_quiz_access,
    is_developer_user_id,
    require_user_scope,
)

router = APIRouter(prefix="/api/v1", tags=["section-quizzes"])
PUBLIC_SCRIPT_CODES = ("ja-hiragana", "ja-katakana", "sa-devanagari", "ta", "zh-hans")
SCRIPT_PLACEHOLDERS = ", ".join(["%s"] * len(PUBLIC_SCRIPT_CODES))

# These existing demo accounts may preview the Foundation assessment early.
# User 12's new access is quiz-only and must not unlock lessons or chapters.
FOUNDATION_QUIZ_EARLY_ACCESS_USER_IDS = frozenset({13})


def _has_developer_progress_bypass(user_id):
    """Developer lesson bypass is restricted to the explicit developer allowlist."""
    return is_developer_user_id(int(user_id))


def _has_demo_quiz_access(user_id):
    """Demo access opens quizzes only; lesson and chapter prerequisites stay intact."""
    return has_demo_quiz_access(int(user_id))


def _has_foundation_quiz_early_access(quiz, user_id):
    return str(quiz["level"]).casefold() == "foundation" and int(user_id) in FOUNDATION_QUIZ_EARLY_ACCESS_USER_IDS


class QuizAnswer(BaseModel):
    question_id: int = Field(gt=0)
    selected_option_index: int = Field(ge=0, le=3)


class QuizAttemptSubmission(BaseModel):
    user_id: int = Field(gt=0)
    answers: List[QuizAnswer] = Field(min_length=1, max_length=20)


class QuizPreviewSubmission(BaseModel):
    answers: List[QuizAnswer] = Field(min_length=1, max_length=20)


def _json_value(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


def _section_complete(cursor, user_id, language_id, level, unit_number):
    cursor.execute(
        """SELECT COUNT(*) AS total,
                  SUM(CASE WHEN lp.status = 'completed' THEN 1 ELSE 0 END) AS completed
           FROM learning_lessons ll
           LEFT JOIN lesson_progress lp
             ON lp.lesson_id = ll.id AND lp.user_id = %s
           WHERE ll.language_id = %s AND ll.level = %s AND ll.unit_number = %s""",
        (user_id, language_id, level, unit_number),
    )
    row = cursor.fetchone() or {}
    total = int(row.get("total") or 0)
    completed = int(row.get("completed") or 0)
    return total, completed, total > 0 and completed == total


def _beginner_unlocked(cursor, user_id, language_id):
    if _has_developer_progress_bypass(user_id):
        return True
    total, completed, lessons_done = _level_progress(cursor, user_id, language_id, "foundation")
    early_quiz_access = int(user_id) in FOUNDATION_QUIZ_EARLY_ACCESS_USER_IDS
    if not lessons_done and not early_quiz_access:
        return False
    cursor.execute(
        """SELECT COUNT(DISTINCT sq.id) AS quiz_count,
                  COUNT(DISTINCT CASE WHEN qa.passed=1 THEN sq.id END) AS passed_count
           FROM section_quizzes sq
           LEFT JOIN section_quiz_attempts qa
             ON qa.quiz_id=sq.id AND qa.user_id=%s
           WHERE sq.language_id=%s AND sq.level='foundation'""",
        (user_id, language_id),
    )
    quiz_progress = cursor.fetchone() or {}
    quiz_count = int(quiz_progress.get("quiz_count") or 0)
    passed_count = int(quiz_progress.get("passed_count") or 0)
    # Preserve legacy behavior if a deployment has not seeded the optional
    # Foundation assessment yet; once present, it is required to enter Beginner.
    if quiz_count == 0:
        return lessons_done
    return passed_count == quiz_count


def _elementary_unlocked(cursor, user_id, language_id):
    if _has_developer_progress_bypass(user_id):
        return True
    cursor.execute(
        "SELECT DISTINCT unit_number FROM learning_lessons WHERE language_id=%s AND level='beginner' ORDER BY unit_number",
        (language_id,),
    )
    units = [int(row["unit_number"]) for row in cursor.fetchall()]
    if not units:
        return False
    for unit in units:
        _, _, lessons_done = _section_complete(cursor, user_id, language_id, "beginner", unit)
        if not lessons_done:
            return False
        cursor.execute(
            """SELECT sq.id FROM section_quizzes sq
               JOIN section_quiz_attempts qa ON qa.quiz_id=sq.id AND qa.user_id=%s AND qa.passed=1
               WHERE sq.language_id=%s AND sq.level='beginner' AND sq.unit_number=%s
               LIMIT 1""",
            (user_id, language_id, unit),
        )
        if cursor.fetchone() is None:
            return False
    return True


def _section_unlocked(cursor, user_id, language_id, unit_number):
    if _has_developer_progress_bypass(user_id):
        return True
    cursor.execute(
        "SELECT MIN(unit_number) AS first_unit FROM learning_lessons WHERE language_id=%s AND level='beginner'",
        (language_id,),
    )
    row = cursor.fetchone() or {}
    first_unit = row.get("first_unit")
    if first_unit is None:
        return False
    if int(unit_number) == int(first_unit):
        return _beginner_unlocked(cursor, user_id, language_id)

    cursor.execute(
        "SELECT MAX(unit_number) AS previous_unit FROM learning_lessons "
        "WHERE language_id=%s AND level='beginner' AND unit_number < %s",
        (language_id, unit_number),
    )
    previous = (cursor.fetchone() or {}).get("previous_unit")
    if previous is None:
        return False
    _, _, lessons_done = _section_complete(cursor, user_id, language_id, "beginner", int(previous))
    if not lessons_done:
        return False
    cursor.execute(
        """SELECT sq.id FROM section_quizzes sq
           JOIN section_quiz_attempts qa ON qa.quiz_id=sq.id AND qa.user_id=%s AND qa.passed=1
           WHERE sq.language_id=%s AND sq.level='beginner' AND sq.unit_number=%s
           LIMIT 1""",
        (user_id, language_id, int(previous)),
    )
    return cursor.fetchone() is not None


def _level_progress(cursor, user_id, language_id, level):
    cursor.execute(
        "SELECT COUNT(*) AS total, SUM(CASE WHEN lp.status='completed' THEN 1 ELSE 0 END) AS completed "
        "FROM learning_lessons ll LEFT JOIN lesson_progress lp ON lp.lesson_id=ll.id AND lp.user_id=%s "
        "WHERE ll.language_id=%s AND ll.level=%s",
        (user_id, language_id, level),
    )
    row = cursor.fetchone() or {}
    total = int(row.get("total") or 0)
    completed = int(row.get("completed") or 0)
    return total, completed, total > 0 and completed == total


def _level_complete(cursor, user_id, language_id, level):
    return _level_progress(cursor, user_id, language_id, level)[2]


def _previous_unit_complete(cursor, user_id, language_id, level, unit_number):
    if unit_number is None:
        return False
    cursor.execute(
        "SELECT MAX(unit_number) AS previous_unit FROM learning_lessons "
        "WHERE language_id=%s AND level=%s AND unit_number < %s",
        (language_id, level, unit_number),
    )
    previous = (cursor.fetchone() or {}).get("previous_unit")
    if previous is None:
        return True
    _, _, complete = _section_complete(cursor, user_id, language_id, level, int(previous))
    return complete


def _lesson_is_unlocked(cursor, user_id, language_id, level, unit_number):
    if _has_developer_progress_bypass(user_id):
        return True
    normalized_level = str(level or "").strip().casefold()
    if normalized_level == "foundation":
        return _previous_unit_complete(cursor, user_id, language_id, normalized_level, unit_number)
    if normalized_level == "beginner":
        return _section_unlocked(cursor, user_id, language_id, unit_number)
    if normalized_level == "elementary":
        return _elementary_unlocked(cursor, user_id, language_id) and _previous_unit_complete(
            cursor, user_id, language_id, normalized_level, unit_number
        )

    prerequisite_level = {
        "intermediate": "elementary",
        "advanced": "intermediate",
    }.get(normalized_level)
    if prerequisite_level is None:
        return False
    if not _level_complete(cursor, user_id, language_id, prerequisite_level):
        return False
    return _previous_unit_complete(cursor, user_id, language_id, normalized_level, unit_number)


def _quiz_status(cursor, quiz, user_id):
    if str(quiz["level"]).casefold() == "foundation":
        total, completed, lessons_done = _level_progress(
            cursor, user_id, quiz["language_id"], "foundation"
        )
        unlocked = True
    else:
        total, completed, lessons_done = _section_complete(
            cursor, user_id, quiz["language_id"], quiz["level"], quiz["unit_number"]
        )
        unlocked = _section_unlocked(cursor, user_id, quiz["language_id"], quiz["unit_number"])
    cursor.execute(
        "SELECT COUNT(*) AS attempt_count, MAX(score) AS best_score, "
        "MAX(CASE WHEN passed=1 THEN 1 ELSE 0 END) AS passed "
        "FROM section_quiz_attempts WHERE quiz_id=%s AND user_id=%s",
        (quiz["id"], user_id),
    )
    stats = cursor.fetchone() or {}
    developer_mode = _has_developer_progress_bypass(user_id)
    demo_quiz_access = _has_demo_quiz_access(user_id)
    lesson_requirement_override = (
        not lessons_done
        and (
            developer_mode
            or demo_quiz_access
            or _has_foundation_quiz_early_access(quiz, user_id)
        )
    )
    return {
        **quiz,
        "lesson_count": total,
        "completed_lessons": completed,
        "lessons_complete": lessons_done,
        "lesson_requirement_override": lesson_requirement_override,
        "developer_mode": developer_mode,
        "demo_quiz_access": demo_quiz_access,
        "is_unlocked": unlocked,
        "quiz_available": developer_mode or demo_quiz_access or (unlocked and (lessons_done or lesson_requirement_override)),
        "attempt_count": int(stats.get("attempt_count") or 0),
        "best_score": float(stats["best_score"]) if stats.get("best_score") is not None else None,
        "passed": bool(stats.get("passed") or 0),
    }


@router.get("/section-quizzes")
def list_section_quizzes(
    language_id: int = Query(gt=0),
    user_id: int = Query(gt=0),
    current_user_id: int = Depends(get_current_user_id),
):
    require_user_scope(current_user_id, user_id)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"SELECT id, script_code FROM languages WHERE id=%s AND script_code IN ({SCRIPT_PLACEHOLDERS})",
            (language_id, *PUBLIC_SCRIPT_CODES),
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Language was not found.")
        cursor.execute("SELECT id FROM users WHERE id=%s", (user_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Learner was not found.")
        cursor.execute(
            "SELECT id, language_id, level, unit_number, pass_percentage "
            "FROM section_quizzes WHERE language_id=%s ORDER BY FIELD(level,'foundation','beginner','elementary'), unit_number",
            (language_id,),
        )
        quizzes = [_quiz_status(cursor, quiz, user_id) for quiz in cursor.fetchall()]
        beginner_units = sorted({
            int(q["unit_number"]) for q in quizzes if q["level"] == "beginner"
        })
        elementary_unlocked = _elementary_unlocked(cursor, user_id, language_id)
        beginner_unlocked = _beginner_unlocked(cursor, user_id, language_id)
        return {"quizzes": quizzes, "progression": {
            "beginner_unlocked": beginner_unlocked,
            "elementary_unlocked": elementary_unlocked,
        }}
    except HTTPException:
        raise
    except Error:
        raise HTTPException(status_code=500, detail="Could not retrieve section quizzes. Run the additive quiz setup script.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@router.get("/section-quizzes/{quiz_id}")
def get_section_quiz(quiz_id: int, user_id: int = Query(gt=0), current_user_id: int = Depends(get_current_user_id)):
    require_user_scope(current_user_id, user_id)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT sq.id, sq.language_id, sq.level, sq.unit_number, sq.pass_percentage
                FROM section_quizzes sq JOIN languages l ON l.id=sq.language_id
                WHERE sq.id=%s AND l.script_code IN ({SCRIPT_PLACEHOLDERS})""",
            (quiz_id, *PUBLIC_SCRIPT_CODES),
        )
        quiz = cursor.fetchone()
        if quiz is None:
            raise HTTPException(status_code=404, detail="Section quiz was not found.")
        cursor.execute("SELECT id FROM users WHERE id=%s", (user_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Learner was not found.")
        status = _quiz_status(cursor, quiz, user_id)
        if not status["quiz_available"]:
            if not status["is_unlocked"]:
                raise HTTPException(status_code=403, detail="Complete the previous course section to unlock this section.")
            detail = (
                "Complete every Foundation lesson before taking the Foundation level quiz."
                if quiz["level"] == "foundation"
                else "Complete every lesson in this section before taking its quiz."
            )
            raise HTTPException(status_code=409, detail=detail)
        cursor.execute(
            "SELECT id, question_order, prompt, options_json FROM section_quiz_questions "
            "WHERE quiz_id=%s ORDER BY question_order",
            (quiz_id,),
        )
        questions = []
        for question in cursor.fetchall():
            questions.append({
                "id": question["id"],
                "question_order": question["question_order"],
                "prompt": question["prompt"],
                "options": _json_value(question["options_json"]),
            })
        if len(questions) < 3:
            raise HTTPException(status_code=409, detail="This section does not yet have enough quiz questions.")
        cursor.execute(
            "SELECT id, score, correct_count, question_count, passed, created_at "
            "FROM section_quiz_attempts WHERE quiz_id=%s AND user_id=%s "
            "ORDER BY created_at DESC, id DESC LIMIT 10",
            (quiz_id, user_id),
        )
        history = cursor.fetchall()
        return {
            "quiz": status,
            "questions": questions,
            "history": history,
        }
    except HTTPException:
        raise
    except Error:
        raise HTTPException(status_code=500, detail="Could not load this section quiz.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@router.get("/admin/section-quizzes")
def list_admin_section_quizzes(
    current_admin_id: int = Depends(get_current_admin_user_id),
):
    """List quiz metadata for an administrator without reading learner progress."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT sq.id, sq.language_id,
                       CASE
                           WHEN l.script_code IN ('ja-hiragana', 'ja-katakana') THEN 'Japanese'
                           WHEN l.script_code = 'sa-devanagari' THEN 'Sanskrit'
                           WHEN l.script_code = 'ta' THEN 'Tamil'
                           WHEN l.script_code = 'zh-hans' THEN 'Chinese'
                           ELSE l.name
                       END AS language_name,
                       l.script_code, sq.level, sq.unit_number,
                       sq.pass_percentage, COUNT(sqq.id) AS question_count
                FROM section_quizzes sq
                JOIN languages l ON l.id = sq.language_id
                LEFT JOIN section_quiz_questions sqq ON sqq.quiz_id = sq.id
                WHERE l.script_code IN ({SCRIPT_PLACEHOLDERS})
                GROUP BY sq.id, sq.language_id, l.name, l.script_code,
                         sq.level, sq.unit_number, sq.pass_percentage
                ORDER BY FIELD(l.script_code, 'ja-hiragana', 'ja-katakana',
                               'sa-devanagari', 'ta', 'zh-hans'),
                         FIELD(sq.level, 'foundation', 'beginner', 'elementary',
                               'intermediate', 'advanced'),
                         sq.unit_number, sq.id""",
            PUBLIC_SCRIPT_CODES,
        )
        quizzes = []
        for row in cursor.fetchall():
            quizzes.append({
                "id": int(row["id"]),
                "language_id": int(row["language_id"]),
                "language_name": row["language_name"],
                "script_code": row["script_code"],
                "level": row["level"],
                "unit_number": int(row["unit_number"]),
                "pass_percentage": float(row["pass_percentage"]),
                "question_count": int(row["question_count"]),
            })
        return {"quizzes": quizzes}
    except Error:
        raise HTTPException(status_code=500, detail="Could not retrieve the developer quiz list.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@router.get("/admin/section-quizzes/{quiz_id}/preview")
def preview_section_quiz(
    quiz_id: int,
    current_admin_id: int = Depends(get_current_admin_user_id),
):
    """Read-only author preview. Includes answer keys and never checks learner progress."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT sq.id, sq.language_id, l.name AS language_name, sq.level,
                       sq.unit_number, sq.pass_percentage
                FROM section_quizzes sq JOIN languages l ON l.id=sq.language_id
                WHERE sq.id=%s AND l.script_code IN ({SCRIPT_PLACEHOLDERS})""",
            (quiz_id, *PUBLIC_SCRIPT_CODES),
        )
        quiz = cursor.fetchone()
        if quiz is None:
            raise HTTPException(status_code=404, detail="Section quiz was not found.")
        cursor.execute(
            """SELECT q.id, q.question_order, q.prompt, q.options_json,
                      q.correct_option_index, ll.title AS source_lesson_title,
                      ll.explanation AS explanation
               FROM section_quiz_questions q
               LEFT JOIN learning_lessons ll ON ll.id = q.source_lesson_id
               WHERE q.quiz_id=%s ORDER BY q.question_order""",
            (quiz_id,),
        )
        questions = []
        for question in cursor.fetchall():
            options = _json_value(question["options_json"])
            correct_index = int(question["correct_option_index"])
            if not isinstance(options, list) or correct_index < 0 or correct_index >= len(options):
                raise HTTPException(status_code=409, detail="This quiz contains an invalid answer key.")
            questions.append({
                "id": int(question["id"]),
                "question_order": int(question["question_order"]),
                "prompt": question["prompt"],
                "options": options,
                "correct_option_index": correct_index,
                "correct_option": options[correct_index],
                "source_lesson_title": question.get("source_lesson_title"),
                "explanation": question.get("explanation") or "",
            })
        if len(questions) < 3:
            raise HTTPException(status_code=409, detail="This section does not yet have enough quiz questions.")
        return {
            "preview_only": True,
            "learner_progress_changed": False,
            "quiz": {
                "id": int(quiz["id"]),
                "language_id": int(quiz["language_id"]),
                "language_name": quiz["language_name"],
                "level": quiz["level"],
                "unit_number": int(quiz["unit_number"]),
                "pass_percentage": float(quiz["pass_percentage"]),
            },
            "questions": questions,
        }
    except HTTPException:
        raise
    except Error:
        raise HTTPException(status_code=500, detail="Could not load the quiz preview.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@router.post("/admin/section-quizzes/{quiz_id}/preview-grade")
def grade_section_quiz_preview(
    quiz_id: int,
    submission: QuizPreviewSubmission,
    current_admin_id: int = Depends(get_current_admin_user_id),
):
    """Score a creator's quiz preview without creating a learner attempt or unlock."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT sq.id, sq.pass_percentage
                FROM section_quizzes sq JOIN languages l ON l.id=sq.language_id
                WHERE sq.id=%s AND l.script_code IN ({SCRIPT_PLACEHOLDERS})""",
            (quiz_id, *PUBLIC_SCRIPT_CODES),
        )
        quiz = cursor.fetchone()
        if quiz is None:
            raise HTTPException(status_code=404, detail="Section quiz was not found.")
        cursor.execute(
            "SELECT id, question_order, prompt, options_json, correct_option_index "
            "FROM section_quiz_questions WHERE quiz_id=%s ORDER BY question_order",
            (quiz_id,),
        )
        questions = cursor.fetchall()
        if len(questions) < 3:
            raise HTTPException(status_code=409, detail="This section does not yet have enough quiz questions.")
        submitted = {}
        for answer in submission.answers:
            if answer.question_id in submitted:
                raise HTTPException(status_code=422, detail="Each quiz question can be answered only once.")
            submitted[answer.question_id] = answer.selected_option_index
        valid_ids = {int(question["id"]) for question in questions}
        if set(submitted) != valid_ids:
            raise HTTPException(status_code=422, detail="Answer every question in this section preview.")
        correct_count = 0
        answer_records = []
        for question in questions:
            options = _json_value(question["options_json"])
            correct_index = int(question["correct_option_index"])
            if not isinstance(options, list) or correct_index < 0 or correct_index >= len(options):
                raise HTTPException(status_code=409, detail="This quiz contains an invalid answer key.")
            selected = submitted[int(question["id"])]
            if selected >= len(options):
                raise HTTPException(status_code=422, detail="A selected answer is invalid.")
            correct = selected == correct_index
            correct_count += int(correct)
            answer_records.append({
                "question_id": int(question["id"]),
                "selected_option_index": selected,
                "correct": correct,
                "correct_option_index": correct_index,
                "correct_option": options[correct_index],
            })
        count = len(questions)
        score = round(correct_count * 100 / count, 2)
        pass_percentage = float(quiz["pass_percentage"])
        return {
            "preview_only": True,
            "learner_progress_changed": False,
            "score": score,
            "correct_count": correct_count,
            "question_count": count,
            "pass_percentage": pass_percentage,
            "would_pass": score >= pass_percentage,
            "answers": answer_records,
        }
    except HTTPException:
        raise
    except Error:
        raise HTTPException(status_code=500, detail="Could not grade the quiz preview.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@router.post("/section-quizzes/{quiz_id}/attempts", status_code=201)
def submit_section_quiz(quiz_id: int, submission: QuizAttemptSubmission, current_user_id: int = Depends(get_current_user_id)):
    require_user_scope(current_user_id, submission.user_id)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            f"""SELECT sq.id, sq.language_id, sq.level, sq.unit_number, sq.pass_percentage
                FROM section_quizzes sq JOIN languages l ON l.id=sq.language_id
                WHERE sq.id=%s AND l.script_code IN ({SCRIPT_PLACEHOLDERS})""",
            (quiz_id, *PUBLIC_SCRIPT_CODES),
        )
        quiz = cursor.fetchone()
        if quiz is None:
            raise HTTPException(status_code=404, detail="Section quiz was not found.")
        cursor.execute("SELECT id FROM users WHERE id=%s", (submission.user_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Learner was not found.")
        status = _quiz_status(cursor, quiz, submission.user_id)
        if not status["quiz_available"]:
            if not status["is_unlocked"]:
                raise HTTPException(status_code=403, detail="Complete the previous course section to unlock this quiz.")
            detail = (
                "Complete every Foundation lesson before taking the Foundation level quiz."
                if quiz["level"] == "foundation"
                else "Complete every lesson in this section before taking its quiz."
            )
            raise HTTPException(status_code=409, detail=detail)
        cursor.execute(
            """SELECT qq.id, qq.question_order, qq.prompt, qq.options_json,
                      qq.correct_option_index, ll.title AS source_lesson_title,
                      ll.explanation AS source_explanation,
                      ll.translation_text AS source_translation,
                      ll.pronunciation_text AS source_pronunciation
               FROM section_quiz_questions qq
               LEFT JOIN learning_lessons ll ON ll.id=qq.source_lesson_id
               WHERE qq.quiz_id=%s ORDER BY qq.question_order""",
            (quiz_id,),
        )
        questions = cursor.fetchall()
        submitted = {}
        for answer in submission.answers:
            if answer.question_id in submitted:
                raise HTTPException(status_code=422, detail="Each quiz question can be answered only once.")
            submitted[answer.question_id] = answer.selected_option_index
        valid_ids = {int(question["id"]) for question in questions}
        if len(questions) < 3 or set(submitted) != valid_ids:
            raise HTTPException(status_code=422, detail="Answer every question in this section quiz.")
        correct_count = 0
        answer_records = []
        review_records = []
        for question in questions:
            options = _json_value(question["options_json"])
            if not isinstance(options, list) or not options:
                raise HTTPException(status_code=409, detail="This quiz contains invalid answer options.")
            question_id = int(question["id"])
            selected = submitted[question_id]
            correct_index = int(question["correct_option_index"])
            if selected >= len(options):
                raise HTTPException(status_code=422, detail="A selected answer is invalid.")
            if correct_index < 0 or correct_index >= len(options):
                raise HTTPException(status_code=409, detail="This quiz contains an invalid answer key.")
            correct = selected == correct_index
            correct_count += int(correct)
            answer_records.append({
                "question_id": question_id,
                "selected_option_index": selected,
                "correct": correct,
            })
            teaching_notes = []
            if question.get("source_lesson_title"):
                teaching_notes.append(str(question["source_lesson_title"]))
            if question.get("source_explanation"):
                teaching_notes.append(str(question["source_explanation"]))
            if question.get("source_translation"):
                teaching_notes.append("Meaning: " + str(question["source_translation"]))
            if question.get("source_pronunciation"):
                teaching_notes.append("Pronunciation: " + str(question["source_pronunciation"]))
            review_records.append({
                "question_id": question_id,
                "question_order": int(question["question_order"]),
                "prompt": question["prompt"],
                "selected_option_index": selected,
                "selected_option": options[selected],
                "correct_option_index": correct_index,
                "correct_option": options[correct_index],
                "correct": correct,
                "teaching_notes": teaching_notes,
            })
        question_count = len(questions)
        score = round(correct_count * 100 / question_count, 2)
        passed = score >= float(quiz["pass_percentage"])
        can_advance = _has_developer_progress_bypass(submission.user_id) or (
            status["is_unlocked"] and status["lessons_complete"]
        )
        cursor.execute(
            """INSERT INTO section_quiz_attempts
               (quiz_id, user_id, score, correct_count, question_count, passed, answers_json)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (quiz_id, submission.user_id, score, correct_count, question_count, passed, json.dumps(answer_records)),
        )
        attempt_id = cursor.lastrowid
        connection.commit()
        return {
            "attempt_id": attempt_id,
            "score": score,
            "correct_count": correct_count,
            "question_count": question_count,
            "pass_percentage": float(quiz["pass_percentage"]),
            "passed": passed,
            "feedback": (
                "Section passed. The next course section is now unlocked."
                if can_advance else "Quiz passed. Complete the normal lesson prerequisites to unlock the next section."
            ) if passed else "Review the answers below, revisit the lessons, and try this quiz again.",
            "answers": review_records,
        }
    except HTTPException:
        if connection:
            connection.rollback()
        raise
    except Error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="Could not save the quiz attempt.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
