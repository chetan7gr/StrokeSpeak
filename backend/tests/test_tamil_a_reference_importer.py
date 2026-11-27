from __future__ import annotations
import hashlib, json, re, sys, unittest
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BACKEND))
sys.path.insert(0,str(BACKEND/"scripts"))
from correct_tamil_reference_strokes import EXPECTED_SOURCE_SHA256,REFERENCE_FILE,SOURCE_FILE,build_reference
from main import _prototype_scores

class TamilAReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(REFERENCE_FILE.read_text(encoding="utf-8"))
        cls.points,cls.metadata,cls.summary=build_reference(cls.config)
    def test_pinned_source_and_target(self):
        self.assertEqual(hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest().upper(),EXPECTED_SOURCE_SHA256)
        self.assertEqual((self.config["character_id"],self.config["character"],self.config["script_code"]),(25,"\u0B85","ta"))
    def test_four_ordered_strokes_pending_instructor_review(self):
        self.assertEqual(self.summary["stroke_count"],4)
        self.assertEqual([s["order"] for s in self.metadata["strokes"]],[1,2,3,4])
        self.assertEqual(self.metadata["instructional_review_status"],"pending")
        self.assertTrue(self.metadata["watermark_align_to_reference"])
    def test_svg_paths_are_derived_from_point_strokes(self):
        for points,path in zip(self.points,self.metadata["strokes"]):
            values=[float(v) for v in re.findall(r"[-+]?(?:\d*\.)?\d+",path["d"])]
            self.assertEqual(len(values),2*len(points))
            for i,p in enumerate(points):
                self.assertAlmostEqual(values[2*i],p["x"],places=3)
                self.assertAlmostEqual(values[2*i+1],p["y"],places=3)
    def test_aspect_ratio_and_viewbox_bounds(self):
        pts=[p for s in self.points for p in s]
        width=max(p["x"] for p in pts)-min(p["x"] for p in pts)
        height=max(p["y"] for p in pts)-min(p["y"] for p in pts)
        self.assertAlmostEqual(width/height,self.summary["source_aspect_ratio"],places=4)
        self.assertGreaterEqual(min(p["x"] for p in pts),0)
        self.assertGreaterEqual(min(p["y"] for p in pts),0)
        self.assertLessEqual(max(p["x"] for p in pts),100)
        self.assertLessEqual(max(p["y"] for p in pts),100)
    def test_self_reference_scores_without_creating_attempt(self):
        shape,order,too_small=_prototype_scores(self.points,self.points)
        self.assertEqual((shape,order,too_small),(100.0,100.0,False))

if __name__=="__main__":
    unittest.main(verbosity=2)
