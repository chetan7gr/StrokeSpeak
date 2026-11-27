"""Stage Tamil vowel review files from pinned progressive handwriting GIFs."""
import base64
import hashlib
import html
import json
import math
import os
from pathlib import Path
import runpy
import sys

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[2]
ROOT = HERE.parent
CACHE = ROOT / "commons-vowel-source-cache-2026-11-25"
OUTPUT = HERE / "vowel-review"
PILOT = HERE / "a-id25-review"
sys.path[:0] = [str(BACKEND / "scripts"), str(BACKEND)]
from main import _classify_stroke_reference, _evaluate_handwriting_assessment, _prototype_scores, model_registry
from stage_external_stroke_candidates import source_candidate

# Waypoints select branches of the final-frame ink ridge. They are read from
# the progressive GIF frames, in arrow order, and snapped to local ink ridges.
# Pipes delimit replay segments at visible restarts. A singleton is a dot.
U = "12,5 21,9 23,17 19,26 10,28 4,23 3,15 7,8 12,5 25,3 35,6 44,12 49,21 49,29 44,37 34,41 16,41 7,44 3,49 6,54 13,56"
E = "24,60 20,53 21,43 27,36 35,34 43,38 47,45 47,54 43,63 35,67 25,66 15,60 8,51 4,40 4,30 9,19 17,10 29,4"
O = "9,48 14,40 23,38 32,42 37,50 35,60 30,66 21,67 12,63 5,56 3,45 6,33 13,22 25,12 38,6 53,3 65,5 80,11 91,20 98,32 102,44 101,53 95,60 85,62 77,60 71,55 69,47 71,39 75,35 68,37 61,43 57,51 57,61 62,70 71,76 82,79 101,79"
O_TAIL = "101,79 77,79 70,82 64,89 60,100 53,108 45,112 34,111 26,108 21,101"
# The two smaller appendages are traced independently in their own rasters.
SPECS = [
 (110, "aa-aa", "43,4 49,8 51,15 48,19 42,21 36,17 36,10 40,5 43,4 52,4 60,7 66,15 67,25 64,33 57,40 47,44 33,45 18,43 9,39 4,34 5,29 12,28 78,28 78,5 | 78,5 78,44 | 78,44 79,39 81,36 87,33 93,34 97,40 95,47 90,53 82,58 72,60 62,60 55,57 53,53 56,49 62,48 69,50"),
 (111, "i-i", "35,31 41,34 45,40 44,45 39,48 33,48 29,45 28,39 31,34 35,31 42,27 51,30 57,35 59,44 58,55 53,65 44,74 33,82 21,87 10,88 4,85 3,80 6,72 14,65 25,60 39,57 50,57 61,60 68,66 72,74 71,81 66,87 58,88 49,86 39,82 29,75 20,67 14,57 10,46 10,35 13,25 19,17 29,9 39,4 50,2 61,4 70,9 76,17 79,27 79,62"),
 (112, "ii-ii", "5,67 5,5 84,5 | 52,5 52,67 | 28,35 | 75,35"),
 (113, "u", U + " 40,56 97,56"),
 (114, "uu-uu", "16,5 23,10 26,19 23,29 16,34 9,33 4,28 4,18 9,9 16,5 28,4 40,5 51,11 58,18 60,29 55,39 46,47 34,50 15,50 8,54 5,60 10,65 19,67 116,67 | 72,55 74,49 80,46 85,48 89,53 89,59 85,65 79,65 73,61 70,55 70,44 74,37 80,32 89,32 95,37 99,44 99,65 | 99,65 99,32 117,32 | 115,32 115,65"),
 (115, "e-e", E + " 92,4 | 76,4 76,66"),
 (116, "ee-ee", "19,49 15,43 17,34 23,29 30,28 35,31 38,36 39,45 35,52 30,55 24,55 17,52 10,47 5,39 3,31 5,22 10,14 17,7 26,3 79,3 | 62,3 62,52 57,57 48,62 40,72"),
 (117, "ai-ai", "11,13 19,13 24,17 26,23 24,28 20,31 13,32 7,30 3,25 3,17 7,9 14,4 24,2 31,4 38,9 42,16 42,31 | 42,31 42,18 45,10 52,5 61,2 68,4 75,10 78,19 78,26 74,33 68,38 59,42 18,42 10,46 5,52 2,60 4,69 10,76 18,78 26,78 34,74 40,68 42,61 42,53 | 42,53 42,63 46,71 52,76 60,78 68,76 75,71 78,64 76,57 71,51"),
 (118, "o-o", O + " | " + O_TAIL + " 20,95 23,89 29,84"),
 (119, "oo-oo", O + " | " + O_TAIL + " 19,95 23,88 29,84 34,85 39,89 42,94 40,100 35,105 29,106 23,103"),
 (120, "au-au", "5,30 9,25 14,24 20,27 23,32 21,38 17,41 11,40 5,36 2,29 3,21 8,14 17,7 27,3 37,3 47,7 55,13 61,21 62,29 58,36 51,39 44,37 41,32 41,26 44,22 39,24 35,28 33,34 35,41 40,46 46,49 60,49 | 60,49 46,49 41,52 37,57 34,64 29,69 23,70 17,68 12,64 12,58 15,53 18,51 | 68,65 70,60 74,59 78,61 80,65 78,70 74,72 69,70 65,66 64,60 65,54 69,49 74,47 80,47 85,51 87,56 87,71 | 87,71 87,47 102,47 | 99,47 99,71"),
]

pilot_helpers = runpy.run_path(str(PILOT / "build_review.py"))
ridge_route = pilot_helpers["ridge_route"]
render = pilot_helpers["render"]
COLORS = ["#1560ae", "#b82c53", "#08774e", "#7440ab", "#9b5100"]
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/3.0/"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snap(distance, x, y):
    options = [(distance[j, i] - 0.96 * math.hypot(i-x, j-y), (i, j))
               for j in range(max(0, y-5), min(distance.shape[0], y+6))
               for i in range(max(0, x-5), min(distance.shape[1], x+6))
               if distance[j, i] > 0]
    if not options:
        raise ValueError(f"No source ink near gate {(x, y)}")
    return max(options)[1]


def extract(mask, gates):
    distance = cv2.distanceTransform(mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    paths = []
    for part in gates.split("|"):
        anchors = [snap(distance, *map(int, token.split(","))) for token in part.split()]
        route = [anchors[0]]
        for start, end in zip(anchors, anchors[1:]):
            if start != end:
                try:
                    route.extend(ridge_route(distance, start, end)[1:])
                except ValueError:
                    # Try an on-ink midpoint without bridging a gap in the raster.
                    mid = snap(distance, *((a+b)//2 for a,b in zip(start,end)))
                    if mid == start or mid == end:
                        raise
                    route.extend(ridge_route(distance, start, mid)[1:] +
                                 ridge_route(distance, mid, end)[1:])
        raw = np.asarray(route, dtype=float)
        smooth = cv2.GaussianBlur(raw, (1, 7), 1.15, borderType=cv2.BORDER_REPLICATE)
        smooth[[0, -1]] = raw[[0, -1]]
        rounded = np.rint(smooth).astype(int)
        smooth[mask[rounded[:, 1], rounded[:, 0]] == 0] = raw[mask[rounded[:, 1], rounded[:, 0]] == 0]
        paths.append(smooth)
    return paths


def normalize(paths):
    raw = np.concatenate(paths)
    low, high = raw.min(axis=0), raw.max(axis=0)
    scale = .76 / max(high - low)
    points = []
    for path in paths:
        if len(path) == 1:
            path = np.repeat(path, 2, axis=0)
        lengths = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
        mapped = .5 + (path - (low + high) / 2) * scale
        points.append([{"x": round(float(x), 4), "y": round(float(y), 4),
                        "time": round(900*t/lengths[-1]) if lengths[-1] else 0}
                       for (x, y), t in zip(mapped, lengths)])
    return points


def geometry_tests(candidate, paths, mask):
    points, metadata = candidate["points"], candidate["svg"]
    before = _classify_stroke_reference(points, metadata)
    assert before["tier"] == "source_supported"
    ink_dist = np.zeros_like(mask)
    samples = []
    for path in paths:
        segments = [np.linspace(a, b, 5) for a,b in zip(path,path[1:])]
        samples.extend(np.concatenate(segments) if segments else path)
        cv2.polylines(ink_dist, [np.rint(path).astype(np.int32)], False, 1, 1)
        for x,y in np.rint(path).astype(int):
            ink_dist[y,x] = 1
    pixels = np.rint(samples).astype(int)
    outside = cv2.distanceTransform(1-mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)[pixels[:,1],pixels[:,0]]
    uncovered = cv2.distanceTransform(1-ink_dist, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)[mask.astype(bool)]
    for index, (stroke, svg_path) in enumerate(zip(points, metadata["strokes"], strict=True), 1):
        assert svg_path["order"] == index
        assert svg_path["d"] == "M " + " L ".join(f"{p['x']*100:.2f} {p['y']*100:.2f}" for p in stroke)
    result = {"svg_point_consistency": "passed",
              "max_centerline_distance_outside_ink_px": float(outside.max()),
              "source_ink_distance_to_centerline_px_p95": round(float(np.percentile(uncovered,95)),2),
              "source_ink_distance_to_centerline_px_max": round(float(uncovered.max()),2)}
    perturbed = [
        [dict(p, x=p["x"] * .93 + .032 + .003*math.sin(i/5), y=p["y"] * .95 + .024)
         for i,p in enumerate(stroke) if i % 2 == 0 or i == len(stroke)-1]
        for stroke in points
    ]
    for name, traced, expected in (
        ("positive_trace", points, True),
        ("positive_trace_resampled_and_perturbed", perturbed, True),
        ("reversed_stroke_order", points[::-1], False),
        ("reversed_stroke_direction", [stroke[::-1] for stroke in points], False),
    ):
        if name == "reversed_stroke_order" and len(points) == 1:
            result[name] = {"verdict": "not_applicable", "reason": "Only one replay segment."}
            continue
        shape, order, small = _prototype_scores(traced, points)
        status, passed, _ = _evaluate_handwriting_assessment(shape, order, before)
        result[name] = {"shape": shape, "order": order, "status": status, "accepted": passed,
                        "verdict": "passed" if passed == expected and not small else "failed"}
    return result


def replay_svg(candidate, mode="plain"):
    paths, points = candidate["svg"]["strokes"], candidate["points"]
    parts = []
    for i, (path, stroke) in enumerate(zip(paths, points)):
        color = COLORS[i % len(COLORS)] if mode == "numbered" else "#172435"
        d = html.escape(path["d"])
        is_dot = all((p["x"],p["y"]) == (stroke[0]["x"],stroke[0]["y"]) for p in stroke)
        animation = (f'<animate attributeName="visibility" from="hidden" to="visible" begin="{i}s" dur=".01s" fill="freeze"/>'
                     if mode == "animated" else "")
        visibility = ' visibility="hidden"' if animation else ""
        if is_dot:
            p = stroke[0]
            parts.append(f'<circle cx="{p["x"]*100}" cy="{p["y"]*100}" r="3" fill="{color}"{visibility}>{animation}</circle>')
        else:
            if mode == "animated":
                animation = f'<animate attributeName="stroke-dashoffset" from="1" to="0" begin="{i}s" dur=".9s" fill="freeze"/>'
            dash = ' pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"' if mode == "animated" else ""
            parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"{dash}>{animation}</path>')
        if mode == "numbered":
            start = stroke[0]
            x,y = start["x"]*100, start["y"]*100
            parts.append(f'<circle cx="{x+i*3}" cy="{y-i*3}" r="3.2" fill="{color}"/><text x="{x+i*3}" y="{y-i*3}" fill="white" text-anchor="middle" dominant-baseline="central" font-size="4">{i+1}</text>')
            if not is_dot:
                j = len(stroke)//2
                a,b = stroke[max(0,j-2)],stroke[min(len(stroke)-1,j+2)]
                angle = math.degrees(math.atan2(b["y"]-a["y"],b["x"]-a["x"]))
                p = stroke[j]
                parts.append(f'<path d="M -4 -2 L 1 0 L -4 2 Z" fill="{color}" stroke="white" stroke-width=".5" transform="translate({p["x"]*100} {p["y"]*100}) rotate({angle})"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{"".join(parts)}</svg>'


def stage(folder, entry, source, asset, gates):
    data = asset.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if hashlib.sha1(data).hexdigest() != source["Sha1"]:
        raise ValueError("Cached GIF checksum mismatch.")
    ok, animation = cv2.imreadanimation(str(asset))
    if not ok:
        raise ValueError("The cached GIF could not be decoded.")
    frame = animation.frames[-1]
    mask = (cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY) < 110).astype("uint8")
    paths = extract(mask, gates)
    points = normalize(paths)
    metadata = {
        "source": "Wikimedia Commons progressive Tamil handwriting animation",
        "source_file": asset.relative_to(BACKEND.parent).as_posix(),
        "source_url": source["Page"], "source_author": source["Creator"],
        "source_asset_sha256": digest, "license": "CC BY-SA 3.0 Unported",
        "license_url": LICENSE_URL, "derivative_license": "CC BY-SA 3.0 Unported",
        "attribution": f'Adapted from {source["Page"]} by {source["Creator"]}. Final raster ink converted to smoothed centerlines, normalized, and replayed with synthetic timing.',
        "character_id": entry["character_id"], "provenance_status": "verified",
        "instructional_review_status": "pending", "visual_review_status": "pending",
        "watermark_align_to_reference": True,
    }
    candidate = source_candidate("ta", entry["character"], points, metadata, entry["character_id"], "Pinned Wikimedia Commons GIF")
    tests = geometry_tests(candidate, paths, mask)
    uncertainty = {
        "geometry": "Pixel resolution limits centerline precision at joins, retraces and ends. Inspect source and candidate overlays.",
        "pen_lift": "Replay segments follow visible progression and restarts. The GIF cannot resolve every physical pen lift at joined or retraced ink.",
    }
    if entry["character_id"] == 112:
        uncertainty["pen_lift"] += " The two dots are stationary contacts, with no source-supported travel direction."
    if tests["max_centerline_distance_outside_ink_px"] > 1 or tests["source_ink_distance_to_centerline_px_p95"] > 5.5:
        uncertainty["geometry"] += " Raster comparison flagged this reconstruction. Inspect before any import."
        candidate["candidate_status"] = "geometry_unresolved_pending_review"
    write_json(folder / "source-trace.json", {"source": source, "sha256": digest, "frame_count": len(animation.frames),
               "branch_gates": gates, "canonical_source_pixels": [p.round(5).tolist() for p in paths], **uncertainty})
    write_json(folder / "staged-candidate.json", candidate)
    image = render(points)
    cv2.imwrite(str(folder / "cnn-canvas.png"), image)
    ok, png = cv2.imencode(".png", image)
    try:
        assert ok
        cnn = model_registry.predict(image_input=base64.b64encode(png).decode("ascii"),
                                     script_code="ta", expected_character=entry["character"])
    except Exception as error:
        cnn = {"status": "error", "message": str(error)}
    write_json(folder / "cnn-result.json", cnn)
    positive = tests["positive_trace"]
    status, passed, _ = _evaluate_handwriting_assessment(
        positive["shape"], positive["order"], _classify_stroke_reference(points, candidate["svg"]),
        cnn, entry["character"])
    tests["positive_trace_with_cnn"] = {"status": status, "accepted": passed,
                                      "verdict": "passed" if passed and cnn.get("is_match") else "failed"}
    write_json(folder / "geometry-tests.json", tests)
    (folder / "numbered.svg").write_text(replay_svg(candidate,"numbered"), encoding="utf-8")
    (folder / "stroke-preview.svg").write_text(replay_svg(candidate,"animated"), encoding="utf-8")
    (folder / "corrected.svg").write_text(replay_svg(candidate), encoding="utf-8")
    overlay = frame[:,:,:3].copy()
    for i,path in enumerate(paths):
        color = tuple(bytes.fromhex(COLORS[i % len(COLORS)][1:])[::-1])
        coords = np.rint(path).astype(np.int32)
        cv2.polylines(overlay, [coords], False, color, 1, cv2.LINE_AA)
        cv2.circle(overlay, coords[0], 1, color, -1)
    cv2.imwrite(str(folder / "source-overlay.png"), cv2.resize(overlay, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST))
    return candidate, tests, cnn, uncertainty


def gallery(cards):
    css = """
    body{font:1rem/1.5 system-ui;color:#172435;max-width:78rem;margin:2rem auto;padding:0 1rem;background:#f5f7fa}
    article{margin:1rem 0;padding:1rem;background:white;border:1px solid #bdc9d6;border-radius:.6rem}
    h2{margin:.1rem 0}.panels{display:grid;grid-template-columns:repeat(auto-fit,minmax(9rem,1fr));gap:.7rem}
    figure{margin:0;background:#f6f8fb;border-radius:.4rem;padding:.45rem}figcaption{font-weight:600}
    figure img{width:100%;height:10rem;object-fit:contain}img.raster{image-rendering:pixelated}
    button{font:inherit;margin:.4rem 0}a{color:#194d91}
    """
    (OUTPUT / "visual-review.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Tamil vowel stroke review</title><style>' + css + '</style><h1>Tamil vowel stroke review</h1>'
        '<p>Visual review, instructor review and production import approval are pending.</p>' + "".join(cards)
        + '<script>function replay(button){const img=button.previousElementSibling;img.src=img.src.split("?")[0]+"?replay="+Date.now()}</script></html>',
        encoding="utf-8")


def panel(label, path, raster=False, replay=False):
    klass = ' class="raster"' if raster else ""
    button = '<button type="button" onclick="replay(this)">Replay</button>' if replay else ""
    return f'<figure><figcaption>{label}</figcaption><img{klass} src="{html.escape(path)}" alt="{label}">{button}</figure>'


def main():
    OUTPUT.mkdir(exist_ok=True)
    sources = {s["File"]: s for s in read_json(CACHE / "sources.json") if s["File"].startswith("tamil-")}
    sources["Writing_Tamil_6.gif"] = {"Creator": "தகவலுழவன் (Info-farmer)", "License": "CC BY-SA 3.0",
        "Page": "https://commons.wikimedia.org/wiki/File:Writing_Tamil_6.gif", "Sha1": "b3a13d530ffbd099e06ebecd93dd0e1fbe0a702a"}
    manifest = read_json(ROOT / "batch-review-20261126-000050" / "review_manifest.json")
    entries = {e["character_id"]: e for e in manifest["entries"] if e["script_code"] == "ta"}
    pilot = read_json(PILOT / "staged-candidate.json")
    pilot_cnn = read_json(PILOT / "cnn-result.json")
    (OUTPUT / "25-corrected.svg").write_text(replay_svg(pilot), encoding="utf-8")
    (OUTPUT / "25-numbered.svg").write_text(replay_svg(pilot,"numbered"), encoding="utf-8")
    cards = ['<article><h2 lang="ta">அ (ID 25)</h2><p>Visual and instructor review pending. '
             '<a href="../a-id25-review/visual-review.html">Open existing review</a></p><div class="panels">'
             + panel("Cached handwriting animation","../Writing_Tamil_2.gif",True)
             + panel("Corrected centerline","25-corrected.svg")
             + panel("Numbered order and direction","25-numbered.svg") +
             '<figure><figcaption>Existing staged replay</figcaption><video width="240" controls playsinline src="../a-id25-review/stroke-preview.mp4"></video></figure></div></article>']
    summary = [{"id":25,"character":pilot["character"],"geometry":"existing_candidate_pending_review",
                "cnn": {"match": pilot_cnn.get("is_match"), "predicted": pilot_cnn.get("predicted_character"),
                        "confidence":pilot_cnn.get("confidence")}}]
    for char_id, slug, gates in SPECS:
        entry = entries[char_id]
        folder = OUTPUT / f"{char_id}-{slug}"
        folder.mkdir(exist_ok=True)
        asset = HERE / "Writing_Tamil_6.gif" if slug == "u" else CACHE / f"tamil-{slug}.gif"
        source = sources[asset.name]
        visuals = panel("Cached source animation", Path(os.path.relpath(asset, OUTPUT)).as_posix(), True)
        try:
            candidate, tests, cnn, uncertainty = stage(folder, entry, source, asset, gates)
        except ValueError as error:
            reason = str(error)
            write_json(folder / "unresolved.json", {"character_id":char_id,"character":entry["character"],"source":source,"geometry":reason,
                "pen_lift":"Candidate not staged.", "cnn":"Not run."})
            details = f'<p>Geometry unresolved. {html.escape(reason)}.</p>'
            summary.append({"id":char_id,"character":entry["character"],"geometry":"unresolved","reason":reason})
        else:
            old_unresolved = folder / "unresolved.json"
            if old_unresolved.exists():
                old_unresolved.unlink()
            relative = folder.name
            visuals += panel("Corrected centerline",f"{relative}/corrected.svg")
            visuals += panel("Centerline on source",f"{relative}/source-overlay.png",True)
            visuals += panel("Numbered order and direction",f"{relative}/numbered.svg")
            visuals += panel("Animated stroke preview",f"{relative}/stroke-preview.svg",replay=True)
            verdicts = {k:v["verdict"] for k,v in tests.items() if isinstance(v,dict)}
            cnn_status = {"match": cnn.get("is_match", False), "predicted": cnn.get("predicted_character"),
                          "confidence": cnn.get("confidence"), "status": cnn.get("status")}
            cnn_label = cnn.get("predicted_character") or cnn.get("status","unknown")
            result_label = "match" if cnn_status["match"] else "retry"
            test_label = ", ".join(f'{k.replace("_", " ")}: {v.replace("_", " ")}' for k,v in verdicts.items()
                                   if k != "positive_trace_with_cnn")
            links = " · ".join(f'<a href="{relative}/{file}">{label}</a>' for file,label in (
                ("staged-candidate.json","Candidate JSON"),("source-trace.json","Source trace and uncertainties"),
                ("geometry-tests.json","Geometry and rejection tests"),("cnn-result.json","CNN result"),("cnn-canvas.png","CNN input")))
            details = (f'<p>{html.escape(uncertainty["geometry"])}</p><p>{html.escape(uncertainty["pen_lift"])}</p>'
                       f'<p>{html.escape(test_label)}.</p><p>CNN {result_label} · <span lang="ta">{html.escape(cnn_label)}</span>'
                       f' · confidence {cnn_status["confidence"]}%.</p><p>{links}</p>')
            summary.append({"id":char_id,"character":entry["character"],"geometry":candidate["candidate_status"],
                            "pen_lift":uncertainty["pen_lift"],"tests":verdicts,"cnn":cnn_status})
        attribution = f'<a href="{source["Page"]}">Wikimedia Commons source by {html.escape(source["Creator"])}</a> · <a href="{LICENSE_URL}">CC BY-SA 3.0 Unported</a>'
        cards.append(f'<article><h2><span lang="ta">{entry["character"]}</span> (ID {char_id})</h2>'
                     f'<div class="panels">{visuals}</div>{details}<p>{attribution}</p></article>')
        print(ascii(summary[-1]), flush=True)
    gallery(cards)
    write_json(OUTPUT / "review-summary.json", summary)


if __name__ == "__main__":
    main()

