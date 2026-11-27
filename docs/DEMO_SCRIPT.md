# StrokeSpeak Live Demonstration Script (10 Minutes)

> **Current-state update (2026-11-21):** Follow [CURRENT_PROJECT_STATUS.md](CURRENT_PROJECT_STATUS.md) for counts and evidence limits. The app now requires account sign-in; all numeric learner-ID URLs and account-switching directions in this older script are retired. Open the root URL and use a newly created account for a clean profile. Do not claim a profile is empty unless you have checked it.

**Target URL**: `http://localhost:5173/`  
**Presenter Profile**: Sign in with a project account; create a new account for a clean learner profile.  
**Rehearsal Profile**: Use an account whose saved attempts and progress you have reviewed.  

**Target Duration**: 10 Minutes  
**Audience**: Final Year MCA Project Viva Board / Academic Evaluators  

---

## Overview & Demo Principles
- **No Secrets Exposed**: Never display console logs with environmental credentials, `.env` values, or database connection parameters.
- **Clean State for Live Demo**: Create a new account for an empty profile; existing account rows remain unchanged.
- **Rehearsal Guidance**: Use an account you control, and check its saved history before making claims about its state.
- **Demo Rehearsal Guidelines (Human Drawing & Submission)**:
  - **Single Submit & Clear**: Press **Submit once**, then press **Clear** or **Reset** before the next drawing (pressing Submit twice saves the same drawing again, creating duplicate attempt rows with identical stored stroke data as seen in Attempts 100/101 and 102/103).
  - **Moderate Expectations Aloud**: human drawings by one person scored from about 16 to 89 (lowest stroke-order score 16.39, highest handwriting score 88.71); do not promise a score.
  - **Optimal Character Selection**: For the "correct drawing" step and the stroke replay use **あ**, drawn in the order shown by the replay (horizontal bar, vertical stroke, loop), single Submit then Clear; keep **い** or **う** as the fallback; do not promise any score aloud; if a stray dot or a wrong order happens, press Clear and redraw.
  - **Strict Stroke Order Explanation**: Explicitly state to the board that stroke-order scoring is mathematically strict and position-by-position, and can show "partly matched" even when the overall character shape looks visually correct to the human eye.
- **Honest Framing & Pronunciation Status**: Browser recording, audio saving, and local Faster-Whisper transcription are implemented. The displayed speech result is transcript similarity, not acoustic or phoneme-level pronunciation analysis. Sanskrit reference audio is an approximate Hindi/Indic voice.
- **Synthetic Trace & Human Drawing Disclosure**: Earlier automated scoring benchmarks recorded in `HANDOFF_REPORT.md` (Sections 8, 9, 10, 20) were synthetic traces generated from the reference strokes, not human drawings: model traces 100; wobble variants handwriting 96.35 to 97.12 and order 88.90 to 96.45 (attempts 57, 60, 63, 66, 69, 72); shifted 15% and scaled to 60% handwriting 78.66 to 89.00 and order 84.19 to 89.55 (attempts 58, 61, 64, 67, 70, 73). Freehand drawings made with a mouse by a human hand were recorded in attempts 93–116 (see table below). The sample is 24 attempts by one person with a mouse on 5 characters; ids 110-116 are a deliberate careful trace of あ. This is not an accuracy measure (do not call any of this "accuracy"). Genuinely physical and environment-dependent viva conditions remain marked `[UNVERIFIED]`.

---

## Human Drawing Test (Exploratory Sample Reference)

> [!NOTE]
> **Exploratory Sample Disclosure**: The earlier tests in this project used synthetic traces generated from the reference strokes; one person then drew the attempts below with a mouse. The sample is 24 attempts by one person with a mouse on 5 characters; ids 110-116 are a deliberate careful trace of あ. Results are not an accuracy measure. Do not call any of this "accuracy".

### Recorded Human Mouse Drawing Attempts (IDs 93–116 on Learner 1):

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

### Key Analytical Findings for Presenters:
- Earlier tests in this project used synthetic traces generated from reference strokes (adding wobble or shifting); one person then drew these attempts with a mouse.
- The sample is 24 attempts by one person with a mouse on 5 characters; ids 110-116 are a deliberate careful trace of あ. This is not an accuracy measure.
- Drawings with the right stroke count scored higher on handwriting shape (71.52 to 88.71).
- Chunk 4F compared the stored stroke data with the reference strokes. In attempts 111 and 114 the strokes were drawn in a different order from the reference (111: vertical, vertical, horizontal; 114: vertical, horizontal, loop). Attempt 94 is a best fit for a different order (weaker evidence). Attempt 96 has a zero-length first stroke (a dot) and two diagonal strokes; the cause of the dot is UNVERIFIED. In four traces drawn in the reference order (112, 113, 115, 116) stroke order scored 87.75 to 88.06. Attempt 110 (2 strokes) was not analysed in 4F. This is one person and a tiny sample.
- Pairs of attempts with identical scores (such as 100 and 101, 102 and 103) have identical stored stroke data, so the same drawing was saved twice.
- Do not call any of this "accuracy".

---

## Step-by-Step Click-by-Click Walkthrough

```
Timeline:
[00:00 - 01:15] Introduction & Dashboard Clean Slate
[01:15 - 03:00] Japanese Hiragana: Stroke Replay & Audio Reference
[03:00 - 05:00] Interactive Drawing & Algorithmic Scoring (Correct Attempt)
[05:00 - 06:15] Deliberately Wrong Attempt & Score Penalties
[06:15 - 07:15] Progress Update & Summary Analytics
[07:15 - 08:30] Multilingual Scope: Sanskrit & Tamil (Graceful Fallbacks)
[08:30 - 09:30] Simplified Chinese: Foundation and Beginner Course
[09:30 - 10:00] Conclusion, Architectural Q&A, and Wrap-Up
```

---

### Step 1: Introduction & Clean Dashboard State (00:00 – 01:15)
- **Action**: Open Google Chrome or Microsoft Edge and navigate to `http://localhost:5173/`. Create a new learner account or sign in.
- **What to Say**:
  > "Good morning, respected evaluators. This is StrokeSpeak, an interactive multilingual handwriting and pronunciation learning platform designed for non-Latin orthographies. A signed-in account keeps each learner's own practice, quiz, and course progress together."
- **Expected Result**:
  - The header shows the name of the signed-in account.
  - A newly registered account begins without prior lesson progress or practice attempts.
  - Four language groups are available: **Japanese** (Hiragana and Katakana), **Sanskrit**, **Tamil**, and **Simplified Chinese**.
- **Fallback if Fails**:
  - If sign-in fails, use **Create account** with a new email and a password of at least eight characters.
  - If the page shows a connection error, verify the Vite dev server is running on port 5173 and the backend health route is healthy.

---

### Step 2: Japanese Hiragana — Stroke Replay & Reference Audio (01:15 – 03:00)
- **Action**:
  1. Click the **Japanese** tab (selected by default).
  2. Select **Foundation Unit 1: Basic Vowels (あ - お)**.
  3. Click **Lesson 61: Hiragana あ**.
  4. In the Learning Studio, observe the **Stroke Order Guide** panel.
  5. Click the **Replay Stroke Order** button.
  6. Click the **Listen to Reference Audio** button.
- **What to Say**:
  > "StrokeSpeak breaks learning into structured units. Here in Japanese Foundation Unit 1, we select Lesson 61 for the Hiragana vowel 'あ'. On the left panel, StrokeSpeak renders an animated SVG stroke guide. This is not a static video; it dynamically renders vector paths sourced from the KanjiVG project (licensed under Creative Commons Attribution-ShareAlike 3.0). By clicking 'Replay', the learner sees the exact order, trajectory, and start-to-end direction of all three strokes. Below the guide, we can listen to the reference pronunciation generated using Google Text-to-Speech."
- **Expected Result**:
  - Lesson title displays `Hiragana あ`, pronunciation `a`, meaning `Hiragana vowel a`.
  - Animated SVG draws stroke 1 (horizontal curve), stroke 2 (vertical loop-cross), and stroke 3 (loop).
  - Audio plays clear native Japanese pronunciation of "a".
- **Fallback if Fails**:
  - *If audio does not play (no internet)*: Explain honestly: *"The backend utilizes gTTS which requires active internet connectivity to stream audio. When offline, the visual phonetic guide (`a`) provides immediate reference."*
  - *If animation freezes*: Click the **Replay** button again; SVG reset triggers a clean DOM key remount.

---

### Step 3: Interactive Drawing & Correct Attempt Submission (03:00 – 05:00)
- **Rehearsal Best Practice**:
  - For the "correct drawing" step and the stroke replay use **あ**, drawn in the order shown by the replay (horizontal bar, vertical stroke, loop), single Submit then Clear; keep **い** or **う** as the fallback; do not promise any score aloud; if a stray dot or a wrong order happens, press Clear and redraw.
  - **Press Submit once, then press Clear or Reset before the next drawing**: Pressing Submit twice saves the same drawing again and creates duplicate attempt rows in the database (with identical stored stroke data as observed in Attempts 100/101 and 102/103).
  - **Score Expectations**: human drawings by one person scored from about 16 to 89 (lowest stroke-order score 16.39, highest handwriting score 88.71); do not promise a score.
- **Action**:
  1. Move cursor to the interactive HTML5 **Drawing Canvas** on the right.
  2. Carefully draw **あ** in 3 strokes in the order shown by the replay (horizontal bar, vertical stroke, loop). If a stray dot or a wrong order happens, press **Clear Canvas** and redraw. (Keep **い** or **う** as the fallback).
  3. Click **Submit Practice Attempt** exactly ONCE, then press **Clear Canvas** before the next drawing.
- **What to Say**:
  > "Now the learner practices on our responsive vector canvas. The canvas records DOM pointer events capturing normalized $(x, y)$ coordinates and millisecond timestamps. When we submit, StrokeSpeak's backend evaluator normalizes the bounding box, resamples the points, and calculates spatial similarity and start-to-end vector cosine alignment against reference strokes. Notice the results: we receive separate scores for handwriting shape score and stroke order correctness. Note that human drawings naturally score lower than synthetic benchmarks, especially on stroke order. Stroke-order scoring is mathematically strict and position-by-position, so it can show 'partly matched' even when the character shape looks visually clean."
- **Expected Result**:
  - Canvas displays drawn strokes smoothly in dark brush ink.
  - POST request sent to `POST /api/v1/practice-attempts`.
  - Response card appears showing:
    - **Handwriting Shape Score**: Drawings matching reference stroke counts achieve 71.52% – 88.71% on human mouse drawings (synthetic benchmarks under ±0.015 wobble achieve 96.35% – 97.12%).
    - **Stroke Order Score**: Strict position-by-position cosine evaluation; in four traces drawn in reference order (112, 113, 115, 116) stroke order scored 87.75 to 88.06, while wrong order drops score heavily; human drawings by one person scored from about 16 to 89 (lowest stroke-order score 16.39, highest handwriting score 88.71); do not promise a score.
    - **Speaking Practice**: Records and assesses a real sample with local Faster-Whisper; describe the result as transcript similarity, not phoneme-level pronunciation.
- **Fallback if Fails**:
  - *If user misdraws accidentally (stray dot or wrong order)*: Click **Clear Canvas** and redraw smoothly. Always clear canvas before submitting a subsequent attempt.
  - *If backend returns error*: Confirm backend is responding on `http://127.0.0.1:8000/api/v1/health`.

---

### Step 4: Deliberately Wrong Attempt & Score Penalty Demonstration (05:00 – 06:15)
- **Action**:
  1. Click **Clear Canvas**.
  2. Draw deliberately incorrect strokes for **あ**:
     - Draw Stroke 1 from right-to-left (reverse direction).
     - Or draw an incorrect straight line across the canvas.
  3. Click **Submit Practice Attempt**.
- **What to Say**:
  > "To demonstrate the geometric prototype, let us draw an intentional error: reverse a stroke or draw an inaccurate shape. Submitting compares the learner path with the selected reference. Direction disagreement lowers the stroke-order score gradually; the current version does not use a hard 90-degree cutoff. The score is a prototype estimate, not a validated measure of handwriting accuracy."
- **Expected Result**:
  - A deliberate direction or shape error should reduce the prototype score, but no exact numeric result is promised.
  - Attempts 74, 76, and 77 were scored before the November 21 gradual-direction update; their stored values are historical and are not current-version validation.
  - Diagnostic feedback identifies directional or geometric mismatch.
- **Fallback if Fails**:
  - If the score seems unexpectedly high, explain that the evaluator still pairs strokes by index and uses approximate geometry. Do not claim that one score proves correct handwriting.

---

### Step 5: Progress Update & Summary Analytics (06:15 – 07:15)
- **Action**:
  1. Click **Mark Lesson Complete** (or observe auto-completion upon qualifying attempt).
  2. Click **Dashboard** in the top navigation bar.
- **What to Say**:
  > "Upon completing the exercise, lesson progress is committed to MySQL. Returning to the dashboard, we can see the completed lesson and saved practice attempt for the selected learner. These results come from the database; the geometric and transcript similarity scores remain prototype measurements."
- **Expected Result**:
  - Lessons Completed updates to `1 / 128` for the Japanese tutor if the clean Learner 3 profile is used.
  - Practice attempts counter increments.
  - Recent attempts table lists the two submissions with individual handwriting and stroke order percentages.
- **Fallback if Fails**:
  - If progress bar does not visually update: Click the browser refresh button (`F5`). Because the signed-in session is persisted in browser storage, the updated state is refetched from MySQL after refresh.

---

### Step 6: Sanskrit & Tamil — Draft Reference Disclosure (07:15 – 08:30)
- **Action**:
  1. Switch to the **Sanskrit (Devanagari)** tab.
  2. Click **Foundation Unit 1: Basic Vowels (अ - उ)** -> **Lesson 339: Vowel अ**.
  3. Highlight the approximate Sanskrit audio label and the draft stroke-guide warning.
  4. Switch to the **Tamil** tab.
  5. Click **Beginner Unit 5: Common Words & Sentences** -> **Lesson 353: Word வணக்கம்**.
- **What to Say**:
  > "Our Sanskrit and Tamil courses include draft reference stroke guides. Their source attribution is still being verified, so the app labels them as drafts and does not present them as authoritative. Sanskrit reference audio is a Hindi/Indic synthetic approximation, and the UI says so."
- **Expected Result**:
  - Sanskrit and Tamil draft guides display the warning that source attribution is unverified.
  - Sanskrit audio is labeled approximate.
  - Tamil course currently contains 32 lessons across Foundation, Beginner, Elementary, and Advanced.
- **Fallback if Fails**:
  - If fallback banner does not appear: Check that lesson character ID is correctly non-Kana (e.g., ID 216 for Sanskrit, ID 25 for Tamil).

---

### Step 7: Simplified Chinese — Current Curriculum (08:30 – 09:30)
- **Action**:
  1. Switch to the **Simplified Chinese** tab.
  2. Choose a Tamil Foundation character to show the draft warning for unverified source provenance. A sourced Sanskrit or Chinese guide instead displays that qualified instructor review is pending.
  3. Click **Lesson 348: Character 一 and its tone**.
- **What to Say**:
  > "Finally, Simplified Chinese currently has 14 lessons: nine Foundation and five Beginner. Its stroke paths are still draft references, not authoritative stroke-order material. Additional levels and source verification remain future work."
- **Expected Result**:
  - Chinese lesson path shows the currently available Foundation and Beginner content.
  - Draft guide warning is visible for characters whose reference provenance is unverified.
- **Fallback if Fails**:
  - If a character has no reference data, explain that stroke animation is unavailable for that character.

---

### Step 8: Conclusion & Viva Defense Wrap-Up (09:30 – 10:00)
- **Action**: Return to Dashboard or open FastAPI Swagger documentation (`http://127.0.0.1:8000/docs`).
- **What to Say**:
  > "To summarize: StrokeSpeak delivers a functional, multi-script language platform with full relational persistence in MySQL, a fast asynchronous API in FastAPI, and a responsive React frontend. All features demonstrated are fully implemented without fabricated machine learning claims. We welcome questions from the examination committee."
- **Expected Result**:
  - Seamless transition to viva questions.

> [!WARNING]
> **Swagger `/docs` Live Demo Safety Rule**:
> In Swagger (/docs) press Execute only on GET routes. Never press Execute on transcribe, pronunciation-audio or pronunciation-assessment, or on any POST/PUT/DELETE route; they can create rows or call an external service.

---

## Comprehensive "If Something Fails" Fallback Matrix

| Scenario / Failure Mode | Root Cause | Immediate Action & Explanatory Script |
|:---|:---|:---|
| **No Internet Connection** | gTTS API requires Google TTS connectivity. | *"Our reference audio leverages gTTS cloud synthesis. The visual phonetic guide (`romaji/pinyin`) remains completely functional offline. In future scope, an offline phoneme synthesis engine is planned."* |
| **Backend Unreachable (Port 8000 down)** | Uvicorn process terminated or stopped. | Open terminal, execute: `python -m uvicorn main:app --reload --port 8000` in `backend/`. Confirm `GET /api/v1/health` returns `healthy`. Keep frontend open. |
| **Frontend Server Terminated (Port 5173)** | Vite process stopped. | Open terminal, execute: `npm run dev` in `frontend/`. Reload `http://localhost:5173/`. |
| **Wrong Account Loaded** | A different account is signed in. | Use **Sign out**, then sign in with the intended email. Account identity is validated by the backend token. |
| **Existing Account Has Prior Practice** | The account already has saved attempts or progress. | Create a new account if a clean profile is needed; do not claim existing accounts are empty. |
| **Canvas Does Not Draw** | Browser pointer event lock or touch issue. | Click **Clear Canvas** button; ensure mouse cursor is within the canvas boundary coordinates (700x320). |
| **Microphone Not Permitted** | Browser blocked audio capture permission. | Click the browser lock icon in the address bar -> toggle **Microphone** to 'Allow' -> refresh page. Remind evaluators that audio recording is local-only and not uploaded. |
