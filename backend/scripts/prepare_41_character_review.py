"""
StrokeSpeak — Consolidated 41-Character Batch Review & Gallery Generator
Generates a single self-contained visual review gallery (gallery_41.html),
manifest (manifest_41.json), and Sanskrit candidate import batch
(sanskrit_import_batch.json) across all 41 target characters:
  - Japanese Hiragana (10): preserved from live KanjiVG DB references
  - Sanskrit Devanagari (10): staged source-attributed candidates
  - Tamil (12): read-only reuse of Codex's staged candidates
  - Simplified Chinese (9): preserved from live Hanzi Writer DB references

Does NOT mutate MySQL, production ML models, or Codex's Tamil files.
"""

import base64
import glob
import hashlib
import html
import json
import math
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.ml.preprocessing import TARGET_SIZE, preprocess_handwriting_image
from main import (
    _classify_stroke_reference,
    _evaluate_handwriting_assessment,
    _prototype_scores,
    get_db_connection,
    model_registry,
)

OUT_DIR = BACKEND / "data" / "reference_strokes" / "batch-review-41-consolidated"
CANDIDATE_MODELS_DIR = BACKEND / "app" / "ml" / "models" / "candidates"
CACHE_DIR = BACKEND / "data" / "reference_strokes" / "commons-vowel-source-cache-2026-11-25"

STROKE_COLORS = [
    "#165ec2",
    "#b32d4d",
    "#067348",
    "#7140a7",
    "#c2640a",
    "#0f766e",
    "#334155",
]

TAMIL_GIF_MAP = {
    25: "../tamil/Writing_Tamil_2.gif",
    110: "../commons-vowel-source-cache-2026-11-25/tamil-aa-aa.gif",
    111: "../commons-vowel-source-cache-2026-11-25/tamil-i-i.gif",
    112: "../commons-vowel-source-cache-2026-11-25/tamil-ii-ii.gif",
    113: "../commons-vowel-source-cache-2026-11-25/tamil-u-u.gif",
    114: "../commons-vowel-source-cache-2026-11-25/tamil-uu-uu.gif",
    115: "../commons-vowel-source-cache-2026-11-25/tamil-e-e.gif",
    116: "../commons-vowel-source-cache-2026-11-25/tamil-ee-ee.gif",
    117: "../commons-vowel-source-cache-2026-11-25/tamil-ai-ai.gif",
    118: "../commons-vowel-source-cache-2026-11-25/tamil-o-o.gif",
    119: "../commons-vowel-source-cache-2026-11-25/tamil-oo-oo.gif",
    120: "../commons-vowel-source-cache-2026-11-25/tamil-au-au.gif",
}

SANSKRIT_GIF_MAP = {
    217: "../commons-vowel-source-cache-2026-11-25/devanagari-aa-a.gif",
    219: "../commons-vowel-source-cache-2026-11-25/devanagari-ii-i.gif",
    224: "../commons-vowel-source-cache-2026-11-25/devanagari-ai-ai.gif",
    225: "../commons-vowel-source-cache-2026-11-25/devanagari-o-o.gif",
    226: "../commons-vowel-source-cache-2026-11-25/devanagari-au-au.gif",
}

TARGET_IDS = [
    # Japanese Hiragana (10)
    2, 28, 29, 30, 3, 31, 32, 33, 34, 35,
    # Sanskrit Devanagari (10)
    216, 217, 218, 219, 220, 221, 223, 224, 225, 226,
    # Tamil (12)
    25, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120,
    # Simplified Chinese (9)
    241, 242, 243, 244, 245, 247, 248, 249, 252,
]


def render_canvas(strokes, width=700, height=320, area=320, thickness=10):
    factor = 3
    canvas = np.full((height * factor, width * factor, 3), 255, np.uint8)
    for stroke in strokes:
        coords = np.array(
            [[(width - area) / 2 + p["x"] * area, (height - area) / 2 + p["y"] * area] for p in stroke],
            dtype=np.float64,
        )
        if not len(coords):
            continue
        pts = np.rint(coords * factor).astype(np.int32)
        if len(pts) >= 2:
            cv2.polylines(canvas, [pts], False, (0, 0, 0), thickness * factor)
        for pt in pts:
            cv2.circle(canvas, tuple(pt), max(1, thickness * factor // 2), (0, 0, 0), -1)
    return cv2.resize(canvas, (width, height), interpolation=cv2.INTER_AREA)


def points_to_svg_paths(strokes):
    paths = []
    for idx, stroke in enumerate(strokes, 1):
        if not stroke:
            continue
        cmds = [("M" if i == 0 else "L") + f" {p['x'] * 100:.2f} {p['y'] * 100:.2f}" for i, p in enumerate(stroke)]
        paths.append({"d": " ".join(cmds), "order": idx, "path_id": f"s{idx}"})
    return paths


def run_geometry_suite(points, svg_meta):
    classification = _classify_stroke_reference(points, svg_meta)
    perturbed = [
        [
            dict(
                p,
                x=p["x"] * 0.92 + 0.035 + 0.004 * math.sin(i / 4.0),
                y=p["y"] * 0.95 + 0.02,
            )
            for i, p in enumerate(st)
            if i % 2 == 0 or i == len(st) - 1
        ]
        for st in points
    ]
    results = {}
    for key, test_strokes, expected in (
        ("positive_trace", points, True),
        ("positive_perturbed", perturbed, True),
        ("reversed_order", points[::-1], False),
        ("reversed_direction", [st[::-1] for st in points], False),
    ):
        shape, order, too_small = _prototype_scores(test_strokes, points)
        status, passed, _ = _evaluate_handwriting_assessment(shape, order, classification)
        applicable = not (key == "reversed_order" and len(points) <= 1)
        ok = (not too_small and passed is expected) if applicable else True
        results[key] = {
            "shape": round(float(shape), 2),
            "order": round(float(order), 2),
            "status": status,
            "passed": bool(passed),
            "applicable": applicable,
            "check_ok": bool(ok),
        }
    svg_strokes = (svg_meta or {}).get("strokes") or []
    results["svg_point_consistency"] = len(svg_strokes) == len(points) and len(points) > 0
    results["classification_tier"] = classification.get("tier")
    results["all_geometry_ok"] = (
        all(results[k]["check_ok"] for k in ("positive_trace", "positive_perturbed", "reversed_order", "reversed_direction"))
        and results["svg_point_consistency"]
    )
    return results


def load_candidate_models():
    models = {}
    for code, fname in (
        ("sa-devanagari", "sanskrit_devanagari_candidate_v2"),
        ("ta", "tamil_candidate_v2"),
    ):
        pt = CANDIDATE_MODELS_DIR / f"{fname}.pt"
        meta = CANDIDATE_MODELS_DIR / f"{fname}_metadata.json"
        if pt.is_file() and meta.is_file():
            m = torch.jit.load(str(pt), map_location="cpu")
            m.eval()
            md = json.loads(meta.read_text(encoding="utf-8"))
            models[code] = (m, md["classes"])
    return models


def predict_candidate_cnn(cand_models, script_code, img_bgr, expected_char):
    if script_code not in cand_models:
        return None
    model, classes = cand_models[script_code]
    tensor = torch.from_numpy(preprocess_handwriting_image(img_bgr, TARGET_SIZE))
    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1)[0].numpy()
    idx = int(np.argmax(probs))
    pred = classes[idx]
    return {
        "predicted_character": pred,
        "confidence": round(float(probs[idx]) * 100.0, 2),
        "is_match": pred == expected_char,
        "model_name": f"Candidate v2 ({script_code})",
    }


def make_svg_simple(paths, stroke_color="#0f172a", dashed=False):
    if not paths:
        return '<svg viewBox="0 0 100 100"><text x="50" y="54" text-anchor="middle" font-size="10" fill="#94a3b8">None</text></svg>'
    dash_attr = ' stroke-dasharray="2.5 2.5"' if dashed else ""
    parts = [
        f'<path d="{html.escape(p["d"], quote=True)}" fill="none" stroke="{stroke_color}" stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round"{dash_attr}/>'
        for p in paths
    ]
    return f'<svg viewBox="0 0 100 100">{"".join(parts)}</svg>'


def make_svg_comparison(db_paths, cand_paths):
    parts = []
    for p in db_paths:
        parts.append(
            f'<path d="{html.escape(p["d"], quote=True)}" fill="none" stroke="#ef4444" stroke-opacity="0.45" stroke-width="5.2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="3 2.5"/>'
        )
    for p in cand_paths:
        parts.append(
            f'<path d="{html.escape(p["d"], quote=True)}" fill="none" stroke="#0f172a" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    return f'<svg viewBox="0 0 100 100">{"".join(parts)}</svg>'


def make_svg_numbered(strokes, paths, animated=False, card_id=""):
    parts = []
    for i, (st, p) in enumerate(zip(strokes, paths)):
        color = STROKE_COLORS[i % len(STROKE_COLORS)]
        cls_attr = f' class="anim-path" data-card="{card_id}" data-order="{i}"' if animated else ""
        parts.append(
            f'<path{cls_attr} d="{html.escape(p["d"], quote=True)}" fill="none" stroke="{color}" stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        if len(st) >= 2:
            # Direction arrow at ~60% along stroke
            idx = max(1, min(len(st) - 1, int(len(st) * 0.6)))
            prev_idx = max(0, idx - max(1, len(st) // 12))
            ax, ay = st[prev_idx]["x"] * 100.0, st[prev_idx]["y"] * 100.0
            bx, by = st[idx]["x"] * 100.0, st[idx]["y"] * 100.0
            dx, dy = bx - ax, by - ay
            if math.hypot(dx, dy) > 0.2:
                ang = math.degrees(math.atan2(dy, dx))
                parts.append(
                    f'<path d="M -3.8 -2.3 L 0.8 0 L -3.8 2.3 Z" fill="{color}" stroke="#ffffff" stroke-width="0.6" transform="translate({bx:.2f} {by:.2f}) rotate({ang:.1f})"/>'
                )
            sx, sy = st[0]["x"] * 100.0, st[0]["y"] * 100.0
            parts.append(
                f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="4.1" fill="{color}" stroke="#ffffff" stroke-width="0.8"/>'
                f'<text x="{sx:.2f}" y="{sy + 1.4:.2f}" text-anchor="middle" font-size="4.8" font-weight="700" fill="#ffffff">{i + 1}</text>'
            )
    return f'<svg viewBox="0 0 100 100">{"".join(parts)}</svg>'


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cand_models = load_candidate_models()

    # Load live DB rows
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    placeholders = ",".join(["%s"] * len(TARGET_IDS))
    cur.execute(
        f"""
        SELECT c.id, c.character_text, c.meaning, c.pronunciation_text,
               c.reference_strokes, c.reference_strokes_svg, l.script_code, l.name AS language_name
        FROM characters c JOIN languages l ON l.id = c.language_id
        WHERE c.id IN ({placeholders})
        """,
        tuple(TARGET_IDS),
    )
    db_rows = {r["id"]: r for r in cur.fetchall()}
    conn.close()

    # Load staged Sanskrit candidates
    sa_candidates = {}
    for f in sorted(
        glob.glob(str(BACKEND / "data/reference_strokes/review-pending/sanskrit-*_20261126/candidate.json"))
    ):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        sa_candidates[d["character_id"]] = (d, f)

    # Load Codex's Tamil candidates READ-ONLY
    ta_candidates = {}
    for dpath in [BACKEND / "data/reference_strokes/tamil/a-id25-review"] + sorted(
        Path(p) for p in glob.glob(str(BACKEND / "data/reference_strokes/tamil/vowel-review/*")) if Path(p).is_dir()
    ):
        cand_f = dpath / "staged-candidate.json"
        if not cand_f.is_file():
            continue
        c = json.loads(cand_f.read_text(encoding="utf-8"))
        ta_candidates[c["character_id"]] = (c, str(cand_f))

    entries = []
    sanskrit_batch_records = []

    for cid in TARGET_IDS:
        row = db_rows[cid]
        script = row["script_code"]
        ch = row["character_text"]

        db_points = json.loads(row["reference_strokes"]) if row["reference_strokes"] else []
        db_svg_meta = json.loads(row["reference_strokes_svg"]) if row["reference_strokes_svg"] else {}
        db_paths = db_svg_meta.get("strokes") or points_to_svg_paths(db_points)

        if script == "sa-devanagari" and cid in sa_candidates:
            cand, cand_path = sa_candidates[cid]
            cand_points = cand["reference_strokes"]
            cand_svg_meta = cand["reference_strokes_svg"]
            cand_paths = cand_svg_meta.get("strokes") or points_to_svg_paths(cand_points)
            prep_status = "staged_candidate_ready"
            cand_file_rel = os.path.relpath(cand_path, ROOT)
            sanskrit_batch_records.append(
                {
                    "character_id": cid,
                    "character_text": ch,
                    "reference_strokes": cand_points,
                    "reference_strokes_svg": cand_svg_meta,
                    "sha256": hashlib.sha256(json.dumps(cand_points, sort_keys=True).encode("utf-8")).hexdigest(),
                    "source_file": cand_file_rel,
                }
            )
        elif script == "ta" and cid in ta_candidates:
            cand, cand_path = ta_candidates[cid]
            cand_points = cand.get("points") or cand.get("reference_strokes")
            cand_svg_meta = cand.get("svg") or cand.get("reference_strokes_svg")
            cand_paths = cand_svg_meta.get("strokes") or points_to_svg_paths(cand_points)
            prep_status = "codex_tamil_staged_readonly"
            cand_file_rel = os.path.relpath(cand_path, ROOT)
        else:
            cand_points = db_points
            cand_svg_meta = db_svg_meta
            cand_paths = db_paths
            prep_status = "preserved_live_source_attributed"
            cand_file_rel = "live_mysql"

        # Render 700x320 10px brush image (or Codex canvas for Tamil)
        if script == "ta" and cid in ta_candidates:
            canvas_png_path = Path(ta_candidates[cid][1]).parent / "cnn-canvas.png"
            img_bgr = cv2.imread(str(canvas_png_path)) if canvas_png_path.is_file() else render_canvas(cand_points)
        else:
            img_bgr = render_canvas(cand_points)

        ok, png_bytes = cv2.imencode(".png", img_bgr)
        assert ok
        prod_cnn = model_registry.predict(
            image_input=base64.b64encode(png_bytes).decode("ascii"),
            script_code=script,
            expected_character=ch,
        )
        cand_cnn = predict_candidate_cnn(cand_models, script, img_bgr, ch)
        geom = run_geometry_suite(cand_points, cand_svg_meta)

        gif_rel = TAMIL_GIF_MAP.get(cid) or SANSKRIT_GIF_MAP.get(cid)
        if gif_rel and not (OUT_DIR / gif_rel).is_file():
            gif_rel = None

        entries.append(
            {
                "character_id": cid,
                "script_code": script,
                "language_name": row["language_name"],
                "character": ch,
                "meaning": row["meaning"],
                "prep_status": prep_status,
                "candidate_file": cand_file_rel,
                "stroke_count_db": len(db_points),
                "stroke_count_candidate": len(cand_points),
                "source": cand_svg_meta.get("source", "Unknown"),
                "license": cand_svg_meta.get("license", "Pending"),
                "provenance_status": cand_svg_meta.get("provenance_status", "unknown"),
                "source_gif_rel": gif_rel,
                "geometry_tests": geom,
                "prod_cnn": {
                    "predicted": prod_cnn.get("predicted_character"),
                    "confidence": prod_cnn.get("confidence"),
                    "is_match": prod_cnn.get("is_match"),
                },
                "cand_cnn": cand_cnn,
                "db_paths": db_paths,
                "cand_paths": cand_paths,
                "cand_points": cand_points,
            }
        )

    # Save Sanskrit import batch (staged, NOT applied to MySQL)
    import_batch = {
        "batch_name": "sanskrit_10_vowels_staged_import_batch",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "database_mutated": False,
        "requires_explicit_approval": True,
        "count": len(sanskrit_batch_records),
        "records": sanskrit_batch_records,
    }
    (OUT_DIR / "sanskrit_import_batch.json").write_text(
        json.dumps(import_batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Save manifest_41.json (compact summary without bloated point arrays)
    manifest_summary = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_characters": len(entries),
        "geometry_all_ok": sum(1 for e in entries if e["geometry_tests"]["all_geometry_ok"]),
        "prod_cnn_matches": sum(1 for e in entries if e["prod_cnn"]["is_match"]),
        "effective_cnn_matches_with_candidates": sum(
            1
            for e in entries
            if (e["cand_cnn"]["is_match"] if e["cand_cnn"] else e["prod_cnn"]["is_match"])
        ),
        "entries": [
            {k: v for k, v in e.items() if k not in ("db_paths", "cand_paths", "cand_points")}
            for e in entries
        ],
    }
    (OUT_DIR / "manifest_41.json").write_text(
        json.dumps(manifest_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Build consolidated self-contained gallery_41.html
    cards_html = []
    for idx, e in enumerate(entries):
        cid = e["character_id"]
        script = e["script_code"]
        geom = e["geometry_tests"]
        p_cnn = e["prod_cnn"]
        c_cnn = e["cand_cnn"]
        eff_match = c_cnn["is_match"] if c_cnn else p_cnn["is_match"]
        needs_attn = (not geom["all_geometry_ok"]) or (not eff_match)

        if e["source_gif_rel"]:
            src_panel = f'<img src="{html.escape(e["source_gif_rel"], quote=True)}" alt="Authentic source" style="max-width:100%;max-height:110px;object-fit:contain"/>'
        else:
            src_panel = f'<div class="glyph-ref">{html.escape(e["character"])}</div><div class="mini-note">{html.escape(e["source"][:55])}</div>'

        db_svg = make_svg_simple(e["db_paths"], "#64748b")
        cand_svg = make_svg_simple(e["cand_paths"], "#0f172a")
        cmp_svg = make_svg_comparison(e["db_paths"], e["cand_paths"])
        num_svg = make_svg_numbered(e["cand_points"], e["cand_paths"], animated=False)
        anim_svg = make_svg_numbered(e["cand_points"], e["cand_paths"], animated=True, card_id=str(cid))

        prod_badge = f'<span class="badge {"ok" if p_cnn["is_match"] else "fail"}">Prod v1: {html.escape(str(p_cnn["predicted"]))} ({p_cnn["confidence"]}%)</span>'
        cand_badge = (
            f'<span class="badge {"ok" if c_cnn["is_match"] else "fail"}">Cand v2: {html.escape(str(c_cnn["predicted_character"]))} ({c_cnn["confidence"]}%)</span>'
            if c_cnn
            else '<span class="badge muted">Cand v2: N/A (Prod used)</span>'
        )
        geom_badge = f'<span class="badge {"ok" if geom["all_geometry_ok"] else "fail"}">Geom: {"PASS" if geom["all_geometry_ok"] else "CHECK"} ({e["stroke_count_candidate"]} strokes)</span>'

        cards_html.append(
            f"""
        <article class="card" data-script="{html.escape(script)}" data-attn="{'1' if needs_attn else '0'}">
          <header class="card-head">
            <div class="char-title">
              <span class="big-char">{html.escape(e["character"])}</span>
              <div>
                <div class="meta-top">ID {cid} · {html.escape(e["language_name"])} · {html.escape(e["meaning"] or "")}</div>
                <div class="meta-sub">Status: <b>{html.escape(e["prep_status"])}</b> · Provenance: {html.escape(e["provenance_status"])}</div>
              </div>
            </div>
            <div class="badges">
              {geom_badge}
              {prod_badge}
              {cand_badge}
            </div>
          </header>
          <div class="panels">
            <div class="panel"><div class="ptitle">1. Authentic Source</div><div class="pbox">{src_panel}</div></div>
            <div class="panel"><div class="ptitle">2. Existing DB ({e["stroke_count_db"]}s)</div><div class="pbox">{db_svg}</div></div>
            <div class="panel"><div class="ptitle">3. Corrected / Target ({e["stroke_count_candidate"]}s)</div><div class="pbox">{cand_svg}</div></div>
            <div class="panel"><div class="ptitle">4. Curve Compare (Red=DB)</div><div class="pbox">{cmp_svg}</div></div>
            <div class="panel"><div class="ptitle">5-6. Order &amp; Arrows</div><div class="pbox">{num_svg}</div></div>
            <div class="panel">
              <div class="ptitle">7. Animated Demo <button class="play-btn" onclick="replayCard('{cid}')">Replay</button></div>
              <div class="pbox">{anim_svg}</div>
            </div>
          </div>
          <footer class="card-foot">
            <div><b>8. CNN:</b> Prod v1={html.escape(str(p_cnn["predicted"]))} ({p_cnn["confidence"]}%) {'✓' if p_cnn['is_match'] else '✗'} {('| Cand v2=' + html.escape(str(c_cnn['predicted_character'])) + f' ({c_cnn["confidence"]}%) ✓' if c_cnn and c_cnn['is_match'] else '')}</div>
            <div><b>9. Geometry:</b> Pos {geom['positive_trace']['shape']}/{geom['positive_trace']['order']} · Pert {geom['positive_perturbed']['shape']}/{geom['positive_perturbed']['order']} · RevOrder {'Reject ✓' if not geom['reversed_order']['passed'] else ('N/A' if not geom['reversed_order']['applicable'] else 'FAIL')} · RevDir {'Reject ✓' if not geom['reversed_direction']['passed'] else 'FAIL'} · SVG Sync {'✓' if geom['svg_point_consistency'] else '✗'}</div>
            <div><b>10. Source &amp; License:</b> {html.escape(e["source"])} — <i>{html.escape(e["license"])}</i> ({html.escape(e["candidate_file"])})</div>
          </footer>
        </article>
        """
        )

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>StrokeSpeak — 41-Character Consolidated Visual Review Gallery</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
  .topbar {{ position: sticky; top: 0; z-index: 20; background: #0f172a; color: #f8fafc; padding: 14px 20px; display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between; }}
  .topbar h1 {{ margin: 0; font-size: 18px; }}
  .summary {{ font-size: 13px; color: #cbd5e1; }}
  .filters {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .fbtn {{ border: 1px solid #475569; background: #1e293b; color: #f8fafc; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; }}
  .fbtn.active {{ background: #4f46e5; border-color: #6366f1; }}
  .container {{ max-width: 1400px; margin: 18px auto; padding: 0 16px; display: flex; flex-direction: column; gap: 16px; }}
  .card {{ background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
  .card-head {{ display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 10px; }}
  .char-title {{ display: flex; align-items: center; gap: 12px; }}
  .big-char {{ font-size: 38px; line-height: 1; font-weight: 700; min-width: 48px; text-align: center; }}
  .meta-top {{ font-weight: 600; font-size: 14px; }}
  .meta-sub {{ font-size: 12px; color: #475569; }}
  .badges {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .badge {{ font-size: 12px; padding: 4px 8px; border-radius: 999px; font-weight: 600; }}
  .badge.ok {{ background: #dcfce7; color: #166534; }}
  .badge.fail {{ background: #fee2e2; color: #991b1b; }}
  .badge.muted {{ background: #f1f5f9; color: #475569; }}
  .panels {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; }}
  @media (max-width: 1100px) {{ .panels {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
  .panel {{ border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px; background: #f8fafc; }}
  .ptitle {{ font-size: 11px; font-weight: 600; color: #334155; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }}
  .pbox {{ height: 120px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; padding: 4px; }}
  .pbox svg {{ width: 100%; height: 100%; }}
  .glyph-ref {{ font-size: 46px; line-height: 1.1; }}
  .mini-note {{ font-size: 9px; color: #64748b; text-align: center; }}
  .play-btn {{ font-size: 10px; padding: 2px 6px; border-radius: 4px; border: 1px solid #4f46e5; background: #eef2ff; color: #3730a3; cursor: pointer; }}
  .card-foot {{ margin-top: 10px; padding-top: 8px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #334155; display: flex; flex-direction: column; gap: 3px; }}
</style>
</head>
<body>
<div class="topbar">
  <div>
    <h1>StrokeSpeak — 41-Character Consolidated Review Gallery</h1>
    <div class="summary">Total: {len(entries)} | Geometry PASS: {manifest_summary['geometry_all_ok']}/41 | Prod CNN: {manifest_summary['prod_cnn_matches']}/41 | With Candidate CNNs (SA/TA): {manifest_summary['effective_cnn_matches_with_candidates']}/41</div>
  </div>
  <div class="filters">
    <button class="fbtn active" onclick="filterCards('all', this)">All (41)</button>
    <button class="fbtn" onclick="filterCards('ja-hiragana', this)">Japanese (10)</button>
    <button class="fbtn" onclick="filterCards('sa-devanagari', this)">Sanskrit (10)</button>
    <button class="fbtn" onclick="filterCards('ta', this)">Tamil (12)</button>
    <button class="fbtn" onclick="filterCards('zh-hans', this)">Chinese (9)</button>
    <button class="fbtn" onclick="filterCards('attn', this)">Needs Attention</button>
    <button class="fbtn" onclick="replayAll()">Replay All Animations</button>
  </div>
</div>
<main class="container">
  {"".join(cards_html)}
</main>
<script>
function filterCards(mode, btn) {{
  document.querySelectorAll('.fbtn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  document.querySelectorAll('.card').forEach(card => {{
    if (mode === 'all') card.style.display = '';
    else if (mode === 'attn') card.style.display = card.dataset.attn === '1' ? '' : 'none';
    else card.style.display = card.dataset.script === mode ? '' : 'none';
  }});
}}
function replayCard(cid) {{
  const paths = Array.from(document.querySelectorAll(`.anim-path[data-card="${{cid}}"]`))
    .sort((a, b) => Number(a.dataset.order) - Number(b.dataset.order));
  paths.forEach(p => {{
    const len = p.getTotalLength();
    p.style.transition = 'none';
    p.style.strokeDasharray = len;
    p.style.strokeDashoffset = len;
  }});
  let delay = 50;
  paths.forEach(p => {{
    const len = p.getTotalLength();
    setTimeout(() => {{
      p.style.transition = 'stroke-dashoffset 650ms ease';
      p.style.strokeDashoffset = '0';
    }}, delay);
    delay += 700;
  }});
}}
function replayAll() {{
  document.querySelectorAll('.card').forEach(c => {{
    if (c.style.display !== 'none') {{
      const btn = c.querySelector('.play-btn');
      if (btn) btn.click();
    }}
  }});
}}
window.addEventListener('DOMContentLoaded', replayAll);
</script>
</body>
</html>"""
    (OUT_DIR / "gallery_41.html").write_text(html_doc, encoding="utf-8")
    print(
        f"Generated 41-character gallery & manifest: "
        f"Geom={manifest_summary['geometry_all_ok']}/41 | "
        f"ProdCNN={manifest_summary['prod_cnn_matches']}/41 | "
        f"WithCandCNN={manifest_summary['effective_cnn_matches_with_candidates']}/41"
    )


if __name__ == "__main__":
    main()
