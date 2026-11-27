"""Read-only regression checks for the developer quiz preview API."""
from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env", override=True)

from fastapi.testclient import TestClient
from app.db.database import get_db_connection
from app.security import create_access_token
from main import app


class AdminQuizPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # These signed test identities are isolated to this process; they are
        # authorized only inside patch.dict blocks and are never stored in .env.
        cls.admin_id = 987654321
        cls.non_admin_id = 987654322
        cls.admin_headers = {"Authorization": f"Bearer {create_access_token(cls.admin_id)}"}
        cls.non_admin_headers = {"Authorization": f"Bearer {create_access_token(cls.non_admin_id)}"}
        cls.client = TestClient(app)

    @staticmethod
    def database_counts():
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            counts = {}
            for table in ("section_quiz_attempts", "lesson_progress"):
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = int(cursor.fetchone()[0])
            return counts
        finally:
            cursor.close()
            connection.close()

    def test_admin_list_and_all_previews_are_read_only(self):
        before = self.database_counts()
        with patch.dict(os.environ, {"STROKESPEAK_ADMIN_USER_IDS": str(self.admin_id)}):
            response = self.client.get("/api/v1/admin/section-quizzes", headers=self.admin_headers)
            self.assertEqual(response.status_code, 200, response.text)
            quizzes = response.json()["quizzes"]
            self.assertTrue(quizzes)
            self.assertEqual({q["language_name"] for q in quizzes}, {"Japanese", "Sanskrit", "Tamil", "Chinese"})

            question_total = 0
            for quiz in quizzes:
                preview_response = self.client.get(
                    f"/api/v1/admin/section-quizzes/{quiz['id']}/preview",
                    headers=self.admin_headers,
                )
                self.assertEqual(preview_response.status_code, 200, preview_response.text)
                data = preview_response.json()
                self.assertTrue(data["preview_only"])
                self.assertFalse(data["learner_progress_changed"])
                self.assertNotIn("attempt_id", data)
                self.assertNotIn("history", data)
                self.assertTrue(data["questions"])
                self.assertEqual(len(data["questions"]), int(quiz["question_count"]))
                for question in data["questions"]:
                    question_total += 1
                    correct_index = int(question["correct_option_index"])
                    self.assertEqual(question["correct_option"], question["options"][correct_index])
                    self.assertTrue(question["explanation"].strip())
            self.assertEqual(question_total, 48)
        self.assertEqual(self.database_counts(), before)

    def test_admin_preview_requires_administrator(self):
        self.assertEqual(self.client.get("/api/v1/admin/section-quizzes").status_code, 401)
        with patch.dict(os.environ, {"STROKESPEAK_ADMIN_USER_IDS": str(self.admin_id)}):
            denied = self.client.get(
                "/api/v1/admin/section-quizzes",
                headers=self.non_admin_headers,
            )
        self.assertEqual(denied.status_code, 403, denied.text)

    def test_existing_learner_quiz_gate_still_blocks_unready_quiz(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id FROM users ORDER BY id"
            )
            learner = next(
                (row for row in cursor.fetchall() if int(row["id"]) not in {
                    int(value.strip()) for value in os.getenv("STROKESPEAK_ADMIN_USER_IDS", "").split(",")
                    if value.strip().isdigit()
                }),
                None,
            )
        finally:
            cursor.close()
            connection.close()
        if learner is None:
            self.skipTest("No existing non-admin account is available for a read-only gate check.")

        learner_id = int(learner["id"])
        user_headers = {"Authorization": f"Bearer {create_access_token(learner_id)}"}
        with patch.dict(os.environ, {"STROKESPEAK_ADMIN_USER_IDS": str(self.admin_id)}):
            available = self.client.get(
                f"/api/v1/section-quizzes?language_id=5&user_id={learner_id}",
                headers=user_headers,
            )
            self.assertEqual(available.status_code, 200, available.text)
            locked = next((quiz for quiz in available.json()["quizzes"] if not quiz["quiz_available"]), None)
            if locked is None:
                self.skipTest("This existing account has no currently locked quiz to test.")
            blocked = self.client.get(
                f"/api/v1/section-quizzes/{locked['id']}?user_id={learner_id}",
                headers=user_headers,
            )
        self.assertIn(blocked.status_code, (403, 409), blocked.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
