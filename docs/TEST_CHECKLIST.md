# StrokeSpeak Feature & Verification Test Checklist

> **Current status:** Older checked items below are historical verification records and their counts/settings may no longer match the live project. Use [CURRENT_PROJECT_STATUS.md](CURRENT_PROJECT_STATUS.md) for current authoritative counts (database snapshot verified 2026-11-21; API schema updated 2026-11-22): 809 total core-table rows, 203 public lessons, 29 OpenAPI paths, four user rows. Current full-flow validation is still pending.

This checklist correlates every platform feature against the empirical test results recorded in `backend/HANDOFF_REPORT.md`. Items that have been automated and tested against the live database/API are marked `[x]` with their corresponding handoff report section cited. Physical and environment-dependent viva conditions are marked `[ ] [UNVERIFIED]`.

> [!NOTE]
> **Synthetic Trace & Human Drawing Disclosure**: Earlier automated scoring benchmarks recorded in `HANDOFF_REPORT.md` (Sections 8, 9, 10, 20) were synthetic traces generated from the reference strokes, not human drawings: model traces 100; wobble variants handwriting 96.35 to 97.12 and order 88.90 to 96.45 (attempts 57, 60, 63, 66, 69, 72); shifted 15% and scaled to 60% handwriting 78.66 to 89.00 and order 84.19 to 89.55 (attempts 58, 61, 64, 67, 70, 73). Freehand drawings made with a mouse by a human hand were recorded in attempts 93–116 (Section 8 below). This is a small exploratory sample from one person on 5 characters, not an accuracy measure (do not call any of this "accuracy"). Genuinely physical and environment-dependent viva conditions remain marked `[UNVERIFIED]`.

---

## 1. Backend Service & System Health

- [x] **FastAPI Service Startup**: API initializes on port 8000 using canonical `python -m uvicorn main:app --reload --port 8000`. (*HANDOFF_REPORT.md Section 1, Section 24.5*)
- [x] **Database Health Check**: `GET /api/v1/health` returns HTTP 200 with `status: healthy` and `database: connected`. (*HANDOFF_REPORT.md Section 1, Section 24.5*)
- [x] **Interactive OpenAPI Documentation**: `GET /openapi.json` and `GET /docs` live; the current schema has 27 paths. (*OpenAPI generation after the review workflow, 2026-11-21*)
- [x] **Python 3.12 Environment Compatibility**: Verified `fastapi` (0.143.2), `uvicorn` (0.54.0), and `mysql.connector` (26.7.0) importing cleanly from `.venv`. (*HANDOFF_REPORT.md Section 24.5*)

---

## 2. Language Isolation & Security Boundaries

- [x] **Public Language Allowlist**: `GET /api/v1/languages` returns exactly four user-facing language groups: Japanese (Hiragana + Katakana), Sanskrit (`sa-devanagari`), Simplified Chinese (`zh-hans`), and Tamil (`ta`). (*HANDOFF_REPORT.md Section 2, Section 12, Section 24.2*)
- [x] **Legacy Language Isolation**: Inactive language records in MySQL (Hindi, Telugu, Malayalam, Kannada, Korean, Arabic) return 0 rows (`{"lessons": []}`) on public query endpoints. (*HANDOFF_REPORT.md Section 2, Section 24.2*)
- [x] **Strict Input Validation**: Unsupported script codes return HTTP 422; duplicate language codes return HTTP 409; unlisted character access returns HTTP 404. (*HANDOFF_REPORT.md Section 2*)
- [x] **Deletion Freeze**: 0 rows deleted across entire project lifecycle (MySQL row count strictly preserved or appended). (*HANDOFF_REPORT.md Section 3, Section 24.3*)

---

## 3. Database Schema & Data Integrity

- [x] **Relational Schema Integrity**: All 6 tables (`users`, `languages`, `characters`, `learning_lessons`, `lesson_progress`, `practice_attempts`) maintain valid foreign key constraints. (*HANDOFF_REPORT.md Section 1, Section 24.6*)
- [x] **Database Full Snapshot**: Exported 720 rows to `backend/db_backups/full_export_2026-11-17.json` (1.28 MB) prior to Chunk 2 (as of 2026-11-17 18:10: 112 practice attempts, 746 total rows (regenerate with backend\scripts\show_table_counts.py); includes User 1 Test Learner, User 2 Demo Learner, and User 3 Spare Demo Learner). *Privacy Note: Contains placeholder password hashes and must not be published or shared publicly. The platform operates with placeholder user accounts and omits authentication.* (*HANDOFF_REPORT.md Section 24.6, Section 28, Section 32, Section 34, Section 35*)
- [x] **Auto-Increment Gap Accounting**: Verified ids 8, 10, 12 and 89 are absent; cause not independently verified, while Attempt 90 exists for Learner 1 (`अ`). (*HANDOFF_REPORT.md Section 24.3*)
- [x] **Safe PUT Route Testing**: Verified character and language update routes with MySQL row inspection before and after execution. (*HANDOFF_REPORT.md Section 3*)

---

## 4. Japanese Curriculum & Stroke Order Animation

- [x] **Japanese Tutor Integration**: 128 Japanese lessons in one Hiragana/Katakana tutor (100 Foundation, 25 Beginner, 2 Elementary, 1 Advanced); lesson 315 is integrated into the Katakana vowel unit with existing progress preserved. Public lesson total is 203 across the four groups.
- [x] **Meaning & Romanization Corrections**: Hiragana meaning label corrected from legacy "Japanese Katakana" to accurate English definitions and Romaji. (*HANDOFF_REPORT.md Section 4*)
- [x] **KanjiVG Vector Animation**: 92 Japanese Kana (Hiragana and Katakana) render animated vector paths extracted from KanjiVG XML/SVG data. (*HANDOFF_REPORT.md Section 4, Section 13*)
- [x] **Replay Capability**: SVG key reset forces smooth replay of stroke animation without page reload. (*HANDOFF_REPORT.md Section 4, Section 24.4*)

---

## 5. Algorithmic Handwriting & Directional Evaluator

- [x] **Bounding Box Normalization**: Canvas strokes scaled and centered to $[0, 100] \times [0, 100]$ space to provide translation and scale invariance. (*HANDOFF_REPORT.md Section 8*)
- [x] **Spatial Shape Scoring (Synthetic Traces)**: Synthetic traces generated from the reference strokes, not human drawings (tested on 6 Kana: `あ, い, ア, イ, ウ, ノ`; *HANDOFF_REPORT.md Section 20 Table 3*):
  * **Model baseline reference trace**: 100 on all test characters (Attempts 56, 59, 62, 65, 68, 71).
  * **Wobble variants ($\pm 0.015$)**: handwriting 96.35 to 97.12 and order 88.90 to 96.45 (attempts 57, 60, 63, 66, 69, 72).
  * **Shifted 15% and scaled to 60%**: handwriting 78.66 to 89.00 and order 84.19 to 89.55 (attempts 58, 61, 64, 67, 70, 73).
- [x] **Start-to-End Vector Cosine Check**: Added directional vector cosine similarity between learner stroke and reference stroke (*HANDOFF_REPORT.md Section 20*).
- [x] **Reversed Stroke Direction Penalty (Post-Change)**: Single-stroke character (`ノ`) drawn in reverse direction drops stroke-order score to 0.00 (Attempt 74). Two-stroke characters `い` and `ア` with both strokes reversed drop stroke-order score to 0.00 (Attempts 76 & 77) due to negative cosine clamping (*HANDOFF_REPORT.md Section 20 Table 3*).
- [x] **Historical Angle Cliff Verification (legacy scorer only)**: The earlier evaluator scored ノ at 80° as 88.4% and at 100° as 0.0%. This is not a current-scorer check; the sharp cutoff was replaced by gradual local-tangent direction weighting (HANDOFF_REPORT.md Section 57).
- [x] **Multi-Stroke Reverse Order**: Reversed or swapped stroke order was measured on human drawings in chunk 4F (attempts 111 and 114: order 16.95 and 28.21); the older synthetic 3-stroke reversal figure of 66.64 predates the direction check and was not re-measured.

---

## 6. Multilingual Expansion & Graceful Degradation

- [x] **Sanskrit Foundation & Beginner**: Lessons 339–343 (vowels `अ, आ, इ, ई, उ`) and Lessons 344–347 (words `नमस्ते, जलम्, मित्रम्, पुस्तकम्`) seeded and verified in MySQL. (*HANDOFF_REPORT.md Section 24.1*)
- [x] **Sanskrit Audio Disclaimer**: UI displays `"Reference voice: Hindi synthetic voice, approximate for Sanskrit"` prominently. (*HANDOFF_REPORT.md Section 24.4*)
- [x] **Tamil Beginner Unit 5**: Lessons 353–356 (words `வணக்கம், நன்றி, புத்தகம், தண்ணீர்`) ordered 1, 2, 3, 4 before sentence lesson 302. (*HANDOFF_REPORT.md Section 24.1*)
- [x] **Stroke Provenance Disclosure**: Japanese Kana paths are attributed to KanjiVG; six Sanskrit and ten Chinese paths have source attribution but await instructor review; five other Sanskrit and twelve Tamil paths remain unverified. Review approvals are bound to the exact path fingerprint.
- [x] **Simplified Chinese Curriculum**: 14 lessons currently exist (9 Foundation, 5 Beginner); higher levels are not yet present.

---

## 7. Frontend User Experience & Responsiveness

- [x] **Mobile Viewport Compliance (390px)**: Headless Chrome CDP verified `document.documentElement.scrollWidth <= window.innerWidth` (390px <= 390px) with 0 horizontal overflow. (*HANDOFF_REPORT.md Section 5, Section 24.4*)
- [x] **Desktop Viewport Compliance (1280px)**: Verified `1265px <= 1280px` layout with 0 horizontal scroll. (*HANDOFF_REPORT.md Section 24.4*)
- [x] **No NaN / Undefined Display Errors**: Verified across all 4 language tabs for both Learner 1 and Learner 2. (*HANDOFF_REPORT.md Section 10, Section 24.4*)
- [x] **Authenticated Learner Ownership (Code)**: Numeric learner-ID selection was removed. Learner attempts, saved audio, lesson progress, and quizzes now require a signed Bearer token and use the authenticated owner. (*HANDOFF_REPORT.md Section 56*)
- [x] **Clean Learner Account Rule**: A newly registered account provides a clean profile. The existing database snapshot remains historical; public pages cannot select accounts by ID.
- [x] **Signed-In Account Header**: Top navigation identifies the authenticated learner name. (*HANDOFF_REPORT.md Section 56*)
- [x] **Signed Token Flow (Implementation)**: Registration/login, 8-hour HMAC token validation, frontend token persistence, and owner checks are implemented.
- [ ] **Live Account Flow**: Restart backend/frontend, create or sign in to a real account, save an attempt, sign out/in, and confirm the account-scoped data. Production hardening (HTTPS, refresh/revocation, rate limits, recovery) remains incomplete.
- [x] **Production Bundle Build**: `npm run build` passed on 2026-11-21 after the authenticated account UI changes.

---

## 8. Human Drawing Test (Exploratory Sample)

- [x] **Freehand Human Drawing Scoring Test (24 Attempts Recorded)**: Real human hand-drawn Kana scores on canvas recorded across 24 interactive submissions for Learner 1 (IDs 93–116; HANDOFF_REPORT.md Section 34, Section 35).

> [!NOTE]
> **Exploratory Sample Disclosure**: Earlier tests in this project used synthetic traces generated from reference strokes (adding wobble or shifting); one person then drew these attempts with a mouse. The sample is 24 attempts by one person with a mouse on 5 characters; ids 110-116 are a deliberate careful trace of あ. Results are not an accuracy measure. Do not call any of this "accuracy".

### Recorded Human Mouse Drawing Attempts (IDs 93–116 on Learner 1):

| Attempt ID | Character (Glyph / ID) | Strokes Drawn | Ref Strokes | Handwriting Score | Stroke Order Score | Created At | Pattern / Observation |
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

### Key Analytical Findings:
- Earlier tests in this project used synthetic traces generated from reference strokes (adding wobble or shifting); one person then drew these attempts with a mouse.
- The sample is 24 attempts by one person with a mouse on 5 characters; ids 110-116 are a deliberate careful trace of あ. This is not an accuracy measure.
- Drawings that matched the reference stroke count scored higher on handwriting shape (71.52 to 88.71).
- Chunk 4F compared the stored stroke data with the reference strokes. In attempts 111 and 114 the strokes were drawn in a different order from the reference (111: vertical, vertical, horizontal; 114: vertical, horizontal, loop). Attempt 94 is a best fit for a different order (weaker evidence). Attempt 96 has a zero-length first stroke (a dot) and two diagonal strokes; the cause of the dot is UNVERIFIED. In four traces drawn in the reference order (112, 113, 115, 116) stroke order scored 87.75 to 88.06. Attempt 110 (2 strokes) was not analysed in 4F. This is one person and a tiny sample.
- Pairs of attempts with identical scores (such as 100 and 101, 102 and 103) have identical stored stroke data, so the same drawing was saved twice.
- Do not call any of this "accuracy"; human drawings by one person scored from about 16 to 89 (lowest stroke-order score 16.39, highest handwriting score 88.71); do not promise a score.

---

## 9. Manual & Physical Hardware Verification [UNVERIFIED]

The following items depend on physical presentation hardware and live human execution, and remain marked `[UNVERIFIED]`:

- [ ] `[UNVERIFIED]` **Projector Resolution Scaling**: Verify that the 1280px UI scales cleanly when mirrored to 1080p (1920x1080) or 720p viva room external projectors.
- [ ] `[UNVERIFIED]` **Physical Microphone Recording**: Verify that browser Web Audio API prompts for and captures local microphone input without OS permission locks.
- [ ] `[UNVERIFIED]` **Live Internet Latency for gTTS**: Verify that campus Wi-Fi / hotspot provides $< 800\text{ms}$ round-trip latency to Google Text-to-Speech audio endpoints.
- [ ] `[UNVERIFIED]` **Hardware Touchscreen / Stylus Input**: If using a tablet or 2-in-1 laptop during presentation, verify stylus pointer events produce continuous stroke coordinate vectors.
- [ ] `[UNVERIFIED]` **External Audio Speakers**: Verify laptop or podium external speakers clearly broadcast sample audio from the Japanese, Sanskrit, Tamil, and Simplified Chinese tutor groups without feedback.

## 10. Final Integration Evidence (2026-11-22)

- [x] Video overwrite safety: 8 focused tests passed; no MP4 regenerated or replaced.
- [x] Five mapped lesson MP4s decode; linguistic/reference findings and release holds are recorded in FINAL_VALIDATION_WORKSHEET.md.
- [ ] Browser learner walkthrough: not completed; do not mark passed based on the API regressions.
- [ ] Genuine handwriting: 1/41 baseline, attempt identity must be attributed; 40 further target classes need genuine drawings.
- [ ] Genuine microphone: 0/4 tutor groups.
- [ ] Final ZIP: not ready pending remaining evidence, integration review, and fresh final build/tests.
- [ ] See FINAL_VALIDATION_WORKSHEET.md for blank character-by-character and microphone recording matrices.

- [x] Fresh Vite production build passed with output outside the project.
- [x] Five mapped video endpoints returned HTTP 200 and video/mp4; this is route/stream access, not instructional validation.
- [x] The former Japanese female-lipsync-v4 direct URL alias returned the v5 media filename; it remains available for compatibility.
- [x] Four CNN model groups loaded and seven fixture-image inference calls matched their expected labels; these are not human handwriting tests or accuracy metrics.

- [x] All five mapped lessons now use teacher-static-v2 videos. Each route returned HTTP 200/video/mp4, each MP4 decoded, and sampled frames confirm the tutor's body is still while the mouth moves during narration. Narration remains English Microsoft Zira Desktop; movement follows audio level, not phonemes.
