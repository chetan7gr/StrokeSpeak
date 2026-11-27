"""Overwrite-safety tests. The real video renderer is never invoked."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
from app.ml import video_generator
from scripts import generate_multilingual_videos


class VideoOverwriteSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="strokespeak-video-safety-")
        self.root = Path(self.temp_dir.name)
        self.target = self.root / "lesson.mp4"

    def tearDown(self):
        self.temp_dir.cleanup()

    @staticmethod
    def fake_render(lesson_id, character_id, output_path, overwrite):
        Path(output_path).write_bytes(b"valid staged video")

    def test_default_refuses_existing_file_before_render(self):
        self.target.write_bytes(b"original")
        with patch.object(video_generator, "_render_lesson_video") as renderer:
            with self.assertRaises(FileExistsError):
                video_generator.generate_lesson_video(output_path=str(self.target))
            renderer.assert_not_called()
        self.assertEqual(self.target.read_bytes(), b"original")

    def test_partial_render_failure_preserves_existing_file(self):
        self.target.write_bytes(b"original")
        def fail(lesson_id, character_id, output_path, overwrite):
            Path(output_path).write_bytes(b"partial")
            raise RuntimeError("encoder failed")
        with patch.object(video_generator, "_render_lesson_video", side_effect=fail):
            with self.assertRaisesRegex(RuntimeError, "encoder failed"):
                video_generator.generate_lesson_video(output_path=str(self.target), overwrite=True)
        self.assertEqual(self.target.read_bytes(), b"original")
        self.assertEqual(list(self.root.glob("*.tmp.mp4")), [])

    def test_invalid_render_preserves_existing_file(self):
        self.target.write_bytes(b"original")
        with patch.object(video_generator, "_render_lesson_video", side_effect=self.fake_render):
            with patch.object(video_generator, "_validate_rendered_video", side_effect=ValueError("bad MP4")):
                with self.assertRaisesRegex(ValueError, "bad MP4"):
                    video_generator.generate_lesson_video(output_path=str(self.target), overwrite=True)
        self.assertEqual(self.target.read_bytes(), b"original")

    def test_explicit_overwrite_publishes_after_validation(self):
        self.target.write_bytes(b"old")
        with patch.object(video_generator, "_render_lesson_video", side_effect=self.fake_render):
            with patch.object(video_generator, "_validate_rendered_video") as validator:
                video_generator.generate_lesson_video(output_path=str(self.target), overwrite=True)
        self.assertEqual(self.target.read_bytes(), b"valid staged video")
        validator.assert_called_once()

    def test_new_file_publishes_without_overwrite_flag(self):
        with patch.object(video_generator, "_render_lesson_video", side_effect=self.fake_render):
            with patch.object(video_generator, "_validate_rendered_video"):
                video_generator.generate_lesson_video(output_path=str(self.target))
        self.assertEqual(self.target.read_bytes(), b"valid staged video")

    def test_atomic_publish_refuses_existing_destination(self):
        staged = self.root / "staged.mp4"
        staged.write_bytes(b"staged")
        self.target.write_bytes(b"original")
        with self.assertRaises(OSError):
            video_generator.publish_video_safely(staged, self.target, overwrite=False)
        self.assertEqual(self.target.read_bytes(), b"original")

    def test_bulk_preflight_requires_opt_in_for_existing_targets(self):
        self.target.write_bytes(b"original")
        with self.assertRaises(FileExistsError):
            generate_multilingual_videos.preflight_outputs([self.target], overwrite=False)
        generate_multilingual_videos.preflight_outputs([self.target], overwrite=True)

    def test_copy_validation_failure_preserves_existing_target(self):
        source = self.root / "source.mp4"
        source.write_bytes(b"candidate")
        self.target.write_bytes(b"original")
        with patch.object(generate_multilingual_videos, "_validate_rendered_video", side_effect=ValueError("decode failed")):
            with self.assertRaisesRegex(ValueError, "decode failed"):
                generate_multilingual_videos.copy_video_safely(source, self.target, overwrite=True)
        self.assertEqual(self.target.read_bytes(), b"original")


if __name__ == "__main__":
    unittest.main(verbosity=2)
