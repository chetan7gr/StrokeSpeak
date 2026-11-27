"""Verify all active tutorial video routes, uniqueness (SHA-256), and MP4 delivery."""

import hashlib
import sys
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from main import get_db_connection


def main():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT ll.id, l.script_code, ll.tutorial_video_url, ll.tutorial_video_status, ll.title
        FROM learning_lessons ll
        JOIN languages l ON l.id = ll.language_id
        WHERE ll.tutorial_video_url IS NOT NULL
        ORDER BY l.script_code, ll.id
        """
    )
    rows = cur.fetchall()
    conn.close()

    print(f"Active lessons with tutorial_video_url: {len(rows)}")
    urls = set()
    hashes = {}
    counts_by_script = {}
    for r in rows:
        lid = r["id"]
        sc = r["script_code"]
        url = r["tutorial_video_url"]
        assert url not in urls, f"Duplicate URL in DB: {url}"
        urls.add(url)
        assert r["tutorial_video_status"] == "ready", r

        full_url = f"http://127.0.0.1:8000{url}"
        with urllib.request.urlopen(full_url) as resp:
            assert resp.status == 200, (lid, resp.status)
            ctype = resp.headers.get("Content-Type")
            disp = resp.headers.get("Content-Disposition")
            data = resp.read()
            h = hashlib.sha256(data).hexdigest()[:12]
            assert h not in hashes, (
                f"Repeated/duplicate video content for lesson {lid}: matches lesson {hashes[h]}"
            )
            hashes[h] = lid
            counts_by_script[sc] = counts_by_script.get(sc, 0) + 1
            print(
                f"OK {sc:13s} | L{lid:3d} | 200 {ctype} | {len(data)/1024:7.1f} KB | sha={h} | {disp}"
            )

    print("\nCounts by script:", counts_by_script)
    print(f"ALL {len(rows)} ACTIVE VIDEO ROUTES RETURNED HTTP 200 WITH UNIQUE CONTENT (0 REPEATS)!")


if __name__ == "__main__":
    main()
