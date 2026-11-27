# KanjiVG reference stroke data attribution

Stroke-order data in this folder is sourced from the KanjiVG project by Ulrich Apel and contributors.

- Project: https://github.com/KanjiVG/kanjivg
- Pinned revision: `610091ce618cf757ed1357a8954cd65283e015d6`
- License: Creative Commons Attribution-Share Alike 3.0 (CC BY-SA 3.0)
- License text: see [`COPYING`](./COPYING) and https://creativecommons.org/licenses/by-sa/3.0/
- Original SVG files are retained unchanged under [`kanji/`](./kanji/).
- The JSON stroke metadata in MySQL preserves each original path `d` string and viewBox. Sampled points used by the geometric prototype are adapted from those paths and are provided under the same CC BY-SA 3.0 terms.

Attribution text for the project report/UI:

> Stroke-order paths are from KanjiVG by Ulrich Apel and contributors, licensed under Creative Commons Attribution-Share Alike 3.0 (CC BY-SA 3.0). Source files are identified per character in `reference_strokes_svg` and retained in `backend/assets/kanjivg/kanji/`. The original SVG paths are preserved; the normalized point sequences are derived for StrokeSpeak's geometric prototype.

## Basic Japanese Kana coverage

The pinned source set now includes all 46 basic Hiragana and 46 basic Katakana characters. Each character is matched to its Unicode-named SVG from the pinned revision above. The original SVG files remain unchanged under `kanji/`; the database metadata identifies the source filename and original stroke paths for each character.
