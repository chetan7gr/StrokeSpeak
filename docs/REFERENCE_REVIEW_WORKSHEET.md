# StrokeSpeak reference-path review worksheet

Use this worksheet with a qualified Sanskrit/Devanagari, Tamil, and Simplified Chinese instructor. Do not approve a path because its animation looks plausible. Compare the target glyph, stroke count, stroke order, direction, and writing convention against a named source or the instructor's explicitly named standard. A qualified reviewer should initial and date each accepted row. Keep the database `instructional_review_status` as `pending` until the reviewer has completed the evidence below.

## Review record

- Reviewer name and qualification: ______________________________
- Script/language expertise: ____________________________________
- Review date: __________________
- Reference standard/source and URL or publication: ______________
- Convention used (region/style/school): _________________________
- Notes on variants or acceptable alternatives: __________________

For each row, mark **approve**, **revise**, or **hold** and record the cited page/section or reviewer explanation. If a path is revised, keep the upstream attribution and disclose the adaptation; create a pre-change backup first.

## Sanskrit (Devanagari)

| Character ID | Glyph | Current source state | Required decision | Reviewer / date / source |
| ---: | :---: | --- | --- | --- |
| 216 | अ | Lipi, pinned revision; CC BY 4.0; review pending | Check form, 2 strokes, order and direction for the Sanskrit convention | |
| 217 | आ | Existing draft path; provenance unverified | Provide a reusable source or replace with a properly sourced path; then review | |
| 218 | इ | Lipi, pinned revision; CC BY 4.0; review pending | Check form, 2 strokes, order and direction | |
| 219 | ई | Existing draft path; provenance unverified | Provide a reusable source or replace with a properly sourced path; then review | |
| 220 | उ | Lipi, pinned revision; CC BY 4.0; review pending | Check form and 1-stroke sequence | |
| 221 | ऊ | Lipi, pinned revision; CC BY 4.0; review pending | Check form and 2-stroke sequence | |
| 222 | ऋ | Lipi, pinned revision; CC BY 4.0; review pending | Check the extracted 3-stroke form, order and direction against the selected Sanskrit convention | |
| 223 | ए | Lipi, pinned revision; CC BY 4.0; review pending | Check form and 2-stroke sequence | |
| 224 | ऐ | Existing draft path; provenance unverified | Provide a reusable source or replace with a properly sourced path; then review | |
| 225 | ओ | Existing draft path; provenance unverified | Provide a reusable source or replace with a properly sourced path; then review | |
| 226 | औ | Existing draft path; provenance unverified | Provide a reusable source or replace with a properly sourced path; then review | |
| 232 | ॠ | Lesson added; no saved stroke path | Verify the glyph and provide a reusable reference path | |
| 233 | ऌ | Lesson added; no saved stroke path | Verify the glyph and provide a reusable reference path | |
| 234 | ॡ | Lesson added; no saved stroke path | Verify the glyph and provide a reusable reference path | |

After completing the worksheet for a character, sign in with an administrator account and open **Instructor tools · reference maintenance** in the learner app. Record the reviewer, qualification, standard/source, convention, decision, and notes in the review form. Choose **Approve** only after checking the displayed SVG guide and saved normalized drawing against that evidence. Approval requires an attributed source/license and is bound to a SHA-256 fingerprint of those exact paths. The form stores the reviewer-supplied attestation; the project owner must independently confirm reviewer qualifications.

Canvas edits to source-attributed paths are rejected. If an unverified draft is changed, the API creates a row-only rollback file, clears prior SVG source paths, and keeps the draft marked unverified with review pending.

Source material for the six attributed glyphs: [Lipi model card](https://huggingface.co/Vishwasaidev/lipi), pinned model revision `c547139c82130da50827a1f2bffb995254395600`, CC BY 4.0. StrokeSpeak's import transformation and timestamp placeholder are described in `backend/data/reference_strokes/lipi-devanagari-c547139c82130da50827a1f2bffb995254395600/README.md`.

## Tamil

All twelve vowel paths have source metadata marked **unverified**. First identify a source that permits reuse of its stroke geometry and sequence; then verify the path against the selected Tamil writing convention. A textbook/PDF page is not automatically reusable merely because it is publicly accessible.

| Character ID | Glyph | Current source state | Required decision | Reviewer / date / source |
| ---: | :---: | --- | --- | --- |
| 25 | அ | Unverified | Source/license and order review | |
| 110 | ஆ | Unverified | Source/license and order review | |
| 111 | இ | Unverified | Source/license and order review | |
| 112 | ஈ | Unverified | Source/license and order review | |
| 113 | உ | Unverified | Source/license and order review | |
| 114 | ஊ | Unverified | Source/license and order review | |
| 115 | எ | Unverified | Source/license and order review | |
| 116 | ஏ | Unverified | Source/license and order review | |
| 117 | ஐ | Unverified | Source/license and order review | |
| 118 | ஒ | Unverified | Source/license and order review | |
| 119 | ஓ | Unverified | Source/license and order review | |
| 120 | ஔ | Unverified | Source/license and order review | |

## Simplified Chinese

These ten rows use ordered median paths from `hanzi-writer-data` 2.0.1 under the Arphic Public License. Review the PRC/Simplified Chinese order and the character shapes shown by StrokeSpeak after its centered, aspect-preserving transform. The full license and source files are included under `backend/data/reference_strokes/hanzi-writer-data-2.0.1/`.

| Character ID | Glyph | Current source state | Required decision | Reviewer / date / source |
| ---: | :---: | --- | --- | --- |
| 241 | 一 | Hanzi Writer Data 2.0.1; APL; review pending | Confirm one horizontal stroke, direction, and placement | |
| 242 | 二 | Hanzi Writer Data 2.0.1; APL; review pending | Confirm 2 strokes, order, direction, and relative placement | |
| 243 | 三 | Hanzi Writer Data 2.0.1; APL; review pending | Confirm 3 strokes and relative placement | |
| 244 | 人 | Hanzi Writer Data 2.0.1; APL; review pending | Confirm 2 strokes, order, and directions | |
| 245 | 大 | Hanzi Writer Data 2.0.1; APL; review pending | Confirm 3 strokes and order | |
| 246 | 小 | Hanzi Writer Data 2.0.1; APL; review pending | Confirm 3 strokes and order | |
| 247 | 口 | Hanzi Writer Data 2.0.1; APL; review pending | Confirm 3 strokes and closure order | |
| 248 | 日 | Hanzi Writer Data 2.0.1; APL; review pending | Confirm 4 strokes and closure order | |
| 249 | 月 | Hanzi Writer Data 2.0.1; APL; review pending | Confirm 4 strokes and order | |
| 252 | 山 | Hanzi Writer Data 2.0.1; APL; review pending | Confirm 3 strokes and order | |

## Release gates

- A **source attribution** status confirms the provenance/license record; it does not mean an instructor approved the sequence.
- Only mark `instructional_review_status` approved after a qualified reviewer has signed off on the exact glyph and convention. Preserve the reviewer/source/date evidence in project documentation.
- A tutorial video additionally requires genuine learner drawing validation for its target character. Never use a synthetic or fabricated learner event to pass that gate.
- Tamil demo generation remains held until both source provenance and instructor review are recorded.
