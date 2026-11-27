"""Generate one safe tutorial demo for each missing public script group."""
import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.db.database import get_db_connection
from app.reference_paths import reference_path_fingerprint
from app.ml.script_demo_video import VIDEOS_DIR, generate_script_demo_video

TARGETS = [
    ("sa-devanagari", "अ"),
    ("ta", "அ"),
    ("zh-hans", "一"),
]


def load_candidate(script_code, character_text):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT ll.id AS lesson_id, ll.title, ll.tutorial_video_status,
                   ll.tutorial_video_url, c.id AS character_id, c.character_text,
                   c.pronunciation_text, c.reference_strokes AS stroke_data,
                   c.reference_strokes_svg AS reference_metadata,
                   l.script_code, l.name AS language_name
            FROM learning_lessons ll
            JOIN languages l ON l.id = ll.language_id
            JOIN characters c ON c.language_id = l.id AND c.character_text = ll.content_text
            WHERE l.script_code = %s AND c.character_text = %s
              AND ll.category = 'character' AND ll.level = 'foundation'
            ORDER BY ll.lesson_order, ll.id
            LIMIT 1
        """, (script_code, character_text))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def verify_admin_token(api_token):
    request = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/auth/me",
        headers={"Authorization": f"Bearer {api_token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise SystemExit(
            f"Admin sign-in check failed (HTTP {error.code}). Sign in again and ensure this account is configured as an administrator."
        ) from error
    except urllib.error.URLError as error:
        raise SystemExit(f"Admin sign-in check could not reach the local API: {error.reason}") from error

    user = payload.get("user", {})
    if user.get("role") != "admin":
        raise SystemExit("No video generated: the signed-in account is not in STROKESPEAK_ADMIN_USER_IDS.")
    return int(user["id"])


def register_video(lesson_id, video_url, api_token):
    payload = json.dumps({"video_url": video_url, "status": "ready"}).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/lessons/{lesson_id}/tutorial-video",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="PUT",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="render files and register them with the local API")
    parser.add_argument("--validated-lesson-id", action="append", type=int, default=[], help="lesson ID whose reference provenance and genuine learner drawing have both been verified; repeat per target")
    args = parser.parse_args()

    candidates = []
    for script_code, character_text in TARGETS:
        lesson = load_candidate(script_code, character_text)
        if not lesson:
            raise SystemExit(f"Missing foundation lesson/reference for {script_code} {character_text}.")
        if isinstance(lesson["stroke_data"], str):
            lesson["stroke_data"] = json.loads(lesson["stroke_data"])
        metadata = lesson.get("reference_metadata")
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        code = " ".join(f"U+{ord(char):04X}" for char in character_text)
        if not isinstance(metadata, dict) or metadata.get("provenance_status") not in {"source_attributed", "verified"}:
            print(f"HOLD {script_code} {code} lesson {lesson['lesson_id']}: reference provenance is unverified")
            continue
        if metadata.get("instructional_review_status") != "approved":
            print(f"HOLD {script_code} {code} lesson {lesson['lesson_id']}: sourced paths need qualified instructional review")
            continue
        current_fingerprint = reference_path_fingerprint(lesson["stroke_data"], metadata)
        if metadata.get("reviewed_reference_sha256") != current_fingerprint:
            print(f"HOLD {script_code} {code} lesson {lesson['lesson_id']}: the reviewed reference geometry has changed")
            continue
        output = VIDEOS_DIR / f"strokespeak_demo_{script_code}_lesson{lesson['lesson_id']}.mp4"
        character_code = " ".join(f"U+{ord(char):04X}" for char in character_text)
        if lesson["tutorial_video_status"] == "ready" or lesson["tutorial_video_url"]:
            print(f"SKIP already linked: {script_code} {character_code} lesson {lesson['lesson_id']}")
            continue
        if any(VIDEOS_DIR.glob(f"*_lesson{lesson['lesson_id']}.mp4")):
            raise SystemExit(f"Refusing to overwrite/adopt an existing video for lesson {lesson['lesson_id']}.")
        lesson["_output"] = output
        candidates.append(lesson)
        print(f"READY {script_code}: {character_code} · lesson {lesson['lesson_id']} · {len(lesson['stroke_data'])} reference strokes")
        print(f"  output: {output}")

    if not args.apply:
        print("Dry run only. Apply requires verified reference provenance plus genuine learner drawing validation for each target.")
        return

    candidate_ids = {int(item["lesson_id"]) for item in candidates}
    if not args.validated_lesson_id:
        raise SystemExit("No video generated: pass --validated-lesson-id only after completing a genuine drawing validation for that lesson.")
    unknown_ids = set(args.validated_lesson_id) - candidate_ids
    if unknown_ids:
        raise SystemExit("These lesson IDs are not ungenerated public demo targets: " + ", ".join(map(str, sorted(unknown_ids))))
    selected = [item for item in candidates if int(item["lesson_id"]) in set(args.validated_lesson_id)]
    if selected:
        api_token = os.getenv("STROKESPEAK_ADMIN_TOKEN", "").strip()
        if not api_token:
            api_token = getpass.getpass("Paste the current administrator access token (input hidden): ").strip()
        if not api_token:
            raise SystemExit("No video generated: an administrator access token is required.")
        admin_id = verify_admin_token(api_token)
        print(f"Administrator session verified for account {admin_id}.")

    for lesson in selected:
        generated = generate_script_demo_video(lesson, lesson["_output"])
        print(f"GENERATED {generated['path']} ({generated['duration_seconds']}s, {generated['size_bytes']} bytes)")
        video_url = f"/api/v1/lessons/{lesson['lesson_id']}/video"
        try:
            result = register_video(lesson["lesson_id"], video_url, api_token)
        except (urllib.error.URLError, urllib.error.HTTPError) as error:
            print(f"VIDEO SAVED but API registration failed for lesson {lesson['lesson_id']}: {error}")
            raise
        print(f"REGISTERED: {result.get('status')} · lesson {lesson['lesson_id']}")


if __name__ == "__main__":
    main()