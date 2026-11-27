"""Import source-pinned Hanzi Writer paths into StrokeSpeak's Y-down canvas coordinates.

Default mode is read-only. Pass --apply to apply all checksum-verified Chinese targets.
Every apply writes an exact, timestamped before-image and verifies the transaction
before commit. Instructor-review metadata is never fabricated or carried across
changed geometry.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
from app.db.database import get_db_connection
from app.reference_paths import reference_path_fingerprint

DATA_DIR = BACKEND_DIR / "data" / "reference_strokes" / "hanzi-writer-data-2.0.1"
BACKUP_DIR = BACKEND_DIR / "data" / "reference_strokes" / "backups"
EXPECTED_VERSION = "2.0.1"
SCRIPT_CODE = "zh-hans"
TARGET_IDS = {
    "一": 241,
    "二": 242,
    "三": 243,
    "人": 244,
    "大": 245,
    "口": 247,
    "日": 248,
    "月": 249,
    "山": 252,
}
TARGETS = tuple(TARGET_IDS)
SOURCE_REPOSITORY = "https://github.com/chanind/hanzi-writer-data"
SOURCE_PACKAGE = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0.1/"
SOURCE_LICENSE = "Arphic Public License (APL); see vendored ARPHICPL.TXT"
VIEWBOX = "0 0 100 100"


def _decode(value):
    return json.loads(value) if isinstance(value, str) else value


def _canonical(value) -> str:
    return json.dumps(_decode(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load_and_convert(character: str) -> tuple[list[list[dict]], dict]:
    """Convert source medians once from source Y-up to canvas/SVG Y-down.

    Source stroke order and point order are preserved verbatim. x is scaled as
    before; y is inverted exactly once for browser SVG/canvas coordinates.
    """
    if character not in TARGET_IDS:
        raise ValueError(f"Unsupported pinned Chinese target: {character!r}")
    path = DATA_DIR / f"{character}.json"
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes.decode("utf-8"))
    medians = raw.get("medians")
    if not isinstance(medians, list) or not medians or any(not isinstance(stroke, list) or len(stroke) < 2 for stroke in medians):
        raise ValueError(f"Missing valid ordered medians for {character} in {path}")

    points = []
    for stroke in medians:
        for point in stroke:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                raise ValueError(f"Malformed source point for {character}: {point!r}")
            x, y = float(point[0]), float(point[1])
            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError(f"Non-finite source point for {character}: {point!r}")
            points.append((x, y))

    min_x = min(x for x, _ in points)
    max_x = max(x for x, _ in points)
    min_y = min(y for _, y in points)
    max_y = max(y for _, y in points)
    extent = max(max_x - min_x, max_y - min_y)
    if extent <= 0:
        raise ValueError(f"Degenerate source geometry for {character}")
    scale = 0.76 / extent
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0

    converted: list[list[dict]] = []
    svg_strokes: list[dict] = []
    for stroke_index, median in enumerate(medians, start=1):
        stroke_points: list[dict] = []
        for point_index, (x, y) in enumerate(median):
            nx = round(0.5 + (float(x) - center_x) * scale, 6)
            ny = round(0.5 - (float(y) - center_y) * scale, 6)
            stroke_points.append({"x": nx, "y": ny, "time": point_index * 50})
        path_d = "M " + " L ".join(
            f"{point['x'] * 100.0:.6f} {point['y'] * 100.0:.6f}" for point in stroke_points
        )
        converted.append(stroke_points)
        svg_strokes.append({"order": stroke_index, "path_id": f"s{stroke_index}", "d": path_d})

    source_sha = hashlib.sha256(raw_bytes).hexdigest()
    metadata = {
        "source": "hanzi-writer-data 2.0.1 (Make Me a Hanzi; Arphic Technology font-derived data)",
        "source_url": SOURCE_REPOSITORY,
        "source_file_url": SOURCE_PACKAGE + f"{character}.json",
        "source_version": EXPECTED_VERSION,
        "video_credit": "Hanzi Writer Data 2.0.1 · Arphic Public License",
        "source_file": f"{character}.json · SHA-256 {source_sha}",
        "license": SOURCE_LICENSE,
        "license_url": SOURCE_REPOSITORY + "/blob/master/ARPHICPL.TXT",
        "source_coordinates": "Hanzi Writer ordered median coordinates, 1024x1024, Y-up",
        "coordinate_transform": (
            "Centered per-character bounds; aspect-preserving scale to 0.12–0.88; "
            "invert source Y-up once into SVG/canvas Y-down. Preserve source stroke and point order."
        ),
        "timing_model": "Uniform 50 ms intervals assigned for StrokeSpeak playback; not present in source data",
        "provenance_status": "source_attributed",
        "instructional_review_status": "pending",
        "character": character,
        "script_code": SCRIPT_CODE,
        "viewBox": VIEWBOX,
        "stroke_count": len(converted),
        "strokes": svg_strokes,
    }
    metadata["reference_path_sha256"] = reference_path_fingerprint(converted, metadata)
    return converted, metadata


def _preserve_valid_review(candidate_points, candidate_meta, old_points, old_meta):
    """Keep an existing valid review only when the reviewed geometry is unchanged."""
    old_meta = copy.deepcopy(old_meta or {})
    old_fp = reference_path_fingerprint(old_points or [], old_meta)
    candidate_fp = reference_path_fingerprint(candidate_points, candidate_meta)
    if (
        old_meta.get("instructional_review_status") == "approved"
        and old_meta.get("reviewed_reference_sha256") == old_fp
        and old_fp == candidate_fp
    ):
        for key in ("instructional_review_status", "reviewed_reference_sha256", "instructional_review_history", "latest_review"):
            if key in old_meta:
                candidate_meta[key] = old_meta[key]
    elif isinstance(old_meta.get("instructional_review_history"), list):
        candidate_meta["instructional_review_history"] = old_meta["instructional_review_history"]
    candidate_meta["reference_path_sha256"] = candidate_fp
    return candidate_meta


def _load_verified_package() -> dict[str, tuple[list[list[dict]], dict]]:
    package = json.loads((DATA_DIR / "package.json").read_text(encoding="utf-8"))
    if package.get("version") != EXPECTED_VERSION:
        raise RuntimeError(f"Expected package {EXPECTED_VERSION}; found {package.get('version')!r}.")
    if package.get("license") != "SEE LICENSE IN ARPHICPL.TXT":
        raise RuntimeError("Unexpected package license declaration; refusing import.")
    if not (DATA_DIR / "ARPHICPL.TXT").is_file():
        raise RuntimeError("The vendored package license file is missing.")
    return {character: _load_and_convert(character) for character in TARGETS}


def import_references(apply: bool = False) -> dict:
    """Dry-run by default; --apply transactionally updates only the nine pinned Chinese IDs."""
    candidates = _load_verified_package()
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        connection.start_transaction()
        placeholders = ",".join(["%s"] * len(TARGETS))
        cursor.execute(
            f"""SELECT c.id,c.character_text,l.script_code,c.reference_strokes,c.reference_strokes_svg
                FROM characters c JOIN languages l ON l.id=c.language_id
                WHERE l.script_code=%s AND c.character_text IN ({placeholders})
                ORDER BY c.character_text FOR UPDATE""",
            (SCRIPT_CODE, *TARGETS),
        )
        rows = cursor.fetchall()
        by_character = {row["character_text"]: row for row in rows}
        if set(by_character) != set(TARGETS):
            missing = set(TARGETS) - set(by_character)
            raise RuntimeError("Chinese database characters missing: " + " ".join(sorted(missing)))
        for character, expected_id in TARGET_IDS.items():
            row = by_character[character]
            if row["id"] != expected_id or row["script_code"] != SCRIPT_CODE:
                raise RuntimeError(f"Database target mismatch for {character}: expected ID {expected_id}, got {row['id']}.")

        planned = []
        for character in TARGETS:
            row = by_character[character]
            old_points = _decode(row["reference_strokes"])
            old_meta = _decode(row["reference_strokes_svg"])
            points, metadata = candidates[character]
            source_sha = metadata["source_file"].split("SHA-256 ")[-1]
            old_source = (old_meta or {}).get("source_file", "")
            old_sha = old_source.split("SHA-256 ")[-1] if "SHA-256 " in old_source else ""
            if old_sha.lower() != source_sha.lower():
                raise RuntimeError(f"Production source checksum differs for {character}; refusing to replace it.")
            metadata = _preserve_valid_review(points, metadata, old_points, old_meta)
            changed = _canonical(old_points) != _canonical(points) or _canonical(old_meta) != _canonical(metadata)
            planned.append({"id": row["id"], "character": character, "old_points": old_points, "old_metadata": old_meta,
                            "points": points, "metadata": metadata, "changed": changed})

        changed = [item for item in planned if item["changed"]]
        print(f"Audited {len(planned)} source-matched Chinese rows; {len(changed)} require the Y-axis correction.")
        for item in planned:
            print(f"{'UPDATE' if item['changed'] else 'UNCHANGED'} id={item['id']} {item['character']} strokes={len(item['points'])} fingerprint={item['metadata']['reference_path_sha256']}")
        if not apply:
            connection.rollback()
            return {"dry_run": True, "updated_ids": [], "pending_ids": [x["id"] for x in changed]}
        if not changed:
            connection.rollback()
            print("All nine references already match the corrected source transform; no write performed.")
            return {"dry_run": False, "updated_ids": [], "pending_ids": []}

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = BACKUP_DIR / f"before_hanzi_writer_y_down_fix_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}.json"
        backup = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "reason": "Exact before-image before source-pinned Hanzi Writer Y-up to SVG/canvas Y-down correction",
            "database": "strokespeak", "script_code": SCRIPT_CODE,
            "source_version": EXPECTED_VERSION,
            "rollback": "In one transaction, restore reference_strokes and reference_strokes_svg from these rows by exact id and character_text; verify affected rowcount before commit.",
            "rows": [{"id": row["id"], "character_text": row["character_text"], "script_code": row["script_code"],
                      "reference_strokes": row["reference_strokes"], "reference_strokes_svg": row["reference_strokes_svg"]}
                     for row in rows],
        }
        with backup_path.open("x", encoding="utf-8") as handle:
            json.dump(backup, handle, ensure_ascii=False, indent=2, default=str)
        for item in changed:
            cursor.execute(
                "UPDATE characters SET reference_strokes=%s, reference_strokes_svg=%s WHERE id=%s AND character_text=%s",
                (json.dumps(item["points"], ensure_ascii=False), json.dumps(item["metadata"], ensure_ascii=False), item["id"], item["character"]),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(f"Expected to update one row for {item['character']}; updated {cursor.rowcount}.")

        # Verify every target, not only changed records, before transaction commit.
        cursor.execute(
            f"""SELECT c.id,c.character_text,c.reference_strokes,c.reference_strokes_svg
                FROM characters c JOIN languages l ON l.id=c.language_id
                WHERE l.script_code=%s AND c.character_text IN ({placeholders})
                ORDER BY c.character_text FOR UPDATE""",
            (SCRIPT_CODE, *TARGETS),
        )
        verified = {row["character_text"]: row for row in cursor.fetchall()}
        for item in planned:
            actual = verified[item["character"]]
            if _canonical(actual["reference_strokes"]) != _canonical(item["points"]):
                raise RuntimeError(f"Point verification failed for {item['character']}; rolling back.")
            if _canonical(actual["reference_strokes_svg"]) != _canonical(item["metadata"]):
                raise RuntimeError(f"SVG/metadata verification failed for {item['character']}; rolling back.")
        connection.commit()
        print(f"Applied {len(changed)} source-verified Chinese coordinate corrections. Backup: {backup_path}")
        print("Instructor review status was not fabricated; changed geometry remains pending review.")
        return {"dry_run": False, "updated_ids": [x["id"] for x in changed], "backup": str(backup_path)}
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Correct pinned Hanzi Writer coordinates for StrokeSpeak's Y-down canvas.")
    parser.add_argument("--apply", action="store_true", help="Apply the nine validated Chinese corrections. Default is read-only dry-run.")
    args = parser.parse_args()
    import_references(apply=args.apply)


if __name__ == "__main__":
    main()