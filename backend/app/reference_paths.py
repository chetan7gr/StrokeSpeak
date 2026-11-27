"""Stable fingerprints for the reference geometry that an instructor reviews."""

import hashlib
import json
import math


def reference_path_fingerprint(stroke_data, metadata=None):
    """Hash normalized point order plus any parallel SVG guide geometry.

    Capture timestamps are deliberately excluded: they affect replay timing, not
    the glyph shape or stroke-order decision. Coordinates are rounded to 1e-6.
    """
    if isinstance(stroke_data, str):
        stroke_data = json.loads(stroke_data)
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    if not isinstance(metadata, dict):
        metadata = {}

    normalized_strokes = []
    for stroke in stroke_data or []:
        if not isinstance(stroke, (list, tuple)):
            raise ValueError("Reference stroke must be a list of points")
        normalized_points = []
        for point in stroke:
            x = float(point["x"])
            y = float(point["y"])
            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError("Reference coordinates must be finite")
            x = round(x, 6)
            y = round(y, 6)
            normalized_points.append([0.0 if x == 0 else x, 0.0 if y == 0 else y])
        normalized_strokes.append(normalized_points)

    svg_paths = []
    for path in metadata.get("strokes", []) or []:
        if not isinstance(path, dict):
            continue
        try:
            order = int(path.get("order", len(svg_paths) + 1))
        except (TypeError, ValueError):
            order = str(path.get("order"))
        svg_paths.append({
            "order": order,
            "path_id": path.get("path_id"),
            "d": path.get("d", ""),
        })

    canonical = json.dumps(
        {
            "points": normalized_strokes,
            "svg_view_box": metadata.get("viewBox"),
            "svg_paths": svg_paths,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
