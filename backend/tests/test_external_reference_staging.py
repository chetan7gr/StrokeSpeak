from __future__ import annotations

import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

import stage_external_stroke_candidates as stage
import import_hanzi_writer_reference_strokes as hanzi
import import_lipi_devanagari_reference_strokes as lipi


class ExternalReferenceStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classes = stage.get_classes()

    def assert_candidate_geometry(self, candidate):
        points = candidate["points"]
        svg_strokes = candidate["svg"]["strokes"]
        self.assertEqual(len(points), len(svg_strokes))
        self.assertEqual(candidate["stroke_count"], len(points))
        for index, (stroke, svg) in enumerate(zip(points, svg_strokes), start=1):
            self.assertGreaterEqual(len(stroke), 2)
            self.assertEqual(svg["order"], index)
            expected = "M " + " L ".join(
                f"{point['x'] * 100:.2f} {point['y'] * 100:.2f}"
                for point in stroke
            )
            self.assertEqual(svg["d"], expected)
            for point in stroke:
                self.assertGreaterEqual(point["x"], 0.0)
                self.assertLessEqual(point["x"], 1.0)
                self.assertGreaterEqual(point["y"], 0.0)
                self.assertLessEqual(point["y"], 1.0)

    def test_fude_kana_pin_covers_all_ten_hiragana_classes(self):
        chars = self.classes["ja-hiragana"]
        self.assertEqual(len(chars), 10)
        for char in chars:
            candidate = stage.load_fude_candidate(char, None)
            self.assertEqual(candidate["character"], char)
            self.assertEqual(candidate["candidate_status"], "source_pinned_unreviewed")
            self.assert_candidate_geometry(candidate)

    def test_lipi_direct_hand_drawn_glyphs_cover_five_trained_vowels(self):
        digest, keys, points, stroke_starts, glyph_starts = lipi.read_safetensors(lipi.WEIGHTS)
        glyphs = {
            item[0]: index
            for index, item in enumerate(keys)
            if isinstance(item, list) and len(item) == 2 and item[1] == "glyph"
        }
        chars = [char for char in self.classes["sa-devanagari"] if char in lipi.TARGETS]
        self.assertEqual(len(chars), 5)
        for char in chars:
            point_data, metadata = lipi.convert_glyph(
                char, glyphs[char], points, stroke_starts, glyph_starts, digest
            )
            candidate = stage.source_candidate(
                "sa-devanagari", char, point_data, metadata, None, "Lipi direct glyph"
            )
            self.assert_candidate_geometry(candidate)

    def test_hanzi_writer_source_covers_all_nine_trained_chinese_classes(self):
        chars = [char for char in self.classes["zh-hans"] if char in hanzi.TARGETS]
        self.assertEqual(len(chars), 9)
        for char in chars:
            point_data, metadata = hanzi._load_and_convert(char)
            candidate = stage.source_candidate(
                "zh-hans", char, point_data, metadata, None, "Hanzi Writer Data 2.0.1"
            )
            self.assert_candidate_geometry(candidate)

    def test_model_scope_is_exactly_41_across_four_requested_groups(self):
        self.assertEqual(
            {key: len(value) for key, value in self.classes.items()},
            {"ja-hiragana": 10, "sa-devanagari": 10, "ta": 12, "zh-hans": 9},
        )
        self.assertEqual(sum(map(len, self.classes.values())), 41)


if __name__ == "__main__":
    unittest.main(verbosity=2)