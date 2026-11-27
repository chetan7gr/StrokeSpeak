from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from stage_external_stroke_candidates import load_capture_candidate

ALLOWED = {("sa-devanagari", "आ"), ("ta", "ஆ")}
ROW = {"id": 217, "script_code": "sa-devanagari", "character_text": "आ"}


def payload():
    return {
        "schema_version": 1,
        "capture_id": "unit-test-capture-1",
        "captured_at_utc": "2026-11-25T10:00:00.000Z",
        "character_id": 217,
        "script_code": "sa-devanagari",
        "character": "आ",
        "candidate_status": "captured_pending_review",
        "stroke_count": 1,
        "point_count": 3,
        "points": [[
            {"x": 0.2, "y": 0.2, "time": 0},
            {"x": 0.5, "y": 0.5, "time": 80},
            {"x": 0.8, "y": 0.8, "time": 160},
        ]],
        "source": {
            "title": "Sample instructor reference",
            "url": "https://example.org/reference",
            "attribution": "Example instructor",
            "license": "Permission documented",
            "license_url": "",
        },
        "captured_by": "Developer",
        "instructor_review": {"status": "pending", "notes": ""},
        "svg": {"strokes": [{"d": "this is ignored and rebuilt"}]},
    }


class CaptureInboxTests(unittest.TestCase):
    def load(self, data, allowed=ALLOWED, row=ROW):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return load_capture_candidate(path, row, allowed)

    def test_valid_capture_rebuilds_svg_from_point_geometry(self):
        candidate = self.load(payload())
        self.assertEqual(candidate["candidate_status"], "captured_pending_review")
        self.assertEqual(candidate["instructor_review"]["status"], "pending")
        self.assertEqual(candidate["stroke_count"], 1)
        self.assertEqual(candidate["svg"]["strokes"][0]["d"], "M 20.00 20.00 L 50.00 50.00 L 80.00 80.00")
        self.assertEqual(candidate["capture_file_sha256"].__len__(), 64)

    def test_only_a_blocked_character_is_accepted(self):
        item = payload()
        item["character"] = "अ"
        with self.assertRaisesRegex(ValueError, "16 source-blocked"):
            self.load(item)

    def test_database_id_must_match_selected_character(self):
        item = payload()
        item["character_id"] = 999
        with self.assertRaisesRegex(ValueError, "ID"):
            self.load(item)

    def test_approved_status_cannot_enter_through_capture_inbox(self):
        item = payload()
        item["instructor_review"]["status"] = "approved"
        with self.assertRaisesRegex(ValueError, "review must remain pending"):
            self.load(item)

    def test_source_attribution_is_required(self):
        item = payload()
        item["source"]["attribution"] = " "
        with self.assertRaisesRegex(ValueError, "attribution"):
            self.load(item)

    def test_bad_timestamps_and_out_of_range_points_are_rejected(self):
        item = payload()
        item["points"][0][2]["time"] = 20
        with self.assertRaisesRegex(ValueError, "increasing"):
            self.load(item)
        item = payload()
        item["points"][0][1]["x"] = 1.1
        with self.assertRaisesRegex(ValueError, "normalized"):
            self.load(item)


if __name__ == "__main__":
    unittest.main(verbosity=2)