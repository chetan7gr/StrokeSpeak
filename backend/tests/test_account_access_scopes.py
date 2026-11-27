import json
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app import quiz_api
from app.quiz_api import QuizAnswer, QuizAttemptSubmission
from app.security import (
    get_current_admin_user_id,
    has_demo_quiz_access,
    is_admin_user_id,
    is_developer_user_id,
    require_user_scope,
)


class FakeCursor:
    def __init__(self):
        self.one = None
        self.rows = []

    def execute(self, query, params=None):
        normalized = " ".join(query.split())
        if "FROM section_quizzes sq JOIN languages l" in normalized and "WHERE sq.id=%s" in normalized:
            self.one = {"id": 901, "language_id": 7, "level": "beginner", "unit_number": 1, "pass_percentage": 70}
        elif normalized.startswith("SELECT id FROM users"):
            self.one = {"id": 12}
        elif "FROM section_quiz_attempts WHERE quiz_id=%s AND user_id=%s ORDER BY created_at" in normalized:
            self.rows = []
        elif "FROM section_quiz_attempts WHERE quiz_id=%s AND user_id=%s" in normalized:
            self.one = {"attempt_count": 0, "best_score": None, "passed": 0}
        elif "FROM section_quiz_questions qq" in normalized:
            self.rows = [
                {"id": 1, "question_order": 1, "prompt": "Choose the correct character", "options_json": json.dumps(["あ", "い", "う", "え"]), "correct_option_index": 0, "source_lesson_title": None, "source_explanation": None, "source_translation": None, "source_pronunciation": None},
                {"id": 2, "question_order": 2, "prompt": "Choose the matching sound", "options_json": json.dumps(["a", "i", "u", "e"]), "correct_option_index": 1, "source_lesson_title": None, "source_explanation": None, "source_translation": None, "source_pronunciation": None},
                {"id": 3, "question_order": 3, "prompt": "Select the correct answer", "options_json": json.dumps(["one", "two", "three", "four"]), "correct_option_index": 2, "source_lesson_title": None, "source_explanation": None, "source_translation": None, "source_pronunciation": None},
            ]
        elif "FROM section_quiz_questions WHERE quiz_id=%s ORDER BY question_order" in normalized:
            self.rows = [
                {"id": 1, "question_order": 1, "prompt": "Choose the correct character", "options_json": json.dumps(["あ", "い", "う", "え"])},
                {"id": 2, "question_order": 2, "prompt": "Choose the matching sound", "options_json": json.dumps(["a", "i", "u", "e"])},
                {"id": 3, "question_order": 3, "prompt": "Select the correct answer", "options_json": json.dumps(["one", "two", "three", "four"])},
            ]
        elif normalized.startswith("INSERT INTO section_quiz_attempts"):
            self.lastrowid = 77
        else:
            raise AssertionError(f"Unexpected query in read-only access test: {normalized}")

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConnection:
    def cursor(self, dictionary=False):
        return FakeCursor()

    def commit(self):
        pass

    def rollback(self):
        pass

    def is_connected(self):
        return True

    def close(self):
        pass


class AccountAccessScopeTests(unittest.TestCase):
    def permission_env(self):
        return patch.dict(os.environ, {
            "STROKESPEAK_ADMIN_USER_IDS": "6",
            "STROKESPEAK_DEVELOPER_USER_IDS": "6",
            "STROKESPEAK_DEMO_QUIZ_ACCESS_USER_IDS": "12",
        })

    def test_permission_allowlists_are_exact(self):
        with self.permission_env():
            self.assertTrue(is_admin_user_id(6))
            self.assertTrue(is_developer_user_id(6))
            self.assertTrue(has_demo_quiz_access(12))
            self.assertFalse(is_admin_user_id(12))
            self.assertFalse(is_developer_user_id(12))
            self.assertFalse(has_demo_quiz_access(6))
            self.assertFalse(is_developer_user_id(7))
            self.assertFalse(has_demo_quiz_access(13))

    def test_old_global_bypass_flag_does_not_authorize_other_accounts(self):
        with self.permission_env(), patch.dict(os.environ, {"STROKESPEAK_DEVELOPER_BYPASS": "true"}):
            self.assertTrue(quiz_api._has_developer_progress_bypass(6))
            self.assertFalse(quiz_api._has_developer_progress_bypass(7))
            self.assertFalse(quiz_api._has_developer_progress_bypass(12))
            self.assertFalse(quiz_api._has_developer_progress_bypass(99))

    def test_demo_quiz_access_does_not_unlock_lessons_or_chapters(self):
        with self.permission_env(), patch.object(quiz_api, "_level_progress", return_value=(5, 0, False)), patch.object(quiz_api, "_section_complete", return_value=(3, 0, False)), patch.object(quiz_api, "_section_unlocked", return_value=False):
            cursor = FakeCursor()
            quiz = {"id": 901, "language_id": 7, "level": "beginner", "unit_number": 1, "pass_percentage": 70}
            demo_status = quiz_api._quiz_status(cursor, quiz, 12)
            ordinary_status = quiz_api._quiz_status(cursor, quiz, 14)
            self.assertTrue(demo_status["quiz_available"])
            self.assertFalse(demo_status["is_unlocked"])
            self.assertTrue(demo_status["demo_quiz_access"])
            self.assertFalse(demo_status["lessons_complete"])
            self.assertFalse(ordinary_status["quiz_available"])
            self.assertFalse(ordinary_status["demo_quiz_access"])
            self.assertTrue(quiz_api._has_foundation_quiz_early_access({"level": "foundation"}, 13))
            self.assertFalse(quiz_api._has_foundation_quiz_early_access({"level": "foundation"}, 12))

        class FirstUnitCursor:
            def execute(self, query, params=None):
                self.row = {"first_unit": 1}

            def fetchone(self):
                return self.row

        with self.permission_env(), patch.object(quiz_api, "_level_progress", return_value=(5, 0, False)):
            self.assertFalse(quiz_api._lesson_is_unlocked(FirstUnitCursor(), 12, 7, "beginner", 1))

    def test_demo_learner_quiz_payload_never_contains_answer_keys(self):
        with self.permission_env(), patch.object(quiz_api, "_section_complete", return_value=(3, 0, False)), patch.object(quiz_api, "_section_unlocked", return_value=False), patch.object(quiz_api, "get_db_connection", return_value=FakeConnection()):
            result = quiz_api.get_section_quiz(901, user_id=12, current_user_id=12)
            self.assertTrue(result["quiz"]["quiz_available"])
            self.assertEqual(len(result["questions"]), 3)
            self.assertTrue(all("correct_option_index" not in question for question in result["questions"]))
            self.assertTrue(all("correct_option" not in question for question in result["questions"]))
            with self.assertRaises(HTTPException) as denied:
                quiz_api.get_section_quiz(901, user_id=6, current_user_id=12)
            self.assertEqual(denied.exception.status_code, 403)

    def test_demo_learner_can_submit_manual_answers_with_normal_scoring(self):
        with self.permission_env(), patch.object(quiz_api, "_section_complete", return_value=(3, 0, False)), patch.object(quiz_api, "_section_unlocked", return_value=False), patch.object(quiz_api, "get_db_connection", return_value=FakeConnection()):
            submission = QuizAttemptSubmission(user_id=12, answers=[
                QuizAnswer(question_id=1, selected_option_index=0),
                QuizAnswer(question_id=2, selected_option_index=0),
                QuizAnswer(question_id=3, selected_option_index=2),
            ])
            result = quiz_api.submit_section_quiz(901, submission, current_user_id=12)
            self.assertEqual(result["score"], 66.67)
            self.assertEqual(result["correct_count"], 2)
            self.assertFalse(result["passed"])
            self.assertFalse(result["answers"][1]["correct"])
            self.assertEqual(result["answers"][1]["selected_option"], "a")

    def test_developer_preview_and_scope_authorization_are_server_enforced(self):
        with self.permission_env():
            self.assertEqual(get_current_admin_user_id(user_id=6), 6)
            with self.assertRaises(HTTPException) as denied:
                get_current_admin_user_id(user_id=12)
            self.assertEqual(denied.exception.status_code, 403)
            with self.assertRaises(HTTPException) as scope_denied:
                require_user_scope(12, 6)
            self.assertEqual(scope_denied.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
