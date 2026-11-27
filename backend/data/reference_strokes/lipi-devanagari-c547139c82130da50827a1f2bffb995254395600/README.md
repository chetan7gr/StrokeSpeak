# Lipi Devanagari reference points

This pinned source revision contains the small `weights.safetensors` artifact used to render hand-drawn Devanagari pen paths. The model card states that the pen-hand Devanagari centerlines were drawn by hand in writing order and are released under Creative Commons Attribution 4.0 International (CC BY 4.0).

- Work: **Lipi · लिपि: Devanagari calligraphy with no training**
- Creator/source account: `Vishwasaidev`
- Source: https://huggingface.co/Vishwasaidev/lipi
- Pinned revision: `c547139c82130da50827a1f2bffb995254395600`
- Pinned model artifact: `https://huggingface.co/Vishwasaidev/lipi/resolve/c547139c82130da50827a1f2bffb995254395600/weights.safetensors`
- License: CC BY 4.0; see `CC-BY-4.0.txt` and the full `MODEL_CARD.md` in this folder.
- This derived data currently imports only the exact standalone glyphs अ, इ, उ, ऊ, ऋ, ए found in the source index. Other vowels formed compositionally are not claimed as exact-source paths.

StrokeSpeak extracts the pinned model's point sequences and stroke boundaries, centers and scales each glyph while preserving aspect ratio, and writes normalized point/SVG paths. The source has no timestamps; StrokeSpeak assigns 50 ms intervals for playback only. This is an adaptation; source attribution is recorded in each database row. The glyph paths have not been independently reviewed by a Sanskrit instructor. The standalone glyph अ is also used in the Sanskrit tutor, so review is required before generating its teaching video.
