# Simplified Chinese reference data

Stroke geometry for these nine public Simplified Chinese starter glyphs is copied and transformed from pinned `hanzi-writer-data` version `2.0.1`. The package identifies its upstream as Make Me a Hanzi and licenses the data under the Arphic Public License (APL).

- Upstream repository: https://github.com/chanind/hanzi-writer-data
- Pinned package: https://cdn.jsdelivr.net/npm/hanzi-writer-data@2.0.1/
- License: Arphic Public License; the complete `ARPHICPL.TXT` is vendored beside the data.
- Public CNN characters: 一, 二, 三, 人, 大, 口, 日, 月, 山.

## Coordinate convention

The source `medians` are Y-up coordinates. StrokeSpeak renders references in SVG and Canvas coordinates, where Y increases downward. The importer therefore centers and uniformly scales the source bounds, preserves the source stroke and point sequence, and inverts Y exactly once using `canvas_y = 0.5 - (source_y - center_y) * scale`. This keeps source directions and writing order intact while producing correctly oriented glyphs. SVG paths are generated from the same normalized points.

The source does not include timestamps. StrokeSpeak assigns 50 ms per source point as playback timing; these are placeholders, not measured pen speed.

Imported rows are `source_attributed` and remain `instructional_review_status: pending` until a qualified Chinese instructor reviews the exact geometry. Source attribution and successful rendering do not imply independent teaching certification.

The importer is read-only by default. Before an explicit `--apply`, it verifies the pinned version, license, exact source checksums, expected character IDs, production metadata hashes, and stroke counts. A successful application creates a timestamped exact before-image and verifies all nine rows inside the same transaction before commit. Restore both `reference_strokes` and `reference_strokes_svg` from that backup by row ID if rollback is required.