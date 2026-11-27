"""Build the ID 25 visual review from cached files, without accessing the database."""
import base64
from heapq import heappop, heappush
import html
import json
from pathlib import Path
import sys

import av
import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[3]
sys.path[:0] = [str(BACKEND / "scripts"), str(BACKEND)]
from correct_tamil_reference_strokes import REFERENCE_FILE, SOURCE_FILE, build_reference
from stage_external_stroke_candidates import source_candidate
from main import _classify_stroke_reference, _evaluate_handwriting_assessment, _prototype_scores, model_registry

# Gates identify which ink branch to follow. Interior samples come from the
# distance ridge, including at the outer bowl/bar crossing in frame 10.
GATES = (
    ((54, 5), (62, 11), (63, 18), (58, 25), (51, 26), (44, 22), (43, 14), (46, 8), (54, 5)),
    ((54, 5), (64, 5), (74, 10), (80, 18), (82, 27), (81, 35), (77, 43),
     (69, 50), (58, 54), (44, 56), (30, 55), (17, 51), (8, 46), (4, 40), (5, 36), (11, 35)),
)
LABELS = (
    "Clockwise upper loop",
    "Sweep right and down around the bowl, then curl right into the bar",
    "Left to right along the bar, then up the stem",
    "Down the right stem",
)
UNCERTAINTY = (
    "The raster resolves branch order and direction. Covered ink does not resolve exact endpoints at the "
    "upper join or left return, or whether the pen physically lifts at each shared endpoint. "
    "The four replay segments follow the visible arrow phases. Playback timing is synthetic."
)
COLORS = ("#165ec2", "#b32d4d", "#067348", "#7140a7")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ridge_route(distance, start, end):
    """Minimize travel cost weighted by distance from the visible ink edge."""
    a, b = np.array(start), np.array(end)
    delta = b - a
    queue = [(0.0, start)]
    costs = {start: 0.0}
    previous = {}
    while queue:
        cost, current = heappop(queue)
        if current == end:
            route = [end]
            while route[-1] != start:
                route.append(previous[route[-1]])
            return route[::-1]
        if cost > costs[current]:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            x, y = neighbor = (current[0] + dx, current[1] + dy)
            if not (0 <= y < distance.shape[0] and 0 <= x < distance.shape[1]) or distance[y, x] == 0:
                continue
            pos = np.array(neighbor) - a
            projection = np.clip(np.dot(pos, delta) / np.dot(delta, delta), 0, 1)
            if np.linalg.norm(pos - projection * delta) > 4:
                continue
            step = np.hypot(dx, dy) / (0.45 + min(distance[y, x], distance[current[1], current[0]])) ** 2
            new_cost = cost + step
            if new_cost < costs.get(neighbor, float("inf")):
                costs[neighbor] = new_cost
                previous[neighbor] = current
                heappush(queue, (new_cost, neighbor))
    raise ValueError(f"No source ink route between {start} and {end}")


def extract():
    ok, animation = cv2.imreadanimation(str(SOURCE_FILE))
    assert ok and len(animation.frames) == 10
    gray = cv2.cvtColor(animation.frames[-1], cv2.COLOR_BGRA2GRAY)
    mask = (gray < 110).astype("uint8")
    mask[:, 102:] = 0  # Narrow band beyond the stem, outside the character.
    distance = cv2.distanceTransform(mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    strokes = []
    for gates in GATES:
        route = [gates[0]]
        for start, end in zip(gates, gates[1:]):
            route.extend(ridge_route(distance, start, end)[1:])
        route = np.asarray(route, dtype=np.float64)
        smoothed = cv2.GaussianBlur(route, (1, 9), 1.55, borderType=cv2.BORDER_REPLICATE)
        smoothed[[0, -1]] = route[[0, -1]]
        strokes.append(smoothed.round(4).tolist())
    # The ridge merges at intersections. Measure the straight runs in their
    # unoccluded portions and continue their measured axes through the joins.
    # Measure the bar between the left turn and the bowl crossing.
    bar_y = float(np.median(np.where(mask[30:41, 18:72])[0]) + 30)
    stem_x = float(np.median(np.where(mask[8:30, 90:101])[1]) + 90)
    bar_start, stem_top, stem_bottom = (11, bar_y), (stem_x, 6), (stem_x, 60)
    strokes[-1][-1] = list(bar_start)
    strokes.extend([
        [bar_start, (stem_x, bar_y), stem_top],
        [stem_top, stem_bottom],
    ])
    for stroke in strokes:
        for start, end in zip(stroke, stroke[1:]):
            samples = max(2, int(np.linalg.norm(np.subtract(end, start)) * 4) + 1)
            pixels = np.rint(np.linspace(start, end, samples)).astype(int)
            assert np.all(mask[pixels[:, 1], pixels[:, 0]]), (start, end)
    return strokes


def make_candidate():
    config = read_json(REFERENCE_FILE)
    config["stroke_labels"] = list(LABELS)
    config["stroke_anchors"] = [{"order": i, "points": s} for i, s in enumerate(extract(), 1)]
    config["trace_method"] = (
        "Frame 10 grayscale ink mask, distance-transform ridge routing with branch gates selected from "
        "the progressive arrows in frames 1–9, then Gaussian smoothing within the ink. The bar and stem "
        "follow median ink axes measured away from the crossings. " + UNCERTAINTY
    )
    raw_points, metadata, _ = build_reference(config)  # Pin source and reuse the importer transform.
    metadata["review_uncertainty"] = UNCERTAINTY
    metadata["attribution"] = (
        "Adapted from Writing Tamil 2.gif by Info-farmer (Wikimedia Commons), CC BY-SA 3.0 Unported. "
        "The raster ink was converted to smoothed centerlines with new playback timing. "
        "The adapted stroke data and visual previews retain CC BY-SA 3.0 Unported."
    )
    return config, raw_points, metadata


def stage(raw_points, metadata):
    points = [[dict(p, x=p["x"] / 100, y=p["y"] / 100) for p in s] for s in raw_points]
    return source_candidate("ta", "\u0b85", points, metadata, 25, "Pinned Wikimedia Commons animation")


def render(strokes, width=700, height=320, area=320, thickness=10):
    # Match the learner canvas dimensions, black ink, and round 10px pen.
    factor = 3
    canvas = np.full((height * factor, width * factor, 3), 255, np.uint8)
    for stroke in strokes:
        coords = np.array([[(width-area)/2 + p["x"]*area, (height-area)/2 + p["y"]*area] for p in stroke])
        if not len(coords):
            continue
        pts = np.rint(coords * factor).astype(np.int32)
        cv2.polylines(canvas, [pts], False, (0, 0, 0), thickness * factor)
        for point in pts:
            cv2.circle(canvas, point, thickness * factor // 2, (0, 0, 0), -1)
    return cv2.resize(canvas, (width, height), interpolation=cv2.INTER_AREA)


def validate(candidate):
    points = candidate["points"]
    metadata = candidate["svg"]
    classification = _classify_stroke_reference(points, metadata)
    assert classification["tier"] == "source_supported"
    perturbed = [
        [dict(p, x=p["x"] * 0.92 + 0.035 + 0.005*np.sin(i/5), y=p["y"] * 0.95 + 0.02)
         for i, p in enumerate(stroke) if i % 2 == 0 or i == len(stroke) - 1]
        for stroke in points
    ]
    scores = {}
    for name, strokes, expected in (
        ("positive_trace", points, True),
        ("positive_trace_resampled_and_perturbed", perturbed, True),
        ("reversed_stroke_order", points[::-1], False),
        ("reversed_stroke_direction", [stroke[::-1] for stroke in points], False),
    ):
        shape, order, too_small = _prototype_scores(strokes, points)
        status, passed, _ = _evaluate_handwriting_assessment(shape, order, classification)
        scores[name] = {"shape": shape, "order": order, "status": status, "passed": passed}
        assert not too_small and passed is expected, scores
        if not expected:
            assert status == "stroke_order_retry", scores
    for order, (stroke, path) in enumerate(zip(points, metadata["strokes"], strict=True), 1):
        assert path["order"] == order
        assert path["d"] == "M " + " L ".join(f"{p['x'] * 100:.2f} {p['y'] * 100:.2f}" for p in stroke)
    scores["svg_point_consistency"] = "passed"
    image = render(points)
    assert cv2.imwrite(str(HERE / "cnn-canvas.png"), image)
    ok, png = cv2.imencode(".png", image)
    assert ok
    try:
        cnn = model_registry.predict(
            image_input=base64.b64encode(png).decode("ascii"), script_code="ta", expected_character="\u0b85"
        )
    except Exception as error:
        cnn = {"status": "error", "message": str(error)}
    write_json(HERE / "geometry-tests.json", scores)
    write_json(HERE / "cnn-result.json", cnn)


def movie(points):
    output = str(HERE / "stroke-preview.mp4")
    with av.open(output, "w", options={"movflags": "+faststart"}) as video:
        stream = video.add_stream("libx264", rate=30)
        stream.width, stream.height, stream.pix_fmt = 700, 320, "yuv420p"

        def emit(image, count=1):
            for _ in range(count):
                frame = av.VideoFrame.from_ndarray(image, format="bgr24")
                for packet in stream.encode(frame):
                    video.mux(packet)

        emit(render([]), 12)
        for i, stroke in enumerate(points):
            for frame in range(1, 28):
                available = [p for p in stroke if p["time"] <= frame * 900 / 27]
                emit(render(points[:i] + [available]))
            emit(render(points[:i + 1]), 8)
        emit(render(points), 30)
        for packet in stream.encode():
            video.mux(packet)
    with av.open(output) as video:
        assert sum(1 for _ in video.decode(video=0)) == 182


def svg(paths, numbered_points=None, viewbox="0 0 100 100"):
    contents = []
    for i, path in enumerate(paths):
        color = COLORS[i] if numbered_points else "#182532"
        dash = ' stroke-dasharray="2.1 2.1"' if numbered_points and i == 3 else ''
        contents.append(f'<path d="{html.escape(path["d"], quote=True)}" stroke="{color}"{dash}/>')
    if numbered_points:
        for i, (stroke, fraction) in enumerate(zip(numbered_points, (0.35, 0.58, 0.5, 0.72))):
            j = int(len(stroke) * fraction)
            a, b = stroke[j], stroke[j+3]
            x, y = 100*b["x"], 100*b["y"]
            angle = np.degrees(np.arctan2(b["y"]-a["y"], b["x"]-a["x"]))
            color = COLORS[i]
            contents.append(f'<path d="M -5 -3 L 0 0 L -5 3 Z" style="fill:{color};stroke:white;stroke-width:.6" transform="translate({x} {y}) rotate({angle})"/>')
            bx, by = ((46, 25), (31, 80), (50, 51), (94, 65))[i]
            contents.append(f'<circle cx="{bx}" cy="{by}" r="3.1" fill="{color}"/><text x="{bx}" y="{by+.2}">{i+1}</text>')
    return f'<svg viewBox="{html.escape(viewbox, quote=True)}" aria-hidden="true">{"".join(contents)}</svg>'


def gallery(candidate):
    snapshot = HERE.parents[1] / "batch-review-20261126-000050" / "review_manifest.json"
    baseline = next(e["current"]["svg_metadata"] for e in read_json(snapshot)["entries"] if e["character_id"] == 25)
    source = '<img src="../Writing_Tamil_2.gif" alt="Cached 10-frame handwriting animation with directional arrows">'
    corrected = svg(candidate["svg"]["strokes"])
    video = '<video controls playsinline preload="metadata" src="stroke-preview.mp4"></video>'
    panels = [
        ("Authentic source animation", source),
        ("Existing displayed geometry", svg(baseline["strokes"], viewbox=baseline["viewBox"])),
        ("Corrected geometry", corrected),
        ("Numbered stroke order and direction", svg(candidate["svg"]["strokes"], numbered_points=candidate["points"])),
        ("Animated stroke replay", video),
    ]
    cards = "".join(f"<figure><figcaption>{title}</figcaption>{visual}</figure>" for title, visual in panels)
    labels = "".join(f"<li>{html.escape(label)}</li>" for label in LABELS)
    page = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tamil handwriting review</title>
<style>
body{{font:1rem/1.5 system-ui;color:#182532;max-width:72rem;margin:2rem auto;padding:0 1rem}}
main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,19rem),1fr));gap:1rem}}
figure{{margin:0;border:1px solid #bcc8d3;border-radius:.5rem;overflow:hidden;background:white}}
figcaption{{padding:.55rem;background:#eef2f6;font-weight:600}}
svg,img,video{{display:block;width:100%;height:15rem;object-fit:contain}}
svg path{{fill:none;stroke-width:2.8;stroke-linecap:round;stroke-linejoin:round}}
svg text{{fill:white;font:bold 4px system-ui;text-anchor:middle;dominant-baseline:middle}}
</style>
<h1>Tamil <span lang="ta">&#2949;</span> (ID 25)</h1>
<p>Visual and instructor review pending.</p>
<main>{cards}</main>
<ol>{labels}</ol>
<p>{html.escape(UNCERTAINTY)}</p>
<p>The existing display path is from the saved ID 25 review snapshot dated November 26.</p>
<p>Adapted from <a href="https://commons.wikimedia.org/wiki/File:Writing_Tamil_2.gif">Writing Tamil 2.gif by Info-farmer</a>.
The source and adapted geometry and previews are licensed under <a href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0 Unported</a>.</p>
</html>"""
    (HERE / "visual-review.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    config, points, metadata = make_candidate()
    candidate = stage(points, metadata)
    write_json(HERE / "source-trace.json", config)
    write_json(HERE / "staged-candidate.json", candidate)
    validate(candidate)
    movie(candidate["points"])
    gallery(candidate)
