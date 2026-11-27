from __future__ import annotations
import argparse
import hashlib
import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
from app.db.database import get_db_connection
DATA_DIR = BACKEND_DIR / "data" / "reference_strokes" / "tamil"
SOURCE_FILE = DATA_DIR / "Writing_Tamil_2.gif"
REFERENCE_FILE = DATA_DIR / "tamil_a_reference.json"
BACKUP_DIR = BACKEND_DIR / "data" / "reference_strokes" / "backups"
EXPECTED_SOURCE_SHA256 = "0F6F7429872E8BDBF6B2F57E8A1E358EF5F1822FBA7DDB1F7FF9E91AB20FA211"
TARGET_CHARACTER_ID = 25
TARGET_CHARACTER = "\u0B85"
TARGET_SCRIPT_CODE = "ta"
SVG_VIEWBOX = "0 0 100 100"

def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def densify_stroke(anchors, max_source_step=1.5):
    points = []
    for start, end in zip(anchors, anchors[1:]):
        dx, dy = float(end[0])-float(start[0]), float(end[1])-float(start[1])
        steps = max(1, math.ceil(math.hypot(dx, dy)/max_source_step))
        if not points:
            points.append((float(start[0]), float(start[1])))
        for i in range(1, steps+1):
            point = (float(start[0])+dx*i/steps, float(start[1])+dy*i/steps)
            if math.dist(points[-1], point) > 1e-9:
                points.append(point)
    return points

def build_reference(config):
    digest = hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest().upper()
    if digest != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"Source GIF checksum mismatch: {digest}")
    if (config.get("character_id"), config.get("character"), config.get("script_code")) != (25, TARGET_CHARACTER, TARGET_SCRIPT_CODE):
        raise ValueError("Reference must target Tamil அ (U+0B85), script ta, character ID 25.")
    anchors = config.get("stroke_anchors")
    if not isinstance(anchors, list) or len(anchors) != 4:
        raise ValueError("Expected four ordered strokes as shown in the pinned source animation.")
    dense = []
    for order, item in enumerate(anchors, 1):
        if item.get("order") != order or len(item.get("points", [])) < 2:
            raise ValueError("Stroke order or anchor data is incomplete.")
        dense.append(densify_stroke(item["points"]))
    all_points = [p for stroke in dense for p in stroke]
    min_x, max_x = min(p[0] for p in all_points), max(p[0] for p in all_points)
    min_y, max_y = min(p[1] for p in all_points), max(p[1] for p in all_points)
    span_x, span_y = max_x-min_x, max_y-min_y
    scale = 76.0/max(span_x, span_y)
    offset_x = (100-span_x*scale)/2-min_x*scale
    offset_y = (100-span_y*scale)/2-min_y*scale
    point_strokes, svg_strokes = [], []
    for order, stroke in enumerate(dense, 1):
        mapped = [(x*scale+offset_x, y*scale+offset_y) for x,y in stroke]
        distances = [0.0]
        for a,b in zip(mapped,mapped[1:]):
            distances.append(distances[-1]+math.dist(a,b))
        total = distances[-1] or 1.0
        points = [
            {"x":round(x,4),"y":round(y,4),"time":int(round(900*distances[i]/total))}
            for i,(x,y) in enumerate(mapped)
        ]
        point_strokes.append(points)
        path_d = "M " + " L ".join(f"{p['x']:.4f} {p['y']:.4f}" for p in points)
        svg_strokes.append({"d":path_d,"order":order,"path_id":f"tamil-a-s{order}"})
    metadata = {
        "source":"Wikimedia Commons · Writing Tamil 2.gif · source-specific instructional animation",
        "source_url":"https://commons.wikimedia.org/wiki/File:Writing_Tamil_2.gif",
        "source_asset_url":"https://upload.wikimedia.org/wikipedia/commons/7/7c/Writing_Tamil_2.gif",
        "source_file":"backend/data/reference_strokes/tamil/Writing_Tamil_2.gif",
        "source_author":"Info-farmer (Wikimedia Commons contributor)",
        "license":"CC BY-SA 3.0 Unported",
        "license_url":"https://creativecommons.org/licenses/by-sa/3.0/",
        "attribution":"Adapted from Writing Tamil 2.gif by Info-farmer via Wikimedia Commons, CC BY-SA 3.0 Unported. Its low-resolution visible centerlines were manually digitized into normalized vector and point paths.",
        "source_asset_sha256":digest,
        "source_reference_style":"This animation's depicted sequence; not asserted as the only Tamil handwriting convention.",
        "source_pixel_size":config["source_pixel_size"],
        "trace_method":config["trace_method"],
        "viewBox":SVG_VIEWBOX,
        "character":TARGET_CHARACTER,
        "script_code":TARGET_SCRIPT_CODE,
        "character_id":TARGET_CHARACTER_ID,
        "stroke_count":len(svg_strokes),
        "stroke_labels":config["stroke_labels"],
        "strokes":svg_strokes,
        "provenance_status":"verified",
        "instructional_review_status":"pending",
        "watermark_align_to_reference":True,
        "timestamps":"Application-assigned 0–900 ms per stroke, proportional to traced path length; not source animation timing.",
        "derivative_license":"CC BY-SA 3.0 Unported",
    }
    summary = {
        "source_sha256":digest,
        "stroke_count":len(point_strokes),
        "point_counts":[len(s) for s in point_strokes],
        "source_aspect_ratio":round(span_x/span_y,6),
        "normalized_width":round(span_x*scale,4),
        "normalized_height":round(span_y*scale,4),
    }
    return point_strokes, metadata, summary

def load_reference():
    if not SOURCE_FILE.is_file() or not REFERENCE_FILE.is_file():
        raise FileNotFoundError("Expected Writing_Tamil_2.gif and tamil_a_reference.json in the Tamil reference folder.")
    return build_reference(json.loads(REFERENCE_FILE.read_text(encoding="utf-8")))

def decode(value):
    return json.loads(value) if isinstance(value,str) else value

def update_database(points, metadata, apply=False):
    if not apply:
        print("Dry run: database unchanged. Pass --apply to update only characters.id=25.")
        return
    connection = cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT c.* FROM characters c
               JOIN languages l ON l.id=c.language_id
               WHERE c.id=%s AND c.character_text=%s AND l.script_code=%s
               FOR UPDATE""",
            (TARGET_CHARACTER_ID,TARGET_CHARACTER,TARGET_SCRIPT_CODE),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("Database target mismatch: expected character ID 25, language script ta, U+0B85.")
        old_points = decode(row.get("reference_strokes"))
        old_metadata = decode(row.get("reference_strokes_svg"))
        if canonical_json(old_points)==canonical_json(points) and canonical_json(old_metadata)==canonical_json(metadata):
            connection.rollback()
            print("Already current: character ID 25 matches this source-pinned reference; no write performed.")
            return
        BACKUP_DIR.mkdir(parents=True,exist_ok=True)
        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path=BACKUP_DIR/f"tamil-a-char25-before-{stamp}-{uuid.uuid4().hex[:8]}.json"
        backup={"backup_created_at_utc":datetime.now(timezone.utc).isoformat(),"table":"characters","character_id":TARGET_CHARACTER_ID,"row":row}
        backup_path.write_text(json.dumps(backup,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        cursor.execute(
            "UPDATE characters SET reference_strokes=%s, reference_strokes_svg=%s WHERE id=%s AND character_text=%s",
            (canonical_json(points),canonical_json(metadata),TARGET_CHARACTER_ID,TARGET_CHARACTER),
        )
        if cursor.rowcount!=1:
            raise RuntimeError(f"Expected to update one row, updated {cursor.rowcount}.")
        connection.commit()
        print(f"Updated only characters.id=25. Pre-update row backup: {backup_path}")
    except Exception:
        if connection:
            connection.rollback()
        raise
    finally:
        if cursor: cursor.close()
        if connection and connection.is_connected(): connection.close()

def main():
    parser=argparse.ArgumentParser(description="Import the pinned Tamil அ reference for character ID 25.")
    parser.add_argument("--apply",action="store_true",help="Back up and update only characters.id=25. Without this flag, validate in dry-run mode.")
    args=parser.parse_args()
    points,metadata,summary=load_reference()
    print(json.dumps(summary,indent=2))
    print("Instructional review status:",metadata["instructional_review_status"])
    update_database(points,metadata,apply=args.apply)

if __name__=="__main__":
    main()
