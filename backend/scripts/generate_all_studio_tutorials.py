"""
Batch-generate StrokeSpeak tutorial videos using the unified circular Studio AI Teacher
(sensei_aoi_studio_v4.png) + Wav2Lip GAN + live MySQL reference strokes.

- Writes non-overwriting `*_studio-v4.mp4` assets via temp file + decode validation.
- Updates `learning_lessons.tutorial_video_url` to `?variant=studio-v4` after validation.
- Verifies unique SHA-256 hashes across all active tutorial videos (no repeated videos).
"""

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.ml.video_generator import (
    LESSON_VIDEO_CONFIGS,
    VIDEOS_DIR,
    _render_lesson_video,
    _validate_rendered_video,
)
from main import get_db_connection

# (lesson_id, character_id, script_code)
TARGETS = [
    # Japanese (62-65; 61 already uses Studio AI Teacher in female-lipsync-v5)
    (62, 28, "ja-hiragana"),
    (63, 29, "ja-hiragana"),
    (64, 30, "ja-hiragana"),
    (65, 3, "ja-hiragana"),
    # Sanskrit (3 original + 3 more = 6)
    (339, 216, "sa-devanagari"),
    (340, 217, "sa-devanagari"),
    (341, 218, "sa-devanagari"),
    (342, 219, "sa-devanagari"),
    (343, 220, "sa-devanagari"),
    (357, 221, "sa-devanagari"),
    # Tamil (55 unique overview + 223 updated + 3 more = 5)
    (55, 25, "ta"),
    (223, 25, "ta"),
    (224, 110, "ta"),
    (225, 111, "ta"),
    (227, 113, "ta"),
    # Chinese (9 foundation updated + 3 beginner phrases = 12)
    (348, 241, "zh-hans"),
    (349, 242, "zh-hans"),
    (350, 243, "zh-hans"),
    (351, 244, "zh-hans"),
    (352, 245, "zh-hans"),
    (383, 247, "zh-hans"),
    (384, 248, "zh-hans"),
    (385, 249, "zh-hans"),
    (386, 252, "zh-hans"),
    (387, 244, "zh-hans"),
    (388, 244, "zh-hans"),
    (389, 249, "zh-hans"),
]


def update_lesson_db(lesson_id: int, variant: str = "studio-v4") -> None:
    url = f"/api/v1/lessons/{lesson_id}/video?variant={variant}"
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE learning_lessons SET tutorial_video_url = %s, tutorial_video_status = 'ready' WHERE id = %s",
            (url, lesson_id),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scripts", nargs="*", default=None, help="Filter script codes")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing studio-v4 MP4s")
    args = parser.parse_args()

    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    selected = [t for t in TARGETS if not args.scripts or t[2] in args.scripts]
    print(f"Processing {len(selected)} Studio AI Teacher tutorial videos...")

    hashes = {}
    for idx, (lid, cid, sc) in enumerate(selected, 1):
        assert (lid, cid) in LESSON_VIDEO_CONFIGS, f"Missing config for {(lid, cid)}"
        prefix = "zh_hans" if sc == "zh-hans" else ("sa_devanagari" if sc == "sa-devanagari" else ("ta" if sc == "ta" else "ja_hiragana"))
        dest_path = VIDEOS_DIR / f"{prefix}_{cid}_lesson{lid}_studio-v4.mp4"

        if dest_path.is_file() and not args.overwrite:
            _validate_rendered_video(dest_path)
            update_lesson_db(lid, "studio-v4")
            h = hashlib.sha256(dest_path.read_bytes()).hexdigest()[:12]
            hashes[lid] = (dest_path.name, h)
            print(f"[{idx}/{len(selected)}] Reused valid {dest_path.name} (sha={h})")
            continue

        fd, tmp_name = tempfile.mkstemp(prefix=f"studio_l{lid}_", suffix=".tmp.mp4", dir=str(VIDEOS_DIR))
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            _render_lesson_video(lid, cid, output_path=str(tmp_path), overwrite=True)
            _validate_rendered_video(tmp_path)
            os.replace(tmp_path, dest_path)
            update_lesson_db(lid, "studio-v4")
            h = hashlib.sha256(dest_path.read_bytes()).hexdigest()[:12]
            hashes[lid] = (dest_path.name, h)
            print(f"[{idx}/{len(selected)}] Generated & DB-linked {dest_path.name} (sha={h})")
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    # Verify zero duplicate SHA-256 hashes among generated targets
    seen = {}
    for lid, (name, h) in hashes.items():
        if h in seen:
            raise RuntimeError(f"Duplicate video hash {h}: lesson {lid} ({name}) == lesson {seen[h]}")
        seen[h] = f"{lid} ({name})"
    print(f"Batch complete: {len(hashes)} unique studio-v4 videos verified.")


if __name__ == "__main__":
    main()
