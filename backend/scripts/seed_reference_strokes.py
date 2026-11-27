# -*- coding: utf-8 -*-
"""Seed verified KanjiVG reference paths and scorer points for all basic Kana."""
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.db.database import get_db_connection  # noqa: E402

REVISION = "610091ce618cf757ed1357a8954cd65283e015d6"
SOURCE_ROOT = BACKEND / "assets" / "kanjivg"
SVG_DIR = SOURCE_ROOT / "kanji"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/3.0/"
SOURCE_REPO = "https://github.com/KanjiVG/kanjivg"
SAMPLE_STEPS_PER_CUBIC = 8
NUMBER = r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
TOKEN_RE = re.compile(rf"[A-Za-z]|{NUMBER}")
HIRAGANA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
KATAKANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
if len(HIRAGANA) != 46 or len(KATAKANA) != 46:
    raise RuntimeError("Expected exactly 46 basic Hiragana and 46 basic Katakana characters.")
TARGETS = [
    (script, character, f"{ord(character):05x}.svg")
    for script, characters in (("ja-hiragana", HIRAGANA), ("ja-katakana", KATAKANA))
    for character in characters
]


def cubic(p0, p1, p2, p3, t):
    u = 1.0 - t
    return (
        u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1],
    )


def flatten_kanjivg_path(path_d):
    """Sample M/c cubic paths; retain the unmodified `d` string separately."""
    tokens = TOKEN_RE.findall(path_d)
    if not tokens or tokens[0] != "M":
        raise ValueError("Expected a KanjiVG path beginning with absolute M.")
    index = 1
    current = (float(tokens[index]), float(tokens[index + 1]))
    index += 2
    points = [current]
    commands = {"M"}
    while index < len(tokens):
        command = tokens[index]
        if not command.isalpha():
            raise ValueError(f"Unexpected numeric token without a command: {command}")
        index += 1
        commands.add(command)
        if command != "c":
            raise ValueError(f"Unsupported KanjiVG SVG command {command!r}; refusing to approximate it.")
        while index < len(tokens) and not tokens[index].isalpha():
            if index + 5 >= len(tokens) or any(tokens[j].isalpha() for j in range(index, index + 6)):
                raise ValueError("Incomplete relative cubic segment in KanjiVG path.")
            dx1, dy1, dx2, dy2, dx, dy = map(float, tokens[index:index + 6])
            index += 6
            p0 = current
            p1 = (p0[0] + dx1, p0[1] + dy1)
            p2 = (p0[0] + dx2, p0[1] + dy2)
            p3 = (p0[0] + dx, p0[1] + dy)
            for step in range(1, SAMPLE_STEPS_PER_CUBIC + 1):
                points.append(cubic(p0, p1, p2, p3, step / SAMPLE_STEPS_PER_CUBIC))
            current = p3
    if commands != {"M", "c"}:
        raise ValueError(f"Unexpected command set {commands!r}; refusing to alter path semantics.")
    return points


def parse_svg(character, filename):
    svg_path = SVG_DIR / filename
    if not svg_path.is_file():
        raise FileNotFoundError(f"Required KanjiVG source is missing: {svg_path}")
    root = ET.parse(svg_path).getroot()
    view_box = root.attrib.get("viewBox")
    if not view_box:
        raise ValueError(f"{filename} has no viewBox.")
    bounds = [float(value) for value in view_box.replace(",", " ").split()]
    if len(bounds) != 4 or bounds[2] <= 0 or bounds[3] <= 0:
        raise ValueError(f"Invalid viewBox in {filename}: {view_box}")
    min_x, min_y, width, height = bounds
    code = filename[:-4]
    xml_character = None
    for element in root.iter():
        element_id = element.attrib.get("id", "")
        if element_id == f"kvg:{code}":
            xml_character = element.attrib.get("{http://kanjivg.tagaini.net}element")
    if xml_character != character:
        raise ValueError(f"{filename} identifies {xml_character!r}, expected {character!r}.")
    path_items = []
    for element in root.iter():
        path_id = element.attrib.get("id", "")
        match = re.fullmatch(rf"kvg:{re.escape(code)}-s(\d+)", path_id)
        if match:
            path_items.append((int(match.group(1)), path_id, element.attrib.get("d", "")))
    path_items.sort(key=lambda item: item[0])
    if not path_items or [item[0] for item in path_items] != list(range(1, len(path_items) + 1)):
        raise ValueError(f"{filename} has missing or unordered stroke IDs.")
    points_by_stroke = []
    metadata_strokes = []
    for order, path_id, path_d in path_items:
        raw_points = flatten_kanjivg_path(path_d)
        normalized = [
            {"x": round((x - min_x) / width, 6), "y": round((y - min_y) / height, 6), "time": i * 10}
            for i, (x, y) in enumerate(raw_points)
        ]
        points_by_stroke.append(normalized)
        metadata_strokes.append({"order": order, "path_id": path_id, "d": path_d})
    metadata = {
        "source": "KanjiVG",
        "source_repository": SOURCE_REPO,
        "source_revision": REVISION,
        "source_file": filename,
        "source_url": f"{SOURCE_REPO}/blob/{REVISION}/kanji/{filename}",
        "license": "Creative Commons Attribution-Share Alike 3.0 (CC BY-SA 3.0)",
        "license_url": LICENSE_URL,
        "character": character,
        "viewBox": view_box,
        "stroke_count": len(metadata_strokes),
        "strokes": metadata_strokes,
        "scoring_points_note": "Points are sampled from the original SVG cubics; time values are point-order indices, not measured writing durations.",
    }
    return metadata, points_by_stroke


def load_json(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


def write_backup(backup_dir, prefix, rows, counts):
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = backup_dir / f"{prefix}-{stamp}.json"
    payload = {
        "created_at_local": datetime.now().astimezone().isoformat(),
        "purpose": "Required pre-change backup for KanjiVG reference stroke task.",
        "table_counts_before_change": counts,
        "affected_rows": {"characters": rows},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
    return path


def main():
    if not (SOURCE_ROOT / "COPYING").is_file():
        raise FileNotFoundError("KanjiVG COPYING license file is missing; no database changes attempted.")
    parsed = [(script, glyph, filename, *parse_svg(glyph, filename)) for script, glyph, filename in TARGETS]
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SHOW COLUMNS FROM characters LIKE 'stroke_count'")
        has_stroke_count = cursor.fetchone() is not None
        cursor.execute("SHOW COLUMNS FROM characters LIKE 'reference_strokes_svg'")
        has_svg_column = cursor.fetchone() is not None
        cursor.execute("SELECT COUNT(*) AS n FROM characters")
        initial_character_count = cursor.fetchone()["n"]
        cursor.execute("SELECT COUNT(*) AS n FROM practice_attempts")
        initial_attempt_count = cursor.fetchone()["n"]
        records = []
        for script, glyph, filename, metadata, points in parsed:
            cursor.execute(
                "SELECT c.id, c.language_id, c.character_text, c.pronunciation_text, c.reference_strokes "
                "FROM characters c JOIN languages l ON l.id=c.language_id "
                "WHERE l.script_code=%s AND c.character_text=%s",
                (script, glyph),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError(f"Database character {glyph!r} under {script!r} is missing; no row updates attempted.")
            if has_stroke_count:
                cursor.execute("SELECT stroke_count FROM characters WHERE id=%s", (row["id"],))
                row["stroke_count"] = cursor.fetchone()["stroke_count"]
            else:
                row["stroke_count"] = None
            if row["stroke_count"] is not None and row["stroke_count"] != metadata["stroke_count"]:
                print(
                    f"COUNT MISMATCH: {glyph} MySQL stroke_count={row['stroke_count']}, "
                    f"KanjiVG paths={metadata['stroke_count']}; this row will not be updated."
                )
                row["count_mismatch"] = True
            else:
                row["count_mismatch"] = False
            records.append({"row": row, "metadata": metadata, "points": points})

        backup_dir = BACKEND / "db_backups"
        if not has_svg_column:
            pre_ddl_rows = [{k: v for k, v in record["row"].items() if k != "count_mismatch"} for record in records]
            ddl_backup = write_backup(
                backup_dir,
                "kanjivg-reference-rows-before-svg-column",
                pre_ddl_rows,
                {"characters": initial_character_count, "practice_attempts": initial_attempt_count},
            )
            cursor.execute("ALTER TABLE characters ADD COLUMN reference_strokes_svg JSON NULL AFTER reference_strokes")
            connection.commit()
            has_svg_column = True
            print(f"Schema column added: reference_strokes_svg JSON NULL; pre-DDL backup: {ddl_backup}")
        else:
            print("Schema column reference_strokes_svg already exists; no schema change.")
        if not has_stroke_count:
            print("MySQL has no stroke_count column; path counts were taken directly from the verified KanjiVG SVG source files.")

        cursor.execute("SELECT COUNT(*) AS n FROM characters")
        character_count_before_update = cursor.fetchone()["n"]
        update_rows = []
        skipped_existing = skipped_mismatch = 0
        for record in records:
            row = record["row"]
            cursor.execute("SELECT reference_strokes_svg FROM characters WHERE id=%s", (row["id"],))
            source_value = load_json(cursor.fetchone()["reference_strokes_svg"])
            points_value = load_json(row["reference_strokes"])
            if row["count_mismatch"]:
                skipped_mismatch += 1
            elif points_value is not None or source_value is not None:
                skipped_existing += 1
            else:
                update_rows.append(record)
        if update_rows:
            ids = [record["row"]["id"] for record in update_rows]
            placeholders = ",".join(["%s"] * len(ids))
            cursor.execute(
                "SELECT id, language_id, character_text, pronunciation_text, reference_strokes, reference_strokes_svg "
                f"FROM characters WHERE id IN ({placeholders}) ORDER BY id",
                tuple(ids),
            )
            rows_before_update = cursor.fetchall()
            cursor.execute("SELECT COUNT(*) AS n FROM practice_attempts")
            attempts_before_update = cursor.fetchone()["n"]
            backup = write_backup(
                backup_dir,
                "kanjivg-reference-strokes-before-update",
                rows_before_update,
                {"characters": character_count_before_update, "practice_attempts": attempts_before_update},
            )
            print(f"Pre-UPDATE JSON backup: {backup}")
            print(
                f"Before UPDATE counts: characters={character_count_before_update}; "
                f"practice_attempts={attempts_before_update}; affected rows={len(update_rows)}"
            )
            for record in update_rows:
                row = record["row"]
                cursor.execute(
                    "UPDATE characters SET reference_strokes=%s, reference_strokes_svg=%s "
                    "WHERE id=%s AND reference_strokes IS NULL AND reference_strokes_svg IS NULL",
                    (
                        json.dumps(record["points"], ensure_ascii=False),
                        json.dumps(record["metadata"], ensure_ascii=False),
                        row["id"],
                    ),
                )
                if cursor.rowcount != 1:
                    connection.rollback()
                    raise RuntimeError(f"Character ID {row['id']} changed during seed; transaction rolled back.")
            connection.commit()
        else:
            backup = None

        cursor.execute("SELECT COUNT(*) AS n FROM characters")
        character_count_after = cursor.fetchone()["n"]
        cursor.execute("SELECT COUNT(*) AS n FROM practice_attempts")
        attempts_after = cursor.fetchone()["n"]
        print(f"KanjiVG targets: {len(TARGETS)}; updated: {len(update_rows)}; skipped existing: {skipped_existing}; skipped count mismatch: {skipped_mismatch}")
        for record in records:
            print(
                f"U+{ord(record['metadata']['character']):04X} from {record['metadata']['source_file']}: "
                f"{record['metadata']['stroke_count']} strokes, viewBox {record['metadata']['viewBox']}"
            )
        print(f"After UPDATE counts: characters={character_count_after}; practice_attempts={attempts_after}")
        if backup is None:
            print("Pre-UPDATE JSON backup: not needed; no rows required an update.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
