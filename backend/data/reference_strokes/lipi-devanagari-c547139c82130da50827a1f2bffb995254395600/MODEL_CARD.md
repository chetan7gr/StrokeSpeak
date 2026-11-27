---
license: cc-by-4.0
pipeline_tag: text-to-image
library_name: numpy
tags:
  - calligraphy
  - no-training
  - hand-written-weights
  - devanagari
  - hindi
  - marathi
  - sanskrit
  - interpretability
---

# Lipi · लिपि: Devanagari calligraphy with no training

Lipi writes Hindi, Marathi and Sanskrit in eight hands. Two are pen hands: letters drawn by hand for Lipi, stroke by
stroke, and written with a hand-set reed pen (lekhani) or brush (tulika). Six are type hands: the outlines of open
Devanagari fonts, joined by HarfBuzz and inked onto paper. Nothing in it was learned.

**Try it:**
- Web app: https://lipi-devanagari-f797919c0a6d.herokuapp.com/
- In your browser (Pyodide): [Space: Vishwasaidev/lipi](https://huggingface.co/spaces/Vishwasaidev/lipi)
- Weights + model card: [Vishwasaidev/lipi](https://huggingface.co/Vishwasaidev/lipi)

Lipi is a sister of [Quill](https://huggingface.co/Vishwasaidev/quill), the Latin and kanji calligraphy model. The
two are kept apart so each keeps its own licences.

![demo](docs/demo.png)

```bash
python server.py                  # web page on http://127.0.0.1:8793
python lipi.py "सत्यमेव जयते" --style lekhani --initial --seal ॐ
python lipi.py "महाराष्ट्र माझा" --style tiro
python lipi.py "वक्रतुण्ड महाकाय" --style tulika --animate
python lipi.py --demo
python export_weights.py          # data/devanagari + Hershey futural -> weights.safetensors
```

Requires `numpy`, `pillow`, `fonttools` and `uharfbuzz`.

## The hands

| Style | Kind | Look | Letters from |
|---|---|---|---|
| `lekhani` | pen | broad reed pen: bold headline and horizontals | drawn by hand for Lipi |
| `tulika` | pen | brush that presses in and lifts off | drawn by hand for Lipi |
| `kalam` | type | everyday handwriting | Kalam, Indian Type Foundry |
| `tiro` | type | book type with Marathi letterforms (अ ल श झ) | Tiro Devanagari Marathi, Tiro Typeworks |
| `rozha` | type | heavy, high-contrast poster type | Rozha One, Indian Type Foundry |
| `amita` | type | calligraphic thick and thin | Amita, Eduardo Tunni |
| `tillana` | type | flowing, slanted hand | Tillana, Indian Type Foundry |
| `jaini` | type | old manuscript style | Jaini, EkType |

`--size` is the body height in pixels, headline to baseline, for every hand. Inks: `iron`, `black`, `sepia`, `sumi`,
`red`, `blue`, `green`, `gold`, `vermilion`.

Extras:
- `--initial` draws the first syllable about twice the size in red, hanging from the headline.
- `--seal` carves ॐ or श्री (one word, headline and all) or up to 4 Latin letters into a red seal stamp.
- `--animate` writes an animated WebP. It starts on blank paper. Pen hands write stroke by stroke and draw each
  word's headline last; type hands ink each syllable from left to right.
- `--flourish` adds a tapered swash under the text.

## How it works

| Layer | Pen hands | Type hands |
|---|---|---|
| letters | hand-drawn centrelines (`glyphs.deva.*` in `weights.safetensors`) | font outlines, read with fontTools |
| shaping | fixed rules in `devanagari.py` (below) | HarfBuzz: the font's own OpenType rules |
| smooth / pen | Chaikin corner cutting, then a broad nib or a brush swept along each stroke as convex shapes | none: the outline is the shape |
| raster | half-plane neurons `d - nx*x - ny*y` per pixel, min over a shape's edges, max over shapes | nonzero-winding scanline fill, 4 x 4 samples per pixel |
| ink | ink density times paper texture, over cream paper; red initial and seal on their own ink layers | same |

In the browser Space, Pyodide has fontTools but not uharfbuzz, so the same HarfBuzz runs as harfbuzzjs (WebAssembly)
and hands its results to the Python.

### The hand-drawn letters

The strokes in `data/devanagari/strokes.txt` were drawn by hand for Lipi, point by point on a grid, in writing order:
34 consonants (including ळ), the vowels अ इ उ ऊ ऋ ए (and from them आ ई ओ औ ऐ ऑ ॲ), the vowel signs, ं ँ ः ् ़,
ॐ ऽ । ॥, the digits ०-९ and the shapes क्ष त्र ज्ञ श्र. No open data set of Devanagari pen strokes with a clear licence
exists. A system font served only as a visual guide while drawing.

`devanagari.py` shapes text for the pen hands with fixed rules:
- **ि** is written before the consonant cluster it follows in the text, and its loop reaches over to that cluster.
- **Half forms:** a consonant whose bar is its right edge drops the bar before another consonant (स्त, न्य, श्व).
  क and फ have their own half shapes.
- **Stacking:** a consonant with no bar (द ट ड ह ...) carries the next one small underneath, the Sanskrit way
  (द्ध, द्व, द्य, ट्ट, ह्न, ह्म).
- **Reph** (र्म) is a hook above the end of the syllable; **rakar** (प्र, क्र) is a tick off the bar, or a caret
  below a letter with no bar (ट्र).
- Vowel signs and ं ँ ः ् ़ hang off the consonant's bar. ँ becomes ं when a vowel sign already sits above.
- The headline is drawn once per word, after its letters.
- Anything else, such as a stack of three consonants, keeps a visible virama. Latin letters, digits and punctuation
  use the Hershey futural letters.

## Data and licences

Each part keeps its own licence:

- **Hand-drawn Devanagari strokes** (`data/devanagari/strokes.txt`, and the `glyphs.deva.*` tensors in
  `weights.safetensors`): drawn for Lipi, released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- **Fonts** (`fonts/`): each under the [SIL Open Font License 1.1](https://openfontlicense.org), with its copyright
  notice in the `OFL.txt` beside it. Kalam, Rozha One and Tillana: Indian Type Foundry. Tiro Devanagari Marathi: The
  Indigo Project Authors (Tiro Typeworks). Amita: Eduardo Tunni (with Modular Infotech and Astigmatic). Jaini: The
  Jaini Project Authors (EkType). They are unmodified and are not part of `weights.safetensors`.
- **Hershey futural letters**: public domain (A. V. Hershey, US National Bureau of Standards, 1967), extracted from
  the MIT-licensed `Hershey-Fonts` package.
- **Code**: CC BY 4.0, the same as the strokes.

## Limits

- **The type hands' letter shapes are the fonts' designers' work.** Lipi only joins, places and inks them. They are
  not written stroke by stroke, so their animation is an ink reveal, not stroke order.
- **The pen hands are one hand, drawn once,** in a modern print-like form. Marathi's traditional अ, झ, ल and श are
  not drawn (the `tiro` hand has them), nor are Vedic accents. Stacks of three or more consonants fall back to a
  visible virama in the pen hands. The type hands follow each font's own rules and handle them.
- **It's slow on a small CPU** for the pen hands: a few seconds per image, because every pen step is rasterised
  separately. Type hands take under a second.
