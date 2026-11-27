"""Extract exact standalone Devanagari glyph strokes from pinned Lipi weights."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
from app.db.database import get_db_connection

DATA_DIR = BACKEND_DIR / "data" / "reference_strokes" / "lipi-devanagari-c547139c82130da50827a1f2bffb995254395600"
WEIGHTS = DATA_DIR / "weights.safetensors"
BACKUP_DIR = BACKEND_DIR / "data" / "reference_strokes" / "backups"
REVISION = "c547139c82130da50827a1f2bffb995254395600"
EXPECTED_SHA256 = "ca2e20257ef737f8166b3e1432ff70d5d95bafea6c41159467bf8a236654b7ee"
SCRIPT_CODE = "sa-devanagari"
TARGETS = ("\u0905", "\u0907", "\u0909", "\u090a", "\u090b", "\u090f")
SOURCE_URL = f"https://huggingface.co/Vishwasaidev/lipi/tree/{REVISION}"
WEIGHTS_URL = f"https://huggingface.co/Vishwasaidev/lipi/resolve/{REVISION}/weights.safetensors"


def read_safetensors(path: Path):
    blob = path.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Pinned model file hash mismatch: {digest}")
    if len(blob) < 8:
        raise RuntimeError("Model artifact is too short to be safetensors.")
    header_length = struct.unpack_from("<Q", blob, 0)[0]
    body_start = 8 + header_length
    header = json.loads(blob[8:body_start].decode("utf-8"))

    def unpack_tensor(name: str, fmt: str):
        item = header[name]
        if item["dtype"] != ("F32" if fmt == "f" else "I32"):
            raise RuntimeError(f"Unexpected dtype for {name}: {item['dtype']}")
        start, end = item["data_offsets"]
        return struct.unpack("<" + fmt * ((end - start) // 4), blob[body_start + start:body_start + end])

    meta = header.get("__metadata__") or {}
    keys = json.loads(meta["deva_keys"])
    points = unpack_tensor("glyphs.deva.points", "f")
    stroke_starts = unpack_tensor("glyphs.deva.stroke_start", "i")
    glyph_starts = unpack_tensor("glyphs.deva.glyph_start", "i")
    return digest, keys, points, stroke_starts, glyph_starts


def convert_glyph(character, glyph_index, points, stroke_starts, glyph_starts, digest):
    first_stroke = glyph_starts[glyph_index]
    last_stroke = glyph_starts[glyph_index + 1]
    raw_strokes = []
    for stroke_index in range(first_stroke, last_stroke):
        first_point, last_point = stroke_starts[stroke_index:stroke_index + 2]
        coordinates = [
            (float(points[i * 2]), float(points[i * 2 + 1]))
            for i in range(first_point, last_point)
        ]
        if len(coordinates) < 2:
            raise RuntimeError(f"Source stroke {stroke_index} for {character} has fewer than two points.")
        raw_strokes.append(coordinates)
    if not raw_strokes:
        raise RuntimeError(f"No ordered strokes found for {character}.")

    all_points = [point for stroke in raw_strokes for point in stroke]
    min_x, max_x = min(x for x, _ in all_points), max(x for x, _ in all_points)
    min_y, max_y = min(y for _, y in all_points), max(y for _, y in all_points)
    extent = max(max_x - min_x, max_y - min_y)
    scale = 0.76 / extent if extent else 1.0
    center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2

    normalized, svg_strokes = [], []
    for order, stroke in enumerate(raw_strokes, start=1):
        pts = []
        svg = []
        for point_index, (x, y) in enumerate(stroke):
            nx = round(0.5 + (x - center_x) * scale, 6)
            ny = round(0.5 + (y - center_y) * scale, 6)
            pts.append({"x": nx, "y": ny, "time": point_index * 50})
            svg.append((nx * 100, ny * 100))
        d = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in svg)
        normalized.append(pts)
        svg_strokes.append({"order": order, "path_id": f"s{order}", "d": d})

    metadata = {
        "source": "Lipi · Devanagari calligraphy with no training (Vishwasaidev)",
        "source_url": SOURCE_URL,
        "source_file_url": WEIGHTS_URL,
        "source_version": REVISION,
        "video_credit": "Lipi / Vishwasaidev · CC BY 4.0",
        "source_file": f"weights.safetensors · SHA-256 {digest}",
        "attribution": "Vishwasaidev, Lipi · Devanagari calligraphy with no training",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0); adapted by StrokeSpeak",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "source_coordinates": "Lipi Devanagari hand-drawn centerline points",
        "coordinate_transform": "Centered per-glyph bounds, aspect-preserving scale to 0.12–0.88",
        "timing_model": "Uniform 50 ms intervals assigned for StrokeSpeak playback; not present in source model",
        "provenance_status": "source_attributed",
        "instructional_review_status": "pending",
        "character": character,
        "script_code": SCRIPT_CODE,
        "viewBox": "0 0 100 100",
        "stroke_count": len(normalized),
        "strokes": svg_strokes,
    }
    return normalized, metadata


def import_references():
    digest, keys, points, stroke_starts, glyph_starts = read_safetensors(WEIGHTS)
    lookup = {}
    for index, item in enumerate(keys):
        if isinstance(item, list) and len(item) == 2 and item[1] == "glyph":
            lookup[item[0]] = index
    missing_source = set(TARGETS) - set(lookup)
    if missing_source:
        raise RuntimeError("Exact standalone source glyphs unavailable: " + " ".join(sorted(missing_source)))
    converted = {
        char: convert_glyph(char, lookup[char], points, stroke_starts, glyph_starts, digest)
        for char in TARGETS
    }

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        connection.start_transaction()
        placeholders = ",".join(["%s"] * len(TARGETS))
        cursor.execute(
            f"""SELECT c.id,c.character_text,c.reference_strokes,c.reference_strokes_svg
                FROM characters c JOIN languages l ON l.id=c.language_id
                WHERE l.script_code=%s AND c.character_text IN ({placeholders})
                ORDER BY c.character_text FOR UPDATE""",
            (SCRIPT_CODE, *TARGETS),
        )
        rows = cursor.fetchall()
        by_character = {row["character_text"]: row for row in rows}
        missing = set(TARGETS) - set(by_character)
        if missing:
            raise RuntimeError("Sanskrit database characters missing: " + " ".join(sorted(missing)))
        backup_path = BACKUP_DIR / "before_lipi_devanagari_cc_by_4.0.json"
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        if not backup_path.exists():
            backup = {
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "source_revision": REVISION,
                "rows": [
                    {"id": row["id"], "character": row["character_text"],
                     "reference_strokes": row["reference_strokes"],
                     "reference_strokes_svg": row["reference_strokes_svg"]}
                    for row in rows
                ],
            }
            backup_path.write_text(json.dumps(backup, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        for character in TARGETS:
            row = by_character[character]
            strokes, metadata = converted[character]
            cursor.execute(
                "UPDATE characters SET reference_strokes=%s, reference_strokes_svg=%s WHERE id=%s",
                (json.dumps(strokes, ensure_ascii=False), json.dumps(metadata, ensure_ascii=False), row["id"]),
            )
        connection.commit()
        print(f"Imported exact source paths for {len(TARGETS)} standalone Devanagari glyphs.")
        print(f"Rollback backup: {backup_path}")
        print("Instructional review remains pending; no learner rows were created or changed.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    import_references()
