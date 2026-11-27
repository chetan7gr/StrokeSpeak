"""Read-only audit of all StrokeSpeak tutorial video DB mappings and MP4 files."""

import hashlib
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.ml.video_generator import LESSON_VIDEO_CONFIGS
from main import get_db_connection


def main():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT ll.id, ll.language_id, l.script_code, ll.title, ll.content_text,
               ll.tutorial_video_url, ll.tutorial_video_status
        FROM learning_lessons ll
        JOIN languages l ON l.id = ll.language_id
        WHERE ll.tutorial_video_url IS NOT NULL
           OR ll.id IN (55,61,62,63,64,65,223,227,339,341,343,348,349,350,351,352,383,384,385,386)
        ORDER BY l.script_code, ll.id
        """
    )
    rows = cur.fetchall()
    conn.close()

    print(f"=== DB LESSONS WITH VIDEO URLS OR CONFIGS ({len(rows)}) ===")
    url_counts = {}
    for r in rows:
        u = r["tutorial_video_url"]
        if u:
            url_counts[u] = url_counts.get(u, 0) + 1
        print(
            f"ID {r['id']:3d} | {r['script_code']:13s} | text={str(r['content_text'])[:6]:6s} | "
            f"status={r['tutorial_video_status']:11s} | url={u} | {r['title'][:42]}"
        )

    print("\n=== DUPLICATE URLS IN DB ===")
    dups = {k: v for k, v in url_counts.items() if v > 1}
    print(dups if dups else "None")

    print("\n=== FILES IN backend/static/videos ===")
    hashes = {}
    videos_dir = BACKEND / "static" / "videos"
    for p in sorted(videos_dir.glob("*")):
        if not p.is_file():
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
        hashes.setdefault(h, []).append(p.name)
        print(f"{p.name:58s} | {p.stat().st_size / 1024:7.1f} KB | sha={h}")

    print("\n=== IDENTICAL FILE HASHES (REPEATED VIDEO FILES) ===")
    any_dup = False
    for h, names in hashes.items():
        if len(names) > 1:
            any_dup = True
            print(f"{h} -> {names}")
    if not any_dup:
        print("None")

    print("\n=== CONFIGURED 20 FOUNDATION VIDEO TARGETS ===")
    for (lid, cid), cfg in sorted(LESSON_VIDEO_CONFIGS.items()):
        fname = cfg.get("default_filename")
        fpath = videos_dir / fname
        exists = fpath.is_file()
        held = (videos_dir / (fname + ".y_axis_hold")).is_file()
        print(f"Lesson {lid:3d} (char {cid:3d}) -> {fname:48s} | exists={exists} | y_axis_hold={held}")


if __name__ == "__main__":
    main()
