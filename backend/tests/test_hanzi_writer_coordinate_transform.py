import json
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from scripts.import_hanzi_writer_reference_strokes import DATA_DIR, TARGET_IDS, _load_and_convert


class HanziWriterYDownTransformTests(unittest.TestCase):
    def test_all_nine_sources_preserve_order_and_transform_y_once(self):
        for character in TARGET_IDS:
            with self.subTest(character=character):
                source = json.loads((DATA_DIR / f"{character}.json").read_text(encoding="utf-8"))
                points, metadata = _load_and_convert(character)
                self.assertEqual(len(points), len(source["medians"]))
                all_points = [p for stroke in source["medians"] for p in stroke]
                min_x, max_x = min(p[0] for p in all_points), max(p[0] for p in all_points)
                min_y, max_y = min(p[1] for p in all_points), max(p[1] for p in all_points)
                scale = 0.76 / max(max_x - min_x, max_y - min_y)
                center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
                for index, (actual, median) in enumerate(zip(points, source["medians"])):
                    self.assertEqual(len(actual), len(median))
                    for point_index, (result, (x, y)) in enumerate(zip(actual, median)):
                        self.assertEqual(result["time"], point_index * 50)
                        self.assertAlmostEqual(result["x"], round(0.5 + (x - center_x) * scale, 6), places=6)
                        self.assertAlmostEqual(result["y"], round(0.5 - (y - center_y) * scale, 6), places=6)
                    path = metadata["strokes"][index]["d"]
                    svg_coords = [tuple(map(float, item.split())) for item in path[2:].split(" L ")]
                    for result, (sx, sy) in zip(actual, svg_coords):
                        self.assertAlmostEqual(result["x"], sx / 100, places=6)
                        self.assertAlmostEqual(result["y"], sy / 100, places=6)
                self.assertEqual(metadata["instructional_review_status"], "pending")
                self.assertNotIn("reviewed_reference_sha256", metadata)
                self.assertIn("invert source Y-up once", metadata["coordinate_transform"])

    def test_three_is_top_to_bottom_in_source_stroke_order(self):
        points, _ = _load_and_convert("三")
        means = [sum(p["y"] for p in stroke) / len(stroke) for stroke in points]
        self.assertLess(means[0], means[1])
        self.assertLess(means[1], means[2])

    def test_two_is_short_upper_then_long_lower(self):
        points, _ = _load_and_convert("二")
        widths = [max(p["x"] for p in stroke) - min(p["x"] for p in stroke) for stroke in points]
        means_y = [sum(p["y"] for p in stroke) / len(stroke) for stroke in points]
        self.assertEqual(len(points), 2)
        self.assertLess(widths[0], widths[1])
        self.assertLess(means_y[0], means_y[1])
        self.assertLess(points[0][0]["x"], points[0][-1]["x"])
        self.assertLess(points[1][0]["x"], points[1][-1]["x"])

    def test_people_and_big_directions_and_idempotence(self):
        ren, _ = _load_and_convert("人")
        self.assertGreater(ren[0][0]["x"], ren[0][-1]["x"])
        self.assertLess(ren[0][0]["y"], ren[0][-1]["y"])
        self.assertLess(ren[1][0]["x"], ren[1][-1]["x"])
        self.assertLess(ren[1][0]["y"], ren[1][-1]["y"])
        da1, _ = _load_and_convert("大")
        da2, _ = _load_and_convert("大")
        self.assertEqual(da1, da2)
        self.assertLess(da1[0][0]["x"], da1[0][-1]["x"])
        self.assertLess(da1[1][0]["y"], da1[1][-1]["y"])
        self.assertLess(da1[2][0]["y"], da1[2][-1]["y"])


if __name__ == "__main__":
    unittest.main()