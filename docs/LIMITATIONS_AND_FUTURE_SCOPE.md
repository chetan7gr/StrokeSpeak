# StrokeSpeak: Technical Limitations & Future Scope

**Document Purpose**: Viva defense preparation and academic transparency guide for the examination committee.  
**Tone**: Honest, technically grounded, and verifiable against the real codebase.

---

## 1. What is Implemented and Verified

**Current checkpoint: 2026-11-22.** See [CURRENT_PROJECT_STATUS.md](CURRENT_PROJECT_STATUS.md) for the live counts, course state, and remaining validation. A read-only database audit on this date found 809 rows across the six core tables: users 4, languages 12, characters 250, learning lessons 394, lesson progress 17, and practice attempts 132. The separate quiz tables contain 10 quizzes, 48 questions, and 0 learner submissions. The live API exposes 29 OpenAPI paths after adding admin-only quiz preview and non-persistent grading; learner quiz submission still enforces prerequisites.

StrokeSpeak currently includes:
1. **MySQL 8.0 persistence** across users, languages, characters, learning lessons, lesson progress, practice attempts, and additive quiz tables. Legacy script data remains hidden from the public allowlist.
2. **FastAPI + Uvicorn API** with Pydantic validation, MySQL health checking, lesson and quiz routes, drawing and audio attempt routes, CNN inference endpoints, and tutorial media.
3. **React + Tailwind + Vite learner application**, with a successful production build at this checkpoint. Local browser requests use the Vite `/api` proxy.
4. **Japanese tutor** with 92 Hiragana/Katakana characters, KanjiVG-attributed stroke guides, and 128 lessons in one Japanese selection. Lesson 315 is integrated in Foundation / Katakana vowels, order 6.
5. **Canvas tracing and geometric scoring** using normalized timestamped points. Handwriting and stroke-order scores are heuristic prototype estimates, not a trained handwriting metric.
6. **Four trained TorchScript CNN models cover 41 classes**: Japanese Hiragana (10), Sanskrit (10), Tamil (12), and Simplified Chinese (9). Japanese Katakana remains available for geometric practice but has no trained CNN model; the registry reports it as untrained. Sample-image checks do not establish learner accuracy, and dataset authenticity varies.
7. **Multilingual course data**: Japanese 128 lessons; Sanskrit 29; Tamil 32; Simplified Chinese 14. Intermediate/advanced coverage is not complete in every language.
8. **Audio path**: browser recording, audio persistence, local Faster-Whisper transcription, and normalized transcript similarity are implemented. The speech value is not acoustic or phoneme-level pronunciation analysis, and real microphone validation remains pending.
9. **Section quizzes**: 10 quizzes / 48 questions. Automated quiz progression regression passed 39/39 for locked access, prerequisites, retries, scoring/unlock, attempt history, authorization, and non-persistent administrator preview using isolated test data. A real learner browser walkthrough remains unverified.
10. **Tutorial media**: one ready Japanese Hiragana `あ` tutorial with a realistic female educator portrait and local narration. Mouth motion follows waveform amplitude and pauses; it is not phoneme-accurate lip sync.

Public language groups are Sanskrit (Devanagari), Japanese (Hiragana and Katakana together), Tamil, and Simplified Chinese. Hindi, Telugu, Malayalam, Kannada, Korean, and Arabic remain hidden.

> [!NOTE]
> **Synthetic Trace & Human Drawing Disclosure**: Earlier automated scoring benchmarks recorded in `HANDOFF_REPORT.md` (Sections 8, 9, 10, 20) were synthetic traces generated from the reference strokes, not human drawings: model traces 100; wobble variants handwriting 96.35 to 97.12 and order 88.90 to 96.45 (attempts 57, 60, 63, 66, 69, 72); shifted 15% and scaled to 60% handwriting 78.66 to 89.00 and order 84.19 to 89.55 (attempts 58, 61, 64, 67, 70, 73). Freehand drawings made with a mouse by a human hand were recorded in attempts 93–116 (detailed in Section 2.1 below). The sample is 24 attempts by one person with a mouse on 5 characters; ids 110-116 are a deliberate careful trace of あ. This is not an accuracy measure (do not call any of this "accuracy"). Genuinely physical viva conditions remain marked `[UNVERIFIED]`.

---

## 2. Algorithmic Handwriting Evaluator: Prototype Realities & Weaknesses

> [!IMPORTANT]
> The handwriting evaluation engine in `backend/main.py` is an **algorithmic geometric prototype**, not a deep learning model or trained convolutional neural network (CNN).

The current scorer:
- Normalizes strokes into a bounded coordinate space and resamples points by arc length, reducing sensitivity to capture point density and timing.
- Compares learner and reference trajectories geometrically and applies gradual local tangent-direction weighting; direction penalties are no longer a hard cosine sign switch.
- Ignores unmatched stationary taps for scoring when the reference has no corresponding stationary stroke. Original learner points remain stored unchanged.

### Current algorithmic weaknesses
1. **No open-ended character classification**: the geometric evaluator only compares a drawing to the selected target; it cannot identify an arbitrary character. CNN inference is a separate path and is not validated for general learner accuracy.
2. **Simple-stroke ambiguity**: a straight line can resemble a simple single-stroke character and may score too well despite poor character form.
3. **One-to-one stroke index alignment**: strokes are paired by array index, so inserted or swapped moving strokes can be penalized harshly. The scorer does not yet search for an optimal stroke assignment.
4. **Prototype direction model**: local tangent weighting remains a geometric heuristic, not a trained handwriting model. Existing saved scores were calculated by earlier scorer versions and were not recalculated after the November 21 update.

### 2.1 Human Drawing Test (Exploratory Sample)

> [!NOTE]
> **Exploratory Sample Disclosure**: Earlier tests in this project used synthetic traces generated from reference strokes (adding wobble or shifting); one person then drew these attempts with a mouse. The sample is 24 attempts by one person with a mouse on 5 characters; ids 110-116 are a deliberate careful trace of あ. Results are not an accuracy measure. Do not call any of this "accuracy".

#### Recorded Human Mouse Drawing Attempts (IDs 93–116 on Learner 1):

| Attempt ID | Character (Glyph / ID) | Strokes Drawn | Ref Strokes | Handwriting Score | Stroke Order Score | Created At | Pattern / Evaluator Observation |
|---:|:---:|:---:|:---:|:---:|:---:|:---|:---|
| 93 | あ (ID 2) | 4 | 3 | 64.50 | 37.16 | 2026-11-17 16:23:11 | Extra stroke drawn (4 vs 3 ref strokes) |
| 94 | あ (ID 2) | 3 | 3 | 87.72 | 16.60 | 2026-11-17 16:23:36 | Right stroke count; best fit for different order (weaker evidence) |
| 95 | あ (ID 2) | 2 | 3 | 51.04 | 16.39 | 2026-11-17 16:24:01 | Missing stroke drawn (2 vs 3 ref strokes) |
| 96 | あ (ID 2) | 3 | 3 | 79.97 | 41.01 | 2026-11-17 16:24:24 | Zero-length first stroke (a dot) and two diagonal strokes; dot cause UNVERIFIED |
| 97 | あ (ID 2) | 4 | 3 | 51.15 | 16.44 | 2026-11-17 16:24:48 | Extra stroke drawn (4 vs 3 ref strokes) |
| 98 | あ (ID 2) | 5 | 3 | 53.04 | 52.97 | 2026-11-17 16:35:31 | Multiple extra strokes (5 vs 3 ref strokes) |
| 99 | い (ID 28) | 2 | 2 | 71.52 | 77.14 | 2026-11-17 16:37:27 | Right stroke count; balanced shape and stroke order |
| 100 | う (ID 29) | 2 | 2 | 80.11 | 79.71 | 2026-11-17 16:38:25 | Right stroke count; strong shape and stroke order match |
| 101 | う (ID 29) | 2 | 2 | 80.11 | 79.71 | 2026-11-17 16:39:00 | Identical score to 100 (identical stored stroke data, so the same drawing was saved twice) |
| 102 | え (ID 30) | 4 | 2 | 41.14 | 31.78 | 2026-11-17 16:39:49 | Fragmented stroke sequence (4 vs 2 ref strokes) |
| 103 | え (ID 30) | 4 | 2 | 41.14 | 31.78 | 2026-11-17 16:40:01 | Identical score to 102 (identical stored stroke data, so the same drawing was saved twice) |
| 104 | か (ID 31) | 9 | 3 | 26.69 | 16.44 | 2026-11-17 16:54:24 | Multi-stroke scribble test (9 vs 3 ref strokes) |
| 105 | か (ID 31) | 3 | 3 | 87.14 | 71.45 | 2026-11-17 16:55:07 | Right stroke count; high shape match and solid stroke order |
| 106 | か (ID 31) | 3 | 3 | 86.80 | 71.23 | 2026-11-17 16:55:32 | Right stroke count; consistent high shape and stroke order |
| 107 | か (ID 31) | 3 | 3 | 87.13 | 55.94 | 2026-11-17 16:56:15 | Right stroke count; good shape, order partly matched |
| 108 | か (ID 31) | 3 | 3 | 79.41 | 63.90 | 2026-11-17 16:56:55 | Right stroke count; consistent shape match |
| 109 | か (ID 31) | 2 | 3 | 41.89 | 26.15 | 2026-11-17 16:57:11 | Incomplete drawing (2 of 3 reference strokes) |
| 110 | あ (ID 2) | 2 | 3 | 56.82 | 47.67 | 2026-11-17 17:52:52 | Deliberate trace of あ (2 of 3 reference strokes; not analysed in 4F) |
| 111 | あ (ID 2) | 3 | 3 | 88.71 | 16.95 | 2026-11-17 17:53:34 | Deliberate trace of あ (drawn in wrong order: vertical, vertical, horizontal) |
| 112 | あ (ID 2) | 3 | 3 | 88.22 | 88.01 | 2026-11-17 17:54:03 | Deliberate trace of あ (drawn in reference order: horizontal, vertical, loop) |
| 113 | あ (ID 2) | 3 | 3 | 88.10 | 87.75 | 2026-11-17 17:54:25 | Deliberate trace of あ (drawn in reference order: horizontal, vertical, loop) |
| 114 | あ (ID 2) | 3 | 3 | 87.74 | 28.21 | 2026-11-17 17:54:47 | Deliberate trace of あ (drawn in wrong order: vertical, horizontal, loop) |
| 115 | あ (ID 2) | 3 | 3 | 88.02 | 87.78 | 2026-11-17 17:55:20 | Deliberate trace of あ (drawn in reference order: horizontal, vertical, loop) |
| 116 | あ (ID 2) | 3 | 3 | 87.86 | 88.06 | 2026-11-17 17:55:55 | Deliberate trace of あ (drawn in reference order: horizontal, vertical, loop) |

#### Key Analytical Findings:
- Earlier tests in this project used synthetic traces generated from reference strokes (adding wobble or shifting); one person then drew these attempts with a mouse.
- The sample is 24 attempts by one person with a mouse on 5 characters; ids 110-116 are a deliberate careful trace of あ. This is not an accuracy measure.
- Drawings that matched the reference stroke count scored higher on handwriting shape (71.52 to 88.71).
- Chunk 4F compared the stored stroke data with the reference strokes. In attempts 111 and 114 the strokes were drawn in a different order from the reference (111: vertical, vertical, horizontal; 114: vertical, horizontal, loop). Attempt 94 is a best fit for a different order (weaker evidence). Attempt 96 has a zero-length first stroke (a dot) and two diagonal strokes; the cause of the dot is UNVERIFIED. In four traces drawn in the reference order (112, 113, 115, 116) stroke order scored 87.75 to 88.06. Attempt 110 (2 strokes) was not analysed in 4F. This is one person and a tiny sample.
- Pairs of attempts with identical scores (such as 100 and 101, 102 and 103) have identical stored stroke data, so the same drawing was saved twice.
- Do not call any of this "accuracy"; human drawings by one person scored from about 16 to 89 (lowest stroke-order score 16.39, highest handwriting score 88.71); do not promise a score.

---

## 3. Pronunciation & Audio: Current Implementation Reality

The frontend records audio through the browser and the backend can store it against a drawing attempt. The active local transcription route uses Faster-Whisper. Language conditioning is Japanese `ja`, Sanskrit `sa`, Tamil `ta`, and Simplified Chinese `zh`; the installed gTTS package has no Sanskrit voice, so its reference audio uses an explicitly labeled Hindi/Indic approximation. The displayed speech value is normalized transcript similarity against the target/transliteration. It does not evaluate phoneme timing, formants, aspiration, accent, or acoustic pronunciation quality. Real learner microphone validation is still 0/4 tutor groups; no successful local transcription result should be claimed until a learner recording is assessed.

---

## 4. Computer Vision and CNN Status

OpenCV preprocessing and four trained TorchScript CNN models are present for 41 classes: Japanese Hiragana (10), Sanskrit (10), Tamil (12), and Simplified Chinese (9). Japanese Katakana has no trained CNN model yet, although its tutor lessons and geometric practice feedback are available. Some model data is synthetic; model loading and sample-image inference do not prove generalization or learner accuracy. A documented `あ`→`お` CNN error remains under investigation, and the original raster for the attempt was not retained. Avoid presenting any model score as validated accuracy.

---

## 5. Reference Stroke Data and Provenance

- **Japanese Kana**: 92 stroke guides are attributed to KanjiVG under CC BY-SA 3.0.
- **Sanskrit**: six standalone vowel paths (अ, इ, उ, ऊ, ऋ, ए) are attributed to the pinned Lipi revision under CC BY 4.0; qualified instructor review is pending. Five other active Sanskrit vectors remain unverified.
- **Simplified Chinese**: ten starter paths are attributed to `hanzi-writer-data` 2.0.1 under the Arphic Public License; instructor review is pending.
- **Tamil**: twelve vowel paths remain unverified and are not authorized for redistribution.
- The review API records instructor-supplied evidence and fingerprints the exact paths. A saved review does not independently verify the reviewer's qualification. Never present a pending or unverified guide as an approved standard.

---

## 6. Tutorial Video and Reference Audio

Five original lesson videos were technically audited and decode. Lesson 61 now maps to the new 3D robotic female portrait/video variant; the previous Japanese v5 file remains preserved, and the Sanskrit, Tamil, and Chinese mappings were not changed. The robot preview uses waveform-smoothed mouth movement, not phoneme-accurate lip sync, and English Microsoft Zira narration, not Japanese pronunciation instruction. The other four lesson files have burned-in English captions and no subtitle streams; their voices are unverified except the historical Japanese v5. Articulation-stage diagrams remain generic across sounds. Sanskrit stroke-caption/vector mismatch is under review; Tamil source paths are unverified; Sanskrit and Chinese references still need qualified instructional review. Non-Japanese clips remain candidate demonstrations, not language-certified tutorials. The overwrite guard has 8/8 focused tests; no existing video was overwritten.

---

## 7. Current Curriculum Depth

The live public lesson total is 203 across the four groups: Japanese 128 (Foundation 100, Beginner 25, Elementary 2, Advanced 1), Sanskrit 29 (Foundation 19, Beginner 10), Tamil 32 (Foundation 24, Beginner 6, Elementary 1, Advanced 1), and Simplified Chinese 14 (Foundation 9, Beginner 5). Sanskrit and Chinese do not yet have Elementary, Intermediate, and Advanced content; Tamil and Japanese also lack some levels. The level selector marks empty levels as “Coming later”. Do not describe all courses as complete.

Ten section quizzes with 48 questions exist. Every Beginner unit in each tutor group currently has a quiz, and server-side lesson/quiz routes enforce prerequisites. No real learner quiz submission/unlock walkthrough has yet been validated.

---

## 8. Accounts, Privacy & Security

Registration and login issue signed 8-hour HMAC access tokens. Learner data routes bind to the authenticated account. Shared content and review writes require an ID in `STROKESPEAK_ADMIN_USER_IDS` (empty by default). The instructor review form records self-reported qualifications and an exact-path fingerprint; it cannot verify a person's expertise. The frontend production build and backend OpenAPI generation passed after the review workflow changes, but a live sign-in still needs confirmation after restarting the servers. Before production deployment, add HTTPS, token refresh/revocation, rate limits, account recovery, and a reviewed administrator-management process. Placeholder accounts with non-PBKDF2 hashes no longer authenticate; register a real account for use.

Keep database exports, `.env` files, and any password hashes private. Do not commit them or share them publicly.

---

## 9. Remaining Engineering and Validation Work

1. Validate handwriting, speech, and quiz progression with genuine learner use; keep synthetic/model traces separate from human evidence.
2. Have qualified instructors review the six attributed Sanskrit and ten attributed Simplified Chinese references through the admin review form. The form stores their cited standard, writing convention, decision, time, and exact geometry fingerprint; the app does not verify reviewer credentials. Acquire and document authorized sources for the remaining five Sanskrit and twelve Tamil paths before approval or redistribution.
3. Extend curricula through missing levels with qualified language review and sources.
4. Validate the updated geometric prototype with genuine drawings. It arc-length-resamples strokes (so point count and capture timing do not set the score), uses gradual tangent-direction weighting, and ignores unmatched stationary taps for scoring. Stroke-sequence alignment remains one-to-one by index, so swapped or inserted moving strokes still need a more tolerant aligner; retain prototype wording. Existing historical scores were not recalculated.
5. Expand CNN datasets with genuine, varied learner handwriting and run held-out evaluation before reporting metrics.
6. Complete live account-flow validation after restarting the servers; review HTTPS, token refresh/revocation, request rate limits, account recovery, and administrator provisioning before public deployment.
7. Add a phoneme/acoustic pronunciation evaluator if required; current score is transcript text similarity only.

## Final integration evidence update (2026-11-22)

The fresh Vite production build passed; all four CNN model groups loaded, 7/7 sample-image inference calls matched their fixture labels, and 5/5 mapped video endpoints returned MP4 streams. These are technical/sample checks and do not establish model accuracy or learner success. Automated regression results and the video audit are summarized in [FINAL_VALIDATION_WORKSHEET.md](FINAL_VALIDATION_WORKSHEET.md). The quiz regression (39/39), auth/drawing/speech API regression (16/16), and video overwrite protection tests (8/8) are software checks only. The project still reports genuine handwriting validation at 1/41 and genuine microphone validation at 0/4. A browser learner walkthrough has not been completed. These gaps must remain visible in the MCA report and any demonstration; do not convert automated checks into human validation or accuracy claims.
