# Fude kana source snapshot
Upstream: https://github.com/karimghezali/fude-kana-data
Resolved immutable commit: ab69a27e2f5a5125ac89b5f13a1b0f0e318d5319
Upstream data derived from KanjiVG by Ulrich Apel, CC BY-SA 3.0.
This folder contains only the ten Japanese Hiragana classes in the current Hiragana CNN metadata.
The staging script preserves stroke sequence and resampled point order, normalizes with a uniform scale, assigns application-only 50 ms point timestamps, and generates SVG polyline paths from those same normalized points. No database import is performed by the staging tool.
See NOTICE and LICENSE for required attribution and share-alike terms.