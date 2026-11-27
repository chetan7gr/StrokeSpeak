"""Create a non-destructive, source-pinned review batch for the 41 trained classes.

This tool is staging-only: it performs SELECT queries and writes JSON/HTML review
artifacts. It contains no INSERT/UPDATE/DELETE path and never changes MySQL.
"""
from __future__ import annotations

import copy
import hashlib
import html
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data" / "reference_strokes"
OUTPUT_ROOT = DATA_DIR
FUDE_DIR = DATA_DIR / "fude-kana-data-ab69a27"
FUDE_REVISION = "ab69a27e2f5a5125ac89b5f13a1b0f0e318d5319"
CAPTURE_INBOX = DATA_DIR / "capture-inbox"
BLOCKED_TARGETS = {
    "sa-devanagari": ("आ", "ई", "ऐ", "ओ", "औ"),
    "ta": ("ஆ", "இ", "ஈ", "உ", "ஊ", "எ", "ஏ", "ஐ", "ஒ", "ஓ", "ஔ"),
}
FUDE_HASHES = {
    "03042.json": "87ED77DF3B2AD24527B4FCCAAC2D4F2B228AE140D465A68C7B7C94AD58FCE864",
    "03044.json": "19BB92EF0008009677F23DB85B2957DF23B6BD7993183FCAAB96C953B5620B3A",
    "03046.json": "10C2B6112322AAD9F53DD9071064D9039EE9E7038FCDF082FE9C802D5329AACB",
    "03048.json": "36508EECC3920337B4D40EAA0E924EA80FACA745A04EB07A15392E396B86834F",
    "0304a.json": "DBF770D62D91BFB7ADFE08C18542AA13E84ED50C3CCED572B280674E7D39277E",
    "0304b.json": "1DDEA5621C68993D088AD90DBE2B689BDE46FA4FDEEDFA93F127D4B80ACE1DE9",
    "0304d.json": "1144490E372F136C429B7AE39257EF842F6E2E81A06F4E758A431615B9AB8CDE",
    "0304f.json": "0BF3259F7C1163BCB1897BE7655132A991977AFD8EFA54EE3450915DC6D3A303",
    "03051.json": "7393462CB0AFC4B876A05752E065F71D88E098BE3AF05EDE547867F371746097",
    "03053.json": "DE806B7E4B326FDCD801723B00B764A1365ABAAE3B184A5151C6DA5A1FAB6F45",
}
SCRIPTS = ("ja-hiragana", "sa-devanagari", "ta", "zh-hans")
SCRIPT_NAMES = {
    "ja-hiragana": "Japanese Hiragana",
    "sa-devanagari": "Sanskrit Devanagari",
    "ta": "Tamil",
    "zh-hans": "Simplified Chinese",
}
PALETTE = ("#4f46e5", "#059669", "#ea580c", "#2563eb", "#9333ea", "#0891b2", "#be123c", "#65a30d")


def load_json_field(value):
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        return json.loads(value) if value else None
    return value


def get_classes():
    sys.path.insert(0, str(BACKEND_DIR))
    from app.ml.registry import SCRIPT_REGISTRY

    classes = {}
    for script in SCRIPTS:
        config = SCRIPT_REGISTRY[script]
        meta_path = BACKEND_DIR / "app" / "ml" / "models" / config["metadata_file"]
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        classes[script] = metadata["classes"]
    expected = sum(map(len, classes.values()))
    if expected != 41:
        raise RuntimeError(f"Expected 41 current CNN classes, found {expected}.")
    return classes


def source_points_to_app_points(strokes):
    """Apply one uniform scale and center, returning the canonical app point form."""
    pairs = []
    for stroke in strokes:
        if len(stroke) < 2:
            raise ValueError("A trajectory stroke has fewer than two points.")
        for point in stroke:
            x, y = float(point[0]), float(point[1])
            if not (math.isfinite(x) and math.isfinite(y)):
                raise ValueError("Non-finite source coordinate.")
            pairs.append((x, y))
    min_x = min(x for x, _ in pairs)
    max_x = max(x for x, _ in pairs)
    min_y = min(y for _, y in pairs)
    max_y = max(y for _, y in pairs)
    extent = max(max_x - min_x, max_y - min_y)
    if extent <= 0:
        raise ValueError("Source trajectory has zero extent.")
    scale = 0.76 / extent
    center_x, center_y = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0
    result = []
    for stroke in strokes:
        converted = []
        for index, (x, y) in enumerate(stroke):
            converted.append({
                "x": round(0.5 + (float(x) - center_x) * scale, 6),
                "y": round(0.5 + (float(y) - center_y) * scale, 6),
                "time": index * 50,
            })
        result.append(converted)
    return result


def normalize_existing_database_points(strokes):
    """Normalize legacy 0–100 Tamil reference coordinates for this HTML preview only."""
    if not isinstance(strokes, list):
        return []
    max_abs = 0.0
    for stroke in strokes:
        for point in stroke:
            max_abs = max(max_abs, abs(float(point["x"])), abs(float(point["y"])))
    divisor = 100.0 if max_abs > 1.0 else 1.0
    return [
        [
            {
                "x": round(float(point["x"]) / divisor, 6),
                "y": round(float(point["y"]) / divisor, 6),
                "time": int(point.get("time", index * 50)),
            }
            for index, point in enumerate(stroke)
        ]
        for stroke in strokes
    ]


def validate_app_points(strokes):
    if not isinstance(strokes, list) or not strokes:
        raise ValueError("Candidate has no strokes.")
    for stroke in strokes:
        if not isinstance(stroke, list) or len(stroke) < 2:
            raise ValueError("Each stroke must have at least two ordered points.")
        previous_time = -1.0
        for point in stroke:
            x, y, timestamp = float(point["x"]), float(point["y"]), float(point["time"])
            if not (
                math.isfinite(x) and math.isfinite(y) and math.isfinite(timestamp)
                and 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0
                and timestamp >= previous_time and timestamp >= 0.0
            ):
                raise ValueError("Candidate points need normalized coordinates and increasing nonnegative times.")
            previous_time = timestamp
    return strokes


def svg_metadata_from_points(character, script, points, source_metadata):
    """Generate display SVG paths only from the same normalized points used by scoring."""
    metadata = copy.deepcopy(source_metadata)
    metadata.update({
        "character": character,
        "script_code": script,
        "viewBox": "0 0 100 100",
        "stroke_count": len(points),
        "strokes": [],
    })
    for index, stroke in enumerate(points, start=1):
        d = "M " + " L ".join(
            f"{float(point['x']) * 100:.2f} {float(point['y']) * 100:.2f}"
            for point in stroke
        )
        metadata["strokes"].append({"order": index, "path_id": f"s{index}", "d": d})
    return metadata


def source_candidate(script, character, point_strokes, metadata, character_id, origin):
    points = validate_app_points(point_strokes)
    svg = svg_metadata_from_points(character, script, points, metadata)
    return {
        "character_id": character_id,
        "script_code": script,
        "character": character,
        "origin": origin,
        "candidate_status": "source_pinned_unreviewed",
        "stroke_count": len(points),
        "point_count": sum(len(stroke) for stroke in points),
        "points": points,
        "svg": svg,
        "review_note": "Source attribution and stroke-order metadata are present; this is not instructor or native-speaker certification.",
    }


def load_fude_candidate(character, character_id):
    filename = f"{ord(character):05x}.json"
    path = FUDE_DIR / filename
    expected = FUDE_HASHES.get(filename)
    if expected is None or not path.is_file():
        raise RuntimeError(f"Missing pinned kana file {filename}.")
    raw_bytes = path.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest().upper()
    if digest != expected:
        raise RuntimeError(f"Pinned kana hash mismatch for {filename}: {digest}")
    raw = json.loads(raw_bytes.decode("utf-8"))
    if raw.get("character") != character or raw.get("codepoint") != f"U+{ord(character):04X}":
        raise RuntimeError(f"Kana label mismatch in {filename}.")
    raw_strokes = [[(float(x), float(y)) for x, y in s["points"]] for s in raw["strokes"]]
    points = source_points_to_app_points(raw_strokes)
    metadata = {
        "source": "fude-kana-data derived from KanjiVG",
        "source_url": f"https://github.com/karimghezali/fude-kana-data/tree/{FUDE_REVISION}",
        "source_file_url": f"https://github.com/karimghezali/fude-kana-data/blob/{FUDE_REVISION}/kana-data/{filename}",
        "source_version": FUDE_REVISION,
        "source_file_sha256": digest,
        "attribution": "Ulrich Apel, KanjiVG; kana extraction and resampling by fude-kana-data contributors",
        "license": "CC BY-SA 3.0; adapted candidate must retain compatible share-alike terms",
        "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
        "source_coordinates": "ordered kana centerline points resampled from KanjiVG SVG paths",
        "coordinate_transform": "uniform aspect-preserving scale to 0.12–0.88 and centered",
        "timing_model": "50 ms per point assigned for StrokeSpeak preview; source provides no timestamps",
        "provenance_status": "source_pinned_candidate",
        "instructional_review_status": "pending",
    }
    return source_candidate("ja-hiragana", character, points, metadata, character_id, "Fude kana data / KanjiVG")


def candidate_from_existing(script, character, character_id, points, prior_svg):
    metadata = copy.deepcopy(prior_svg if isinstance(prior_svg, dict) else {})
    metadata.update({
        "source": metadata.get("source", "existing StrokeSpeak pilot reference"),
        "provenance_status": metadata.get("provenance_status", "existing_reference"),
        "instructional_review_status": metadata.get("instructional_review_status", "pending"),
        "candidate_review_note": "Existing Tamil pilot geometry is reused as-is for comparison. No instructor attestation is inferred.",
    })
    points = validate_app_points(points)
    return source_candidate(script, character, points, metadata, character_id, "completed Tamil அ pilot (existing geometry)")


def render_svg(strokes, character, svg_key):
    if not strokes:
        return '<div class="missing">No usable stroke geometry</div>'
    watermark = html.escape(character)
    bits = [
        f'<svg class="glyph" viewBox="0 0 100 100" role="img" aria-label="{watermark} stroke-order reference">',
        '<defs><marker id="arrow" markerWidth="3.5" markerHeight="3.5" refX="2.8" refY="1.75" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L3.5,1.75 L0,3.5 z" fill="#334155"/></marker></defs>',
        f'<text x="50" y="59" text-anchor="middle" dominant-baseline="middle" class="watermark">{watermark}</text>',
    ]
    for order, stroke in enumerate(strokes, start=1):
        color = PALETTE[(order - 1) % len(PALETTE)]
        coords = " ".join(f"{float(p['x']) * 100:.2f},{float(p['y']) * 100:.2f}" for p in stroke)
        first = stroke[0]
        bits.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#{svg_key}-arrow)"/>')
        bits.append(f'<circle cx="{float(first["x"]) * 100:.2f}" cy="{float(first["y"]) * 100:.2f}" r="2.4" fill="{color}"/>')
        bits.append(f'<text x="{float(first["x"]) * 100:.2f}" y="{float(first["y"]) * 100:.2f}" class="order">{order}</text>')
    bits[1] = f'<defs><marker id="{svg_key}-arrow" markerWidth="3.5" markerHeight="3.5" refX="2.8" refY="1.75" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L3.5,1.75 L0,3.5 z" fill="#334155"/></marker></defs>'
    bits.append("</svg>")
    return "".join(bits)


def build_gallery(entries):
    cards = []
    for index, entry in enumerate(entries):
        current = entry["current"]
        candidate = entry.get("candidate")
        current_svg = render_svg(current.get("points") or [], entry["character"], f"cur-{index}")
        if candidate:
            candidate_svg = render_svg(candidate["points"], entry["character"], f"cand-{index}")
            cand_label = f"Staged: {html.escape(candidate['origin'])}"
            cand_meta = f"{candidate['stroke_count']} strokes · {candidate['candidate_status']}"
        else:
            candidate_svg = '<div class="missing">No external ordered-coordinate source staged</div>'
            cand_label = "Staged candidate"
            cand_meta = "UNVERIFIED / source blocker"
        note = html.escape(entry.get("coverage_note", ""))
        cards.append(f"""
        <article class="card" data-script="{html.escape(entry['script_code'])}">
          <header><div><small>{html.escape(SCRIPT_NAMES[entry['script_code']])} · ID {entry['character_id']}</small><h2>{html.escape(entry['character'])}</h2></div>
          <span class="status">{html.escape(entry['review_status'])}</span></header>
          <p class="coverage">{note}</p>
          <div class="compare">
            <section><h3>Current database reference</h3><p>{current.get('stroke_count', 0)} strokes · {html.escape(current.get('provenance_status','unknown'))}</p>{current_svg}</section>
            <section><h3>{cand_label}</h3><p>{html.escape(cand_meta)}</p>{candidate_svg}</section>
          </div>
        </article>""")
    options = "".join(f'<option value="{html.escape(s)}">{html.escape(SCRIPT_NAMES[s])}</option>' for s in SCRIPTS)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>StrokeSpeak · External Stroke Candidate Review</title><style>
    :root{{font-family:Inter,Segoe UI,Arial,sans-serif;color:#172033;background:#f5f7fc}}body{{margin:0;padding:24px}}main{{max-width:1300px;margin:auto}}
    h1{{margin:0 0 8px}}.lead{{color:#52607a;max-width:850px;line-height:1.5}}.toolbar{{display:flex;gap:12px;align-items:center;margin:18px 0}}
    select{{padding:9px;border:1px solid #ccd5e5;border-radius:8px;background:white}}.notice{{padding:12px 16px;background:#fff5dc;border:1px solid #f0d993;border-radius:9px;margin:18px 0}}
    .grid{{display:grid;grid-template-columns:1fr;gap:16px}}.card{{background:white;border:1px solid #e0e6f0;border-radius:14px;padding:16px;box-shadow:0 2px 7px #15264a0c}}
    header{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #eef1f6;padding-bottom:8px}}small{{color:#5d6680}}h2{{font-size:30px;margin:4px 0}}h3{{font-size:15px;margin:8px 0}}
    .status{{font-size:12px;padding:5px 8px;border-radius:12px;background:#eef2ff;color:#4338ca}}.coverage{{color:#52607a;min-height:1.3em}}
    .compare{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.compare section{{border:1px solid #edf0f5;border-radius:10px;padding:10px;min-width:0}}
    .compare p{{font-size:12px;color:#667085;min-height:1.2em}}.glyph{{display:block;width:100%;max-height:340px;aspect-ratio:1/1;background:linear-gradient(#fff,#f8faff);border:1px solid #e8edf6;border-radius:8px}}
    .watermark{{font-family:"Noto Sans Devanagari","Noto Sans Tamil","Noto Sans CJK JP","Noto Sans CJK SC",sans-serif;font-size:63px;fill:#cbd5e1;opacity:.34}}
    .order{{font:700 5px Arial,sans-serif;fill:#fff;stroke:#1f2937;stroke-width:.7px;paint-order:stroke;text-anchor:middle;dominant-baseline:middle}}
    .missing{{height:100%;min-height:220px;display:grid;place-items:center;color:#a12b1d;background:#fff5f2;border:1px dashed #e6aa9c;border-radius:8px;text-align:center;padding:10px}}
    @media(max-width:700px){{body{{padding:12px}}.compare{{grid-template-columns:1fr}}.glyph{{max-height:280px}}}}
    </style></head><body><main><h1>StrokeSpeak · Stroke reference batch review</h1>
    <p class="lead">41 current CNN classes. Candidate paths are shown against the current database geometry. Colors and numbered start points show stroke order; arrowheads show point direction. The staged SVG is generated from the exact normalized points shown for assessment. This gallery is a technical review aid, not a linguistic/instructor certification.</p>
    <div class="notice"><strong>No database changes were made.</strong> Staged candidates are not live. A source citation or capture does not by itself prove a teaching sequence is acceptable. Every captured reference must receive instructor review before a separate, explicitly approved import.</div>
    <div class="toolbar"><label for="filter">Filter language</label><select id="filter"><option value="all">All four groups</option>{options}</select><span>{len(entries)} characters · {sum(bool(e.get('candidate')) for e in entries)} staged candidates</span></div>
    <div class="grid">{''.join(cards)}</div></main>
    <script>document.getElementById('filter').addEventListener('change',e=>{{for(const c of document.querySelectorAll('.card'))c.hidden=e.target.value!=='all'&&c.dataset.script!==e.target.value}});</script>
    </body></html>"""


def load_capture_candidate(path, expected_row, allowed_targets):
    """Validate one developer export and rebuild its SVG from its point strokes."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError(f"{path.name}: unsupported schema_version.")
    key = (payload.get("script_code"), payload.get("character"))
    if key not in allowed_targets:
        raise ValueError(f"{path.name}: only the 16 source-blocked targets accept captures.")
    if int(payload.get("character_id", -1)) != int(expected_row["id"]):
        raise ValueError(f"{path.name}: character ID does not match the live database row.")
    if payload.get("candidate_status") != "captured_pending_review":
        raise ValueError(f"{path.name}: candidate must remain captured_pending_review.")
    review = payload.get("instructor_review")
    if not isinstance(review, dict) or review.get("status") != "pending":
        raise ValueError(f"{path.name}: instructor review must remain pending.")
    source = payload.get("source")
    if not isinstance(source, dict):
        raise ValueError(f"{path.name}: source attribution is required.")
    required_source = ("title", "url", "attribution", "license")
    if any(not str(source.get(field, "")).strip() for field in required_source):
        raise ValueError(f"{path.name}: title, HTTPS source URL, attribution, and license are required.")
    from urllib.parse import urlparse
    parsed_source_url = urlparse(str(source["url"]).strip())
    if parsed_source_url.scheme != "https" or not parsed_source_url.netloc:
        raise ValueError(f"{path.name}: source URL must be a valid HTTPS URL.")
    captured_by = str(payload.get("captured_by", "")).strip()
    captured_at = str(payload.get("captured_at_utc", "")).strip()
    capture_id = str(payload.get("capture_id", "")).strip()
    if not captured_by or not captured_at or not capture_id:
        raise ValueError(f"{path.name}: capture_id, captured_by and captured_at_utc are required.")
    try:
        datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{path.name}: captured_at_utc must be an ISO timestamp.") from error
    points = validate_app_points(payload.get("points"))
    if int(payload.get("stroke_count", -1)) != len(points):
        raise ValueError(f"{path.name}: stroke_count does not match points.")
    point_count = sum(len(stroke) for stroke in points)
    if int(payload.get("point_count", -1)) != point_count:
        raise ValueError(f"{path.name}: point_count does not match points.")

    capture_sha256 = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    source_metadata = {
        "source": str(source["title"]).strip(),
        "source_url": str(source["url"]).strip(),
        "attribution": str(source["attribution"]).strip(),
        "license": str(source["license"]).strip(),
        "license_url": str(source.get("license_url", "")).strip(),
        "captured_by": captured_by,
        "captured_at_utc": captured_at,
        "capture_id": capture_id,
        "capture_file": path.name,
        "capture_file_sha256": capture_sha256,
        "provenance_status": "captured_pending_review",
        "instructional_review_status": "pending",
        "instructor_review_status": "pending",
        "coordinate_transform": "Browser pointer coordinates normalized independently to the square capture canvas.",
        "timing_model": "Captured browser pointer timestamps in milliseconds from the first pointer-down.",
    }
    candidate = source_candidate(
        key[0], key[1], points, source_metadata, int(expected_row["id"]),
        "Developer capture · pending instructor review",
    )
    candidate["candidate_status"] = "captured_pending_review"
    candidate["captured_by"] = captured_by
    candidate["captured_at_utc"] = captured_at
    candidate["capture_id"] = source_metadata["capture_id"]
    candidate["capture_file"] = path.name
    candidate["capture_file_sha256"] = capture_sha256
    candidate["instructor_review"] = {
        "status": "pending",
        "reviewer": "",
        "reviewed_at_utc": "",
        "notes": str(review.get("notes", "")).strip(),
    }
    candidate["review_note"] = "Captured from the cited source; instructor verification is still pending. This candidate is not live."
    return candidate


def main():
    sys.path.insert(0, str(BACKEND_DIR))
    sys.path.insert(0, str(BACKEND_DIR / "scripts"))
    from app.db.database import get_db_connection
    from import_hanzi_writer_reference_strokes import TARGETS as HANZI_TARGETS, _load_and_convert as load_hanzi
    from import_lipi_devanagari_reference_strokes import (
        TARGETS as LIPI_TARGETS, WEIGHTS, read_safetensors, convert_glyph,
    )

    classes = get_classes()
    all_targets = [(script, character) for script, chars in classes.items() for character in chars]
    candidates = {}

    # Kana: exact pinned files from a derivative of KanjiVG. Validate all source hashes.
    for character in classes["ja-hiragana"]:
        filename = f"{ord(character):05x}.json"
        candidate = load_fude_candidate(character, None)
        candidates[("ja-hiragana", character)] = candidate

    # Devanagari: only directly drawn Lipi glyphs that overlap trained classes.
    digest, keys, raw_points, stroke_starts, glyph_starts = read_safetensors(WEIGHTS)
    glyph_lookup = {
        item[0]: index for index, item in enumerate(keys)
        if isinstance(item, list) and len(item) == 2 and item[1] == "glyph"
    }
    for character in classes["sa-devanagari"]:
        if character not in LIPI_TARGETS:
            continue
        point_data, source_meta = convert_glyph(character, glyph_lookup[character], raw_points, stroke_starts, glyph_starts, digest)
        source_meta = copy.deepcopy(source_meta)
        source_meta["candidate_review_note"] = "Lipi marks this as hand-drawn centerline data; instructional review is pending."
        candidates[("sa-devanagari", character)] = source_candidate(
            "sa-devanagari", character, point_data, source_meta, None, "Lipi · hand-drawn Devanagari centerlines"
        )

    # Simplified Chinese: reuse the existing pinned Hanzi Writer conversion, no database import.
    for character in classes["zh-hans"]:
        if character not in HANZI_TARGETS:
            continue
        point_data, source_meta = load_hanzi(character)
        candidates[("zh-hans", character)] = source_candidate(
            "zh-hans", character, point_data, source_meta, None, "Hanzi Writer Data 2.0.1 · Make Me a Hanzi/Arphic"
        )

    # The completed Tamil அ pilot remains the only candidate in its group.
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("START TRANSACTION READ ONLY")
        placeholders = ",".join(["%s"] * len(SCRIPTS))
        cursor.execute(
            f"""SELECT l.script_code,c.id,c.character_text,c.reference_strokes,c.reference_strokes_svg
                FROM characters c JOIN languages l ON l.id=c.language_id
                WHERE l.script_code IN ({placeholders}) ORDER BY l.script_code,c.id""",
            SCRIPTS,
        )
        db_rows = cursor.fetchall()
    finally:
        try:
            connection.rollback()
        finally:
            cursor.close()
            connection.close()

    by_key = {(row["script_code"], row["character_text"]): row for row in db_rows}
    allowed_capture_targets = {
        (script, character)
        for script, characters in BLOCKED_TARGETS.items()
        for character in characters
    }
    capture_files = []
    capture_keys = set()
    if CAPTURE_INBOX.exists():
        for capture_path in sorted(CAPTURE_INBOX.glob("*.json")):
            payload = json.loads(capture_path.read_text(encoding="utf-8"))
            key = (payload.get("script_code"), payload.get("character"))
            row = by_key.get(key)
            if row is None:
                raise ValueError(f"{capture_path.name}: character is absent from the selected database scope.")
            if key in candidates:
                raise ValueError(f"{capture_path.name}: refusing to replace an existing source-backed candidate.")
            if key in capture_keys:
                raise ValueError(f"{capture_path.name}: duplicate capture for the same character.")
            candidate = load_capture_candidate(capture_path, row, allowed_capture_targets)
            candidates[key] = candidate
            capture_keys.add(key)
            capture_files.append(capture_path.name)

    entries, backup_rows = [], []
    for script, character in all_targets:
        row = by_key.get((script, character))
        if row is None:
            raise RuntimeError(f"Missing database character for {script} {character!r}.")
        points = load_json_field(row["reference_strokes"])
        current_svg = load_json_field(row["reference_strokes_svg"])
        points = points if isinstance(points, list) else []
        current_svg = current_svg if isinstance(current_svg, dict) else {}
        # The DB snapshot is preserved exactly below; normalize a display copy only.
        points = normalize_existing_database_points(points)
        current_status = str(current_svg.get("provenance_status", "unknown"))
        current_count = len(points)
        backup_rows.append({
            "character_id": row["id"], "script_code": script, "character": character,
            "reference_strokes": row["reference_strokes"],
            "reference_strokes_svg": row["reference_strokes_svg"],
        })
        candidate = candidates.get((script, character))
        if script == "ta" and character == "அ":
            candidate = candidate_from_existing(script, character, row["id"], points, current_svg)
            candidates[(script, character)] = candidate
        if candidate:
            candidate["character_id"] = row["id"]
        else:
            candidate = None
        if candidate and candidate.get("candidate_status") == "captured_pending_review":
            note = "Developer-captured from the cited source. Instructor review is pending; this export is not live."
        elif script == "ta" and character == "அ":
            note = "Existing reference is marked verified in the database; no instructor attestation is inferred."
        elif script == "ta":
            note = "No suitable licensed ordered-coordinate dataset was found; this character remains pending a sourced capture."
        elif candidate is None:
            note = "No direct source candidate is staged; preserve the current reference pending review."
        else:
            note = "Source candidate is staged; visually compare shape and sequence before any import."
        entries.append({
            "script_code": script, "character_id": row["id"], "character": character,
            "review_status": (
                "captured · pending instructor review"
                if candidate and candidate.get("candidate_status") == "captured_pending_review"
                else "pilot source review" if script == "ta" and character == "அ"
                else "candidate staged" if candidate
                else "source blocked / unverified"
            ),
            "coverage_note": note,
            "current": {
                "points": points, "stroke_count": current_count,
                "provenance_status": current_status,
                "svg_metadata": current_svg,
            },
            "candidate": candidate,
        })

    output_dir = OUTPUT_ROOT / ("batch-review-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    output_dir.mkdir(parents=True, exist_ok=False)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "database_mutated": False,
        "classes_total": len(entries),
        "candidate_count": sum(bool(item["candidate"]) for item in entries),
        "candidate_counts_by_script": {
            script: sum(1 for item in entries if item["script_code"] == script and item["candidate"])
            for script in SCRIPTS
        },
        "source_blocked_by_script": {
            script: sum(1 for item in entries if item["script_code"] == script and not item["candidate"])
            for script in SCRIPTS
        },
        "bulk_import_status": "not applied; source review and explicit approval required",
        "captured_candidates": len(capture_files),
        "capture_inbox_files": capture_files,
        "sources": {
            "kana": {"url": f"https://github.com/karimghezali/fude-kana-data/tree/{FUDE_REVISION}", "license": "CC BY-SA 3.0", "classes": len(classes["ja-hiragana"])},
            "lipi": {"url": "https://huggingface.co/Vishwasaidev/lipi/tree/c547139c82130da50827a1f2bffb995254395600", "license": "CC BY 4.0", "direct_model_overlap": sum(ch in LIPI_TARGETS for ch in classes["sa-devanagari"])},
            "hanzi_writer": {"url": "https://github.com/chanind/hanzi-writer-data/tree/master", "version": "2.0.1", "license": "Arphic Public License", "model_overlap": sum(ch in HANZI_TARGETS for ch in classes["zh-hans"])},
            "tamil_pilot": {"url": "https://commons.wikimedia.org/wiki/File:Writing_Tamil_2.gif", "license": "see local source attribution", "classes": 1},
        },
    }
    (output_dir / "database_backup_41_before_any_import.json").write_text(
        json.dumps({"created_at_utc": summary["created_at_utc"], "scope": "reference fields only for 41 CNN classes", "rows": backup_rows}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    (output_dir / "staged_candidates.json").write_text(
        json.dumps([item["candidate"] for item in entries if item["candidate"]], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "review_manifest.json").write_text(json.dumps({"summary": summary, "entries": entries}, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "review_gallery.html").write_text(build_gallery(entries), encoding="utf-8")
    (output_dir / "README.txt").write_text(
        "Review gallery and candidates. The live MySQL database was read in a READ ONLY transaction and was not modified.\n"
        "Captured JSON can be copied into backend/data/reference_strokes/capture-inbox before rerunning the stage script.\n"
        "Captured candidates remain pending instructor review; no file in this workflow writes to MySQL.\n"
        "database_backup_41_before_any_import.json contains only the 41 target character reference fields.\n"
        "Open review_gallery.html in a browser. Source citations/license notes are in review_manifest.json and the vendored source notices.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output_dir": str(output_dir),
        "total_model_classes": len(entries),
        "staged_candidates": summary["candidate_count"],
        "candidate_counts_by_script": summary["candidate_counts_by_script"],
        "source_blocked_by_script": summary["source_blocked_by_script"],
        "database_mutated": False,
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()