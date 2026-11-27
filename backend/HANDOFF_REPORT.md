# StrokeSpeak Backend Handoff Report

Started: 2026-11-16; current checkpoint verified 2026-11-20 (local project workspace)

> **Current source of truth:** See `docs/CURRENT_PROJECT_STATUS.md` for the latest counts and remaining work. The older numbered sections below are a chronological audit and may contain historical snapshots. Latest verified snapshot: 808 rows across the six core tables and 203 public lessons: Japanese 128, Sanskrit 29, Tamil 32, Simplified Chinese 14. Learner 3 is clean; learner 2 has 17 attempts. Genuine handwriting/speech/quiz validation remains incomplete.

## 1. Completed tasks and evidence

### Task 1 — Read-only inspection
- Inspected the FastAPI backend, setup/seed scripts, database connection and all six MySQL tables.
- Verified `GET /` and `GET /api/v1/health` return HTTP 200; health reports `database: connected`.
- Inspected all routes in `/openapi.json` (17 paths; method list in section 4).
- Recorded the original row counts before work: users 1, languages 9, characters 166, learning lessons 314, lesson progress 4, practice attempts 8.

### Task 2 — Public language visibility and validation
- The shared public allowlist in `backend/main.py` is now `ja-hiragana`, `ja-katakana`, `sa-devanagari`, `ta`, and `zh-hans`. This is five script entries for four user-facing languages because Japanese has two scripts.
- Applied the allowlist to the language, character, lesson, progress, and practice result routes. Legacy rows remain in MySQL and are hidden from public results.
- Verified unsupported script input and blank input return 422, duplicate language script code returns 409, invalid/hidden language or character access returns 404, and missing required character input returns 422.

### Task 3 — Safe PUT route checks
- Inserted isolated rows and tested `PUT /api/v1/languages/56` and `PUT /api/v1/characters/169`; both returned success and were confirmed with MySQL `SELECT`.
- Test character 169 (`ॐ`) remains. Language row 56 also remains; Task 6 later reused and renamed it to the canonical Sanskrit language to respect its unique `sa-devanagari` code.

### Task 4 — Correct Japanese labels
- Backed up all 46 Hiragana rows, then changed only their wrong meaning label from “Japanese Katakana character” to “Japanese Hiragana character.”
- Verified 46/46 corrected; glyphs and pronunciations remained unchanged. Python Unicode checks found all glyphs in U+3040–U+309F, no duplicate, missing modern basic, or unexpected glyphs.
- The existing unique `script_code` design (`ja-hiragana`) already distinguishes this data from Katakana, so no schema change was needed.

### Task 5 — Katakana
- Added Japanese Katakana language ID 57 (`ja-katakana`) and 46 basic characters in gojuon order. All are in U+30A0–U+30FF; pronunciation values match the paired Hiragana conventions. The `characters` table has no `stroke_count` column, so no stroke counts were added.
- The API now orders both Hiragana and Katakana in gojuon order. Both lists were checked through the live API.

### Task 6 — Sanskrit
- Reused language ID 56 as “Sanskrit” (`sa-devanagari`), preserving its test character ID 169.
- Added 20 starter entries: 14 independent vowel forms, the first five velar consonants, and standalone anusvara. All saved glyphs are in U+0900–U+097F; all checked IAST/simple romanizations matched the seed data. This is not a complete Sanskrit inventory.
- The current MySQL `utf8mb4_unicode_ci` collation compares `अं` and `अः` equal to `अ`, and standalone `ं` and `ः` equal to each other. The schema was left unchanged; standalone anusvara was retained, and visarga was omitted.

### Task 7 — Tamil
- Verified the 12 original Tamil rows are linked to language ID 19 (`ta`) and lie in U+0B80–U+0BFF. All 12 independent vowels remain.
- Added five starter consonants (`க`, `ச`, `ட`, `த`, `ப`) with simple romanization. The API returns 17 Tamil rows; there are no duplicates.

### Task 8 — Simplified Chinese
- Added Chinese (Simplified), language ID 58 (`zh-hans`), with 12 common Hanzi: 一 二 三 人 大 小 口 日 月 水 火 山.
- Verified all 12 lie in CJK Unified Ideographs U+4E00–U+9FFF and the pinyin tone marks/English meanings match the saved values. This is not a complete Chinese inventory.

### Task 9 — Practice and progress
- Added one beginner Katakana lesson, ID 315 (“Katakana: first five vowels”), because Katakana had no lessons to exercise its progress route.
- Saved progress for user 1 through the API for Hiragana lesson 63 (score 75) and Katakana lesson 315 (score 80), then read both back through `GET /api/v1/lesson-progress?user_id=1`.
- Created Japanese Hiragana practice attempt 11 for user 1 and character ID 2 (`あ`). Its stroke data and feedback were saved and confirmed by direct MySQL `SELECT`.
- The Japanese characters have no reference strokes, so handwriting and stroke-order scores correctly remain `null`/Pending. The text-only pronunciation assessment request `{"transcribed_text":"a"}` returned score 100 and feedback; no audio or transcription service was used.
- Invalid attempts were rejected: missing/empty drawing data 422, unknown user 404, hidden legacy character 404, blank transcript 422, and progress score 101 returned 422. Existing stored scores are all within 0–100.
- Read frontend `App.jsx` only. The backend response fields match the frontend’s character, progress, drawing, and attempt-history reads. No frontend file was changed.

### Task 10 — Repeat-safe scripts and Swagger checklist
- Added six scripts under `backend/scripts/`. Each uses the existing MySQL connection module, validates its seed data, and reports inserted/skipped/updated counts.
- Compiled and ran all six scripts against the populated database. They reported zero new inserts/updates and skipped existing data, confirming they do not duplicate the seeded records.
- Added the PowerShell commands and Swagger request examples in sections 4 and 7.

## 2. Files created/modified and backups

### Modified
- `backend/main.py`: public script allowlist, visibility/validation work, Katakana support, and gojuon ordering.

### Created
- `backend/scripts/fix_japanese_labels.py`
- `backend/scripts/seed_katakana.py`
- `backend/scripts/seed_sanskrit.py`
- `backend/scripts/seed_tamil_extra.py`
- `backend/scripts/seed_chinese.py`
- `backend/scripts/seed_katakana_lesson.py`
- `backend/HANDOFF_REPORT.md` (this report)

### Timestamped backups
- `backend/main.py.bak-2026-11-16-065834` — before Task 2 edit.
- `backend/main.py.bak-2026-11-16-071138` — before adding Katakana to the allowlist.
- `backend/main.py.bak-2026-11-16-075813` — before gojuon API ordering edit.
- `backend/scripts/fix_japanese_labels.py.bak-2026-11-16-075219`
- `backend/scripts/seed_katakana.py.bak-2026-11-16-075219`
- `backend/scripts/seed_sanskrit.py.bak-2026-11-16-075219`
- `backend/scripts/seed_tamil_extra.py.bak-2026-11-16-075219`
- `backend/scripts/seed_chinese.py.bak-2026-11-16-075219`
- `backend/scripts/seed_sanskrit.py.bak-2026-11-16-075906` — before adding safe name-backup behavior.
- `backend/scripts/seed_katakana_lesson.py.bak-2026-11-16-075906`
- `backend/HANDOFF_REPORT.md.bak-2026-11-16-075219`

The script/report backups above preserve the empty pre-write files because those files were new. Python compilation also created normal `__pycache__` files under `backend/scripts`.

### Database JSON backups
- `backend/db_backups/task3-put-test-rows-before-update-2026-11-16-070740.json`
- `backend/db_backups/japanese-hiragana-rows-before-label-fix-2026-11-16-070932.json`
- `backend/db_backups/sanskrit-language-before-name-update-2026-11-16-071346.json`
- `backend/db_backups/task9-practice-attempt-11-before-pronunciation-test-2026-11-16-072357.json`

No secrets, passwords, or API keys are included in this report.

## 3. Database schema and data changes

The database has six tables:
- `users`: learner identity and password hash.
- `languages`: name and unique `script_code`.
- `characters`: language link, glyph, meaning, pronunciation, JSON reference strokes; unique `(language_id, character_text)`.
- `learning_lessons`: language, category, text, level/unit/order, and tutorial-video fields.
- `lesson_progress`: user/lesson status and score; unique `(user_id, lesson_id)`.
- `practice_attempts`: user/character, handwriting/stroke-order/pronunciation scores, feedback, JSON stroke data, optional audio fields and transcription state.

No table was dropped, truncated, or cleared. Legacy language/character rows remain.

| Table | Baseline | Final | Change |
|---|---:|---:|---:|
| users | 1 | 1 | 0 |
| languages | 9 | 12 | +3 |
| characters | 166 | 250 | +84 |
| learning_lessons | 314 | 315 | +1 |
| lesson_progress | 4 | 6 | +2 |
| practice_attempts | 8 | 9 | +1 |

New or repurposed records:
- Language ID 56: inserted for PUT test, later renamed to Sanskrit; its original test character ID 169 remains under it.
- Character ID 169: `ॐ`, PUT test record, retained.
- Language ID 57 and character IDs 170–215: Japanese Katakana, 46 characters.
- Character IDs 216–235: 20 Sanskrit starter entries under language ID 56.
- Character IDs 236–240: five added Tamil consonants under language ID 19.
- Language ID 58 and character IDs 241–252: Chinese (Simplified) and 12 Hanzi.
- Lesson ID 315: first five Katakana vowels.
- Progress IDs 15 and 16: user 1 on Hiragana lesson 63 and Katakana lesson 315.
- Practice attempt ID 11: user 1, Hiragana character ID 2; pronunciation score 100, drawing scores pending for lack of Japanese reference strokes.

Japanese Task 4 changed 46 `meaning` values and no row counts. Sanskrit Task 6 changed the name of language row 56; its JSON backup is listed above.

## 4. API results and Swagger checklist

### OpenAPI routes (17 paths)
- `GET /`
- `GET /api/v1/health`
- `POST /api/v1/auth/register`
- `GET, POST /api/v1/practice-attempts`
- `POST /api/v1/practice-attempts/{attempt_id}/pronunciation-assessment`
- `POST /api/v1/practice-attempts/{attempt_id}/transcribe`
- `PUT /api/v1/practice-attempts/{attempt_id}/pronunciation-audio`
- `GET, PUT /api/v1/characters/{character_id}/reference-strokes`
- `GET /api/v1/lessons/{lesson_id}/reference-audio`
- `GET /api/v1/lessons`
- `GET /api/v1/lesson-progress`
- `PUT /api/v1/lessons/{lesson_id}/progress`
- `PUT /api/v1/lessons/{lesson_id}/tutorial-video`
- `GET, POST /api/v1/languages`
- `GET, PUT /api/v1/languages/{language_id}`
- `GET, POST /api/v1/characters`
- `GET, PUT /api/v1/characters/{character_id}`

### Verified live results
- `/` and `/api/v1/health`: HTTP 200; database connected.
- `/api/v1/languages`: HTTP 200; public script codes `ja-hiragana`, `ja-katakana`, `sa-devanagari`, `ta`, `zh-hans`.
- `/api/v1/characters`: HTTP 200; 142 public characters.
- Hiragana language 5: 46 characters in gojuon order. Katakana language 57: 46 characters in gojuon order.
- Tamil language 19: 17 characters. Sanskrit language 56: 21 records including retained test character. Chinese language 58: 12 characters.
- `/api/v1/lessons?language_id=57`: HTTP 200; one Katakana lesson.
- `/api/v1/lesson-progress?user_id=1`: HTTP 200; contains progress for Hiragana and Katakana.
- `/api/v1/practice-attempts?user_id=1`: HTTP 200; includes attempt 11 and its scores/feedback.
- PUT language 56 and character 169 returned success; MySQL SELECT verified the new values.
- Practice attempt 11 response: `{"message":"Practice drawing saved.","attempt_id":11,"user_id":1,"character_id":2,"stroke_count":3,"scores":{"handwriting":null,"stroke_order":null,"pronunciation":null},"scoring_method":"prototype geometric comparison; not trained AI","feedback":"Drawing saved. No reference drawing exists for this character yet, so drawing scores are pending."}`
- Typed pronunciation assessment on attempt 11 returned expected `a`, submitted `a`, score 100.0 and text-comparison feedback. This is transcript-text scoring, not microphone-based scoring.
- Audio upload, hosted/local transcription, reference audio, and tutorial-video update routes were not called. They remain unverified in this work.

### Request examples for Swagger (`http://127.0.0.1:8000/docs`)
Examples using existing IDs may write to the database. Back up the exact row to JSON before any PUT/update. Do not submit audio or call the transcription route.

**POST `/api/v1/languages`** — duplicate-check example; currently returns 409 because `zh-hans` exists:
```json
{"name":"Chinese (Simplified)","script_code":"zh-hans"}
```

**PUT `/api/v1/languages/56`** — Sanskrit row example:
```json
{"name":"Sanskrit","script_code":"sa-devanagari"}
```

**POST `/api/v1/characters`** — one new Simplified Chinese character example; submits one new row if executed:
```json
{"language_id":58,"character_text":"四","meaning":"four","pronunciation_text":"sì"}
```

**PUT `/api/v1/characters/169`** — retained test character example:
```json
{"language_id":56,"character_text":"ॐ","meaning":"PUT route update verified","pronunciation_text":"om"}
```

**POST `/api/v1/practice-attempts`** — creates another practice row if executed:
```json
{"user_id":1,"character_id":2,"stroke_data":[[{"x":0.25,"y":0.1,"time":0},{"x":0.75,"y":0.1,"time":120}],[{"x":0.7,"y":0.12,"time":200},{"x":0.4,"y":0.5,"time":350}],[{"x":0.4,"y":0.5,"time":400},{"x":0.6,"y":0.8,"time":550}]]}
```

**POST `/api/v1/practice-attempts/{attempt_id}/pronunciation-assessment`** — typed-text example only; updates the selected attempt and is not audio transcription:
```json
{"transcribed_text":"a"}
```

The only practice-attempt PUT route is `/api/v1/practice-attempts/{attempt_id}/pronunciation-audio`; it requires actual base64 audio and was intentionally not tested or included as an executable sample.

## 5. Packages

No packages were installed or upgraded. The verified backend environment versions were FastAPI 0.143.2, Uvicorn 0.54.0, mysql-connector-python 26.7.0, python-dotenv 1.2.4, and Pydantic 2.14.1. No CNN, OpenCV, Whisper, gTTS, or hosted API package/service was installed or used as part of these tasks.

## 6. Remaining issues and unverified areas

- Superseded on 2026-11-16: the first five Hiragana and first five Katakana now have verified KanjiVG references. The remaining Kana have no verified references yet. Current scoring is a geometric prototype, not a trained CNN.
- Katakana has one beginner lesson; the broader ordered course still needs to be authored. Sanskrit and Chinese have starter character sets, not complete courses. Tamil has 17 verified rows, not the full script inventory.
- The MySQL case/accent-insensitive collation prevents storing both standalone anusvara `ं` and visarga `ः` under the current unique key; the visarga and combined `अं`/`अः` forms were not inserted.
- Windows Whisper/audio runtime remains unverified. The current learner UI keeps recordings local and does not expose upload or transcription controls. The backend routes remain unverified; no audio or transcription request was made.
- CNN/OpenCV handwriting recognition and AI-generated tutorial videos are not implemented or verified here.
- The original placeholder and legacy Hindi, Arabic, Korean, Telugu, Malayalam, and Kannada rows remain in MySQL, but are hidden by public API filters.

## 7. Exact next task

Next, verify the phone layout in normal Chrome/Edge; then add verified references for more Kana, expand the ordered Japanese curriculum, and continue tutorial video work. Do not estimate reference paths; source them from a verified licensed guide. See the dated Section 9 below for the latest implementation and verified counts.

## 8. Run commands

Backend, in one PowerShell window:
```powershell
Set-Location C:\Users\CHETAN\.vscode\StrokeSpeak\backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Frontend, in a second PowerShell window:
```powershell
Set-Location C:\Users\CHETAN\.vscode\StrokeSpeak\frontend
npm run dev
```

Run each idempotent seed/fix script from the backend folder:
```powershell
Set-Location C:\Users\CHETAN\.vscode\StrokeSpeak\backend
.\.venv\Scripts\python.exe .\scripts\fix_japanese_labels.py
.\.venv\Scripts\python.exe .\scripts\seed_katakana.py
.\.venv\Scripts\python.exe .\scripts\seed_sanskrit.py
.\.venv\Scripts\python.exe .\scripts\seed_tamil_extra.py
.\.venv\Scripts\python.exe .\scripts\seed_chinese.py
.\.venv\Scripts\python.exe .\scripts\seed_katakana_lesson.py
```

## 9. Stroke reference playback and UI implementation (2026-11-16)

### Changes completed

- Added and verified KanjiVG path data for the first five Hiragana and first five Katakana characters. The original SVG path strings, path IDs, viewBox, pinned revision, source URL, and license are preserved with the stored metadata. The learner-facing guide animates those ordered paths from the API response and displays source attribution. It is an SVG stroke replay, not an AI-generated video.
- Extended `GET /api/v1/characters/{character_id}/reference-strokes` with optional `reference_available`, `reference_source`, `stroke_guidance`, and `message` fields. The existing `stroke_data` field remains. For a missing reference, the response and UI say `Reference strokes not available yet`.
- Reworked the frontend into a responsive StrokeSpeak shell with Dashboard, Studio, and Summary navigation; Curriculum and Workspace side navigation; indigo cards; an ordered course picker; a tracing guide overlay; and local recording playback. Initial language selection prefers Japanese because it has the most available lessons.
- Summary cards use API/database values only. The handwriting value is labelled `Geometric prototype · not a trained AI model`; missing values are shown as unavailable or pending. No cohort comparisons or invented streaks are displayed.
- Microphone recordings remain available for local playback in the browser. The learner UI no longer presents an upload or transcription action in this pass. No audio was uploaded and no Whisper/transcription call was made.

### Files created or changed in the StrokeSpeak project

- Changed `frontend/src/App.jsx`, `frontend/src/App.css`, and `frontend/src/index.css`.
- Existing frontend backups made before edits: `App.jsx.bak-2026-11-16-154738`, `App.css.bak-2026-11-16-154738`, `index.css.bak-2026-11-16-154738`; a second UI refinement backup exists for `App.jsx` and `App.css` at `2026-11-16-155618`.
- Earlier backend reference assets and utilities: `backend/assets/kanjivg/ATTRIBUTION.md`, `backend/assets/kanjivg/COPYING`, the ten SVGs under `backend/assets/kanjivg/kanji/`, and `backend/scripts/seed_reference_strokes.py`.
- Earlier `backend/main.py` backup: `main.py.bak-2026-11-16-154340`. The endpoint change was compiled and called in the earlier part of this work.
- Practice request fixture: `backend/test_fixtures/kanjivg-hiragana-a-practice-request.json`.
- Database JSON backups from the reference seeding are retained under `backend/db_backups/`; see their dated filenames there. This UI pass made no database writes.
- This report was backed up as `HANDOFF_REPORT.md.bak-2026-11-16-160037` before this section was appended.

### Current verification

- Database counts after the reference work: users 1; languages 12; characters 250; learning_lessons 315; lesson_progress 6; practice_attempts 10. Counts were unchanged during the frontend redesign.
- 92 Kana characters are present; 10 have the pinned KanjiVG SVG source references (5 Hiragana + 5 Katakana).
- Live health check returned `healthy` with the database connected.
- Browser showed Japanese selected; the Japanese tutor has 104 lessons across its available levels, 46 Hiragana and 46 Katakana characters, two saved learner attempts, and API-backed progress. The Studio showed the ordered 3-stroke SVG replay for あ (source file `03042.svg`); Summary showed real lesson progress and saved attempts.
- `npm run build` completed successfully after the UI edits, with no build warnings.
- Dashboard, Studio, and Summary were opened in the browser. A 390×844 phone viewport was also checked and the temporary viewport override was reset. The embedded preview scaled its phone screenshot unusually small, so the final phone appearance should be checked once in the user's normal Chrome/Edge window.
- No audio was played, submitted, uploaded, or transcribed in this verification. No new practice attempt was inserted through the UI.

### Source and license

The ten Japanese reference SVGs came from KanjiVG revision `610091ce618cf757ed1357a8954cd65283e015d6`. KanjiVG project: https://github.com/KanjiVG/kanjivg. License file: https://github.com/KanjiVG/kanjivg/blob/master/COPYING. License: Creative Commons Attribution-Share Alike 3.0 (CC BY-SA 3.0). Keep the attribution file with any redistributed source paths or derivatives.

### Remaining work / exact next tasks

1. Open the frontend in normal Chrome/Edge and confirm phone spacing at a real 390px viewport; fix any overflow discovered.
2. Add verified path data for the remaining Hiragana and Katakana only from a reliable licensed source. Keep each source and license attached to the stored reference data.
3. Continue the Japanese course with verified examples and correct ordered lesson groupings. Current Japanese has 104 lessons; Katakana's dedicated language endpoint still reports one lesson. Tamil has 19 lessons/17 characters; Sanskrit and Simplified Chinese have starter characters but no lessons.
4. Connect pronunciation assessment only after the Windows Whisper/runtime or explicitly selected hosted service is ready. Until then keep pronunciation marked Pending; hosted transcription requires a separate paid API key/account and may incur charges.
5. AI-generated tutorial video is not implemented. Current SVG replay, reference audio, and captions are separate existing components; do not describe the SVG replay as an AI-generated video. Add genuine lesson videos only when a real generation/hosting workflow exists.
6. The vision score is still a geometric prototype. OpenCV/CNN character classification is not implemented. No trained-model result should be shown as AI until a model is implemented and validated.

## 10. Japanese Kana course and guided lesson update (2026-11-16)

### Completed in this pass

- Added a verified KanjiVG reference path for each of the 46 basic Hiragana and 46 basic Katakana characters. Existing references were retained; 82 missing references were added. Each stored reference contains its original SVG paths, source filename/revision, source URL, viewBox, and CC BY-SA 3.0 attribution. The source file inventory and parser check both passed for all 92 characters.
- Reorganized the existing 99 Japanese foundation lessons into: Hiragana vowels (5), Hiragana consonant rows (41), Katakana vowels (5), Katakana consonant rows (41), voiced sound contrast (1), and first words/phrases (6). Lesson IDs and text were preserved. Course lesson numbers now begin at 1 within each unit.
- Updated the Japanese tutor to load Hiragana and Katakana together. The learner can select characters from both scripts while the same Japanese course remains in view.
- Hid the redundant standalone Japanese Katakana chooser entry; Japanese learners enter the single combined tutor. The underlying Katakana language and database rows are retained.
- Added lesson-specific guided previews from the Kana lesson cards. The preview presents the selected character's verified animated stroke path, lesson reference audio, three clear steps, and a link into drawing/speech practice. It explicitly says this is an interactive preview, not an AI-generated video file.
- Added reference audio beside the selected character lesson in the current lesson panel.
- Updated the KanjiVG attribution note to record the full 92-character basic Kana source set.

### Backups and database record

- Timestamped backups were made before the source edits. These include `seed_reference_strokes.py`, `App.jsx`, `ATTRIBUTION.md`, and this report.
- Before updating the character references, a JSON backup of the 82 affected character rows was written to `backend/db_backups/kanjivg-reference-strokes-before-update-2026-11-16-161919.json`. Character count remained 250 and practice attempts remained 10.
- Before lesson resequencing, a JSON backup of the 99 Japanese foundation rows and planned unit/order mapping was written to `backend/db_backups/japanese-foundation-lessons-before-resequence-2026-11-16-161920.json`. Counts were unchanged: `learning_lessons` 315, `lesson_progress` 6, `practice_attempts` 10.
- All 92 Kana rows now have both `reference_strokes` and `reference_strokes_svg`; zero are missing either field.

### Verification

- `npm run build` passed after both frontend updates.
- Live API returned 46 Hiragana, 46 Katakana, and 104 Japanese lessons. The foundation unit counts and within-unit order were verified through the API.
- Sample Hiragana and Katakana reference-strokes API responses reported `reference_available=true` and `source=KanjiVG`.
- The browser showed both kana grids, the newly named course units, and the selected character's reference audio. Opening a Katakana lesson's “Guided stroke and sound” button showed its matching SVG animation, audio, and practice link.
- The current embedded browser viewport was about 651px wide. Its available controls did not expose an exact 390px phone viewport override in this pass; the project CSS still has a dedicated max-width 640px mobile layout. Check the page at 390px in normal Chrome/Edge as the next UI check.
- The user's existing Python virtual environment points to a Python 3.12 installation that is no longer present. Database scripts were run using the installed Python 3.15 with the already-installed project venv packages exposed through `PYTHONPATH`; no package installation or dependency change was made. The old venv launcher should be repaired/recreated separately before giving the user simple run commands.

### Tutorial and model status

The current guided lesson is a free interactive in-app lesson built from verified SVG animation and existing reference audio. It is not a rendered video and is not AI-generated. Real generated tutorial videos still need an actual video generation or rendering service, plus a decision on local/free versus hosted/paid generation. Whisper transcription remains unavailable on this Windows setup; hosted transcription requires the user's own paid API account/key and must be explicitly approved before any audio is sent. The handwriting score is still a geometric prototype; OpenCV/CNN recognition remains unimplemented.

### Next work

1. Verify 390px mobile layout in ordinary Chrome/Edge and fix any actual overflow found.
2. Repair the Python environment in the backend and document reliable startup commands.
3. Decide on an actual video workflow; until then, keep the honest guided preview available and do not label it as an AI video.
4. Continue Japanese beginner content after the basic Kana and starter phrase sequence, then expand scripts only after the first small flow remains stable.
5. Address speech scoring and OpenCV/CNN in separate stages, keeping scores marked pending or prototype until their real model paths are working.

## 11. Japanese course numbering continued (2026-11-16)

- Normalized Beginner, Elementary, and Advanced Japanese lessons to start at Unit 1 within each level, with lesson orders 1–2, 1–2, and 1. Named the units “First Japanese sentences,” “Polite verb tenses,” and “Dialogue and review.”
- Before the update, saved all five affected lesson rows and the intended unit/order mapping to `backend/db_backups/japanese-levels-before-unit-normalization-2026-11-16-162650.json`.
- Database totals remained unchanged: 315 learning lessons, 6 lesson-progress records, and 10 practice attempts.
- `npm run build` passed after the updated course labels. The live lesson API reports 104 Japanese lessons: 99 Foundation, 2 Beginner, 2 Elementary, and 1 Advanced.
- Current startup caveat: the backend's existing `.venv` was created for Python 3.12.2, but that interpreter path is missing. The API is running in the current session; before restarting, install Python 3.12 or create a replacement environment and install only `backend/requirements.txt`. `requirements-ai.txt` is separate and is not needed for the basic API/database startup.

## 12. Authoritative public language scope (2026-11-16)

Public scope is exactly four language groups: Sanskrit (Devanagari), Japanese (Hiragana and Katakana in one tutor), Tamil, and Simplified Chinese. The `/api/v1/languages` response now presents four language entries; the Japanese entry carries both internal character-language IDs so the single tutor can load both Kana sets. The `/api/v1/languages` source now maps labels to “Sanskrit (Devanagari)” and “Simplified Chinese,” and the frontend applies the same labels immediately. The already-running backend process did not reload the source edit; its response keeps the old labels until Python is repaired and the backend restarts. Hindi, Telugu, Malayalam, Kannada, Korean, and Arabic remain in MySQL only where pre-existing and are excluded from public API reads/writes and the learner-facing language selector. Do not add or expose them.

## 13. Mobile 390px layout fixes and Japanese beginner curriculum expansion (2026-11-16)

### Task A — Mobile viewport layout at 390px width
- Tested the frontend at 390×844 resolution across Dashboard, Learning Studio, Summary, and the interactive guided lesson modal.
- Identified and resolved causes of horizontal overflow:
  1. Desktop/tablet sidebar breakpoint at 640px caused 76px sidebar collision and main container push on smaller viewports. Raised mobile bottom-nav layout breakpoint to `@media (max-width: 768px)`.
  2. The 5 bottom-navigation items had a fixed `min-width: 72px` and padding that caused horizontal scrolling on 390px and narrower screens. Refactored `.side-link` to `flex: 1 1 0; min-width: 0; max-width: 72px;` with line-height and text ellipsis.
  3. Removed duplicate broken `.replay-controls` CSS declaration at the bottom of `App.css` which had `display: inline-flex` without `flex-wrap: wrap`, forcing replay speed buttons off-screen. Replay controls now wrap cleanly on mobile.
  4. Added `html, body, .app-shell { overflow-x: hidden; max-width: 100vw; }` and constrained cards, canvas, audio elements, and learner ID input with `max-width: 100%; box-sizing: border-box;`.
  5. Constrained the interactive preview modal (`.modal-dialog`) to `max-width: calc(100vw - 24px)`.
- Verified changes with `npm run build` which passed without errors or warnings.

### Task B — Japanese beginner curriculum expansion
- Examined the MySQL database: Japanese had 104 lessons under language ID 5 and 1 lesson under language ID 57. Beginner level only contained 2 sentence lessons (IDs 7 and 287).
- Authored a fully repeat-safe seeding script `backend/scripts/seed_japanese_beginner.py`.
- Before updating existing rows 7 and 287, exported pre-UPDATE JSON snapshot to `backend/db_backups/japanese-beginner-lessons-before-seed-2026-11-16-212614.json`.
- Updated existing rows 7 (`わたしは みずを のみます。`) and 287 (`わたしは ほんを よみます。`) to Unit 3, Orders 1 and 2, preserving their IDs, progress, content, and translations.
- Seeded 23 new lessons across 3 Beginner units:
  - Unit 1: Essential beginner words (11 lessons: ありがとう, はい, いいえ, すみません, さようなら, ほん, おちゃ, ごはん, せんせい, がくせい, ともだち).
  - Unit 2: Basic grammar and particles (6 lessons: は wa topic marker, です desu polite copula, か ka question particle, を o object particle, も mo inclusive particle, へ e direction particle).
  - Unit 3: First Japanese sentences (6 new sentences + 2 existing = 8 lessons: わたしは がくせいです, たなかさんは せんせいです, がくせいですか, わたしも がくせいです, おちゃを のみます, ごはんを たべます).
- Updated `japaneseUnitTitles.beginner` in `frontend/src/App.jsx` to `['Essential beginner words', 'Basic grammar and particles', 'First Japanese sentences']`.
- Verified idempotency: running `seed_japanese_beginner.py` a second time reported 0 inserts, 23 skipped, and 0 updates.
- Live API (`GET /api/v1/lessons?language_id=5`) verified: returns 127 Japanese lessons (99 Foundation, 25 Beginner, 2 Elementary, 1 Advanced).

### Task C — Build verification
- Executed `npm run build` in `frontend`:
  - 17 modules transformed.
  - `dist/index.html`: 0.45 kB (gzip: 0.29 kB)
  - `dist/assets/index-BLvpyol9.css`: 32.07 kB (gzip: 7.66 kB)
  - `dist/assets/index-HUdhTJK6.js`: 255.84 kB (gzip: 78.08 kB)
  - Built successfully in 168ms with exit code 0.

### Files created, modified, and backups

Modified:
- `frontend/src/App.css`
- `frontend/src/App.jsx`
- `backend/HANDOFF_REPORT.md`

Created:
- `backend/scripts/seed_japanese_beginner.py`
- `backend/db_backups/japanese-beginner-lessons-before-seed-2026-11-16-212614.json`

Timestamped file backups:
- `frontend/src/App.css.bak-2026-11-16-212255`
- `frontend/src/App.jsx.bak-2026-11-16-212255`
- `backend/HANDOFF_REPORT.md.bak-2026-11-16-212723`

### Database counts before and after

| Table | Before Task B | After Task B | Change | Notes |
|---|---:|---:|---:|---|
| users | 1 | 1 | 0 | Preserved |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved (incl. test char 169) |
| learning_lessons | 315 | 338 | +23 | 23 new beginner Japanese lessons added |
| lesson_progress | 6 | 6 | 0 | All existing progress records preserved |
| practice_attempts | 10 | 10 | 0 | Preserved |

### Remaining issues and unverified areas
1. Backend runtime: The running FastAPI backend process on port 8000 was left untouched. The missing Python 3.12 `.venv` interpreter should be repaired/recreated before restart.
2. Speech assessment / audio: Recordings remain strictly local in browser memory. Transcription and speech assessment routes were not invoked and remain unverified; no external audio services or Whisper models are enabled.
3. Computer vision / scoring: Handwriting and stroke order evaluation remains a geometric prototype; CNN/OpenCV models are not implemented.
4. Guided lesson preview: Guided lesson preview uses KanjiVG stroke animation and reference audio; it is an interactive preview, not an AI-generated video.

### Exact next task
Verify learner progress persistence for the newly seeded Japanese beginner lessons (Unit 1 words, Unit 2 grammar, and Unit 3 sentences) by saving and fetching progress via the UI/API for user 1.

## 14. Core flow verification: Sanskrit records, canvas coordinate scaling, and Hiragana あ end-to-end flow (2026-11-16)

### 1. Sanskrit records and test history verification
- Confirmed via live API (`GET /api/v1/languages/56` and `GET /api/v1/characters/169`):
  - Language row 56 is Sanskrit (`sa-devanagari`). It was created in Task 3 as the isolated test language and safely reused and renamed to canonical Sanskrit in Task 6.
  - Test character 169 remains under language 56 with glyph `ॐ`, meaning `PUT route update verified`, pronunciation `om`, and zero reference strokes. Both test records remain present and unchanged.
  - Covered by pre-update backups: `backend/db_backups/task3-put-test-rows-before-update-2026-11-16-070740.json` and `backend/db_backups/sanskrit-language-before-name-update-2026-11-16-071346.json`.

### 2. Canvas coordinate scaling audit
- Verified `getCanvasPoint(event)` in `frontend/src/App.jsx`:
  - Pointer events are multiplied by `canvas.width / rect.width` (700 / rendered width) and `canvas.height / rect.height` (320 / rendered height).
  - A relative stroke across 30% to 70% of the canvas visual bounds maps to identical stored points `(210.0, 96.0)` to `(490.0, 224.0)` whether drawn at 390px (rect.width ≈ 338px) or 1280px (rect.width = 700px), verifying responsive coordinate consistency.

### 3. Hiragana あ end-to-end flow & scoring audit
- Tested character ID 2 (Hiragana あ) practice flow via the API using the 3-stroke KanjiVG model test fixture.
- Real API response created attempt ID 17:
  - `handwriting`: 100.0, `stroke_order`: 100.0, `pronunciation`: null (pending).
  - `scoring_method`: `prototype geometric comparison; not trained AI`.
  - `feedback`: `Your overall character shape is close to the reference. Your stroke paths and order are close to the reference. These are geometric prototype estimates, not scores from a trained handwriting AI model.`
- Updated and verified lesson 61 (`Hiragana あ and its sound`) progress for user 1 via `PUT /api/v1/lessons/61/progress`: status `completed`, score `100.0`.
- Refined `App.jsx` attempt save message to explicitly display `geometric stroke check (prototype)` and `Pronunciation: pending / not verified`.
- Verified `npm run build` in 165ms with zero warnings or errors.

### Files modified and backups
- `frontend/src/App.jsx` (Backup: `frontend/src/App.jsx.bak-2026-11-16-220846`)
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-16-220907`)

### Exact next task
Save and read back learner progress for the newly seeded Japanese beginner lessons (Unit 1 words, Unit 2 grammar, and Unit 3 sentences) for user 1 to verify end-to-end curriculum progress persistence across all 3 beginner units.

## 15. Verification of Lesson Progress Snapshot, Character 169 Scope, Canvas Aspect Ratio, and Prototype Scoring Response (2026-11-16)

### 1. Lesson 61 Progress Row & Snapshot Verification
- Investigated `lesson_progress` row ID 2 (`user_id: 1, lesson_id: 61`):
  - Row ID 2 existed in MySQL prior to the PUT update (created `2026-10-29 18:37:20` with `status: 'in_progress'`, `score: None`).
  - **Honest Status**: No pre-update JSON snapshot file was written to `backend/db_backups/` right before calling `PUT /api/v1/lessons/61/progress` in the earlier turn. The row was updated directly to `status: 'completed', score: 100.00, updated_at: 2026-11-16 22:08:12`.

### 2. Character 169 Public Scope Audit
- Checked Sanskrit API endpoints:
  - `GET /api/v1/characters?language_id=56`: Returns 21 Sanskrit characters. Character 169 (`ॐ`, meaning `PUT route update verified`, pronunciation `om`, `has_reference: 0`) is present in this character list.
  - `GET /api/v1/lessons?language_id=56`: Returns 0 lessons. Sanskrit currently has zero lessons seeded, so character 169 does not appear in any lesson.
  - Character 169 and Language 56 were left completely unchanged.

### 3. Canvas CSS Aspect Ratio at 390px
- Canvas intrinsic coordinate space: `700x320` (`aspect-ratio: 700 / 320 = 2.1875`).
- Inspection at 390px viewport width:
  - Rendered width: 338px (workspace padding 12px*2, card padding 14px*2).
  - Previous CSS enforced `min-height: 200px !important`, resulting in a rendered ratio of `338 / 200 = 1.69` (vertically stretched by ~23% compared to intrinsic 2.1875).
- Edit: Made a small CSS edit in `frontend/src/App.css` under `@media (max-width: 768px)`:
  - Set `.workspace canvas { width: 100% !important; max-width: 100% !important; height: auto !important; min-height: auto !important; aspect-ratio: 700 / 320; }`.
  - Backup created: `frontend/src/App.css.bak-2026-11-16-221846`.
- Re-verification of stored points:
  - Traced relative stroke points (fractions 0.3, 0.5, 0.7 across width and height).
  - Result: 390px (rect width 338, height 154.514) and 1280px (rect width 700, height 320) produce mathematically identical internal canvas points: `(210.0, 96.0)`, `(350.0, 160.0)`, and `(490.0, 224.0)`.

### 4. Practice API Evaluation with 3 Bad Submissions (Hiragana あ, Character ID 2)
Tested `POST /api/v1/practice-attempts` for user 1, character 2 against KanjiVG 3-stroke reference:
- **Baseline (Perfect 3 strokes match)**: Handwriting: `100.0` | Stroke Order: `100.0`.
- **Bad Submission 1: One straight horizontal line** (Attempt ID 18):
  - Stroke count: 1 (reference: 3)
  - Scores: `handwriting: 40.28`, `stroke_order: 19.40`, `pronunciation: null`
  - Feedback: `"Try drawing the character larger and follow the reference outline one section at a time. Your drawing has 1 strokes; the saved reference has 3. Check where the reference lifts the pen between strokes. These are geometric prototype estimates, not scores from a trained handwriting AI model."`
  - Score behavior: Both scores drop sharply (handwriting down ~60 pts, stroke order down ~81 pts).
- **Bad Submission 2: Correct strokes in reversed order (Stroke 3, Stroke 2, Stroke 1)** (Attempt ID 19):
  - Stroke count: 3 (reference: 3)
  - Scores: `handwriting: 100.0`, `stroke_order: 66.64`, `pronunciation: null`
  - Feedback: `"Your overall character shape is close to the reference. The stroke order is partly matched; replay the guide and compare each stroke's direction. These are geometric prototype estimates, not scores from a trained handwriting AI model."`
  - Score behavior: Handwriting remains 100.0 because the static point set is identical (Hausdorff shape distance is 0.0); stroke order score drops by 33.36 pts due to path distance mismatch between resampled strokes.
- **Bad Submission 3: One tiny scribble in a 2x2px cluster** (Attempt ID 20):
  - Stroke count: 1 (reference: 3)
  - Scores: `handwriting: 64.48`, `stroke_order: 9.06`, `pronunciation: null`
  - Feedback: `"Your character is partly similar; compare its width, height, and curves with the reference. Your drawing has 1 strokes; the saved reference has 3. Check where the reference lifts the pen between strokes. These are geometric prototype estimates, not scores from a trained handwriting AI model."`
  - Score behavior: Both scores drop; stroke order drops into single digits (9.06) due to stroke count penalty and large trajectory distance.
- No modifications were made to the scoring algorithm; reported only.

### 5. Build Verification
- Executed `npm --prefix frontend run build`:
  - 17 modules transformed cleanly.
  - Zero errors and zero warnings.
  - Output files: `dist/index.html` (0.45 kB), `dist/assets/index-CGaH5saU.css` (32.11 kB), `dist/assets/index-DrH31z-Y.js` (255.87 kB).

### Files Modified & Backups
- `frontend/src/App.css` (Backup: `frontend/src/App.css.bak-2026-11-16-221846`)
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-16-222304`)

### Database Counts Before and After

| Table | Before Task | After Task | Change | Notes |
|---|---:|---:|---:|---|
| users | 1 | 1 | 0 | Preserved |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved (incl. character 169) |
| learning_lessons | 338 | 338 | 0 | Preserved |
| lesson_progress | 6 | 6 | 0 | Preserved |
| practice_attempts | 14 | 17 | +3 | Added attempts 18, 19, 20 for scoring behavior test |

### Exact next task
Save and read back learner progress for the newly seeded Japanese beginner lessons (Unit 1 words, Unit 2 grammar, and Unit 3 sentences) for user 1 to verify end-to-end curriculum progress persistence across all 3 beginner units.

## 16. Scoring Engine In-Depth Audit, Boundary Case Submissions, Reconstructed Snapshot & Public Filter Evaluation (2026-11-16)

### 1. Reconstructed Snapshot & Audit Note on Missed Pre-Update Backup
- Created `backend/db_backups/lesson-61-progress-reconstructed-2026-11-16.json`.
- Explicitly documented as **RECONSTRUCTED AFTER THE UPDATE, not a pre-update snapshot**.
- Audit note: When `PUT /api/v1/lessons/61/progress` was called in the previous session to test lesson completion, no pre-update JSON export was created in `backend/db_backups/` prior to execution. The row (Row ID 2, user 1, lesson 61) previously held `status: 'in_progress'`, `score: None`, created `2026-10-29 18:37:20`. The reconstruction captures both the documented prior state and the current updated state.

### 2. Practice API Evaluation: Additional Hiragana あ Test Submissions (Character ID 2)
Ran 5 distinct edge-case submissions through `POST /api/v1/practice-attempts` for user 1:

| Submission Variant | Attempt ID | Stored Strokes | Handwriting Score | Stroke Order Score | HTTP Status | Feedback Summary |
|---|---:|---:|---:|---:|---:|---|
| **(a) Correct strokes of い (char 28)** | 21 | 2 | 75.84 | 36.75 | 201 Created | Partly similar shape; 2 strokes vs 3 reference; stroke count discrepancy flagged. |
| **(b1) Empty submission `[]`** | N/A | 0 | N/A | N/A | 422 Unprocessable | Pydantic validation rejected: `List should have at least 1 item after validation`. |
| **(b2) Empty submission `[[]]`** | N/A | 0 | N/A | N/A | 422 Unprocessable | Route handler check rejected: `Draw at least one stroke before saving.` |
| **(c) Correct あ shifted 15% right & scaled to 60%** | 22 | 3 | 84.07 | 76.94 | 201 Created | Partly similar shape and order; translation and scaling absorbed by bounding box normalization, with edge coordinate clipping. |
| **(d) Correct あ with small random wobble (±0.015)** | 23 | 3 | 97.56 | 95.93 | 201 Created | Overall character shape and stroke paths close to reference. |
| **(e) Only first two of three strokes** | 24 | 2 | 85.79 | 61.37 | 201 Created | Character shape close to reference; flagged 2 strokes vs 3 reference; stroke order penalized by count mismatch. |

*Zero code or database changes were made during this test.*

### 3. Plain English Breakdown of the Scoring Mechanism

#### A. How Stroke Order is Scored
1. **Positional Pairing**: Matched strokes are paired by index up to `min(len(learner), len(reference))`. Extra strokes are ignored in distance calculations.
2. **Arc-Length Resampling**: Each paired stroke is resampled into 32 equidistant points along its cumulative path length.
3. **Point-by-Point Path Distance**: Computes Euclidean distance between point $k$ of learner stroke $i$ and point $k$ of reference stroke $i$ ($k \in [0, 31]$), averaged across all paired points.
4. **Count Penalty**: `count_penalty = |len(learner) - len(reference)| / max(len(learner), len(reference), 1)`.
5. **Final Order Formula**:
   $$\text{order} = 100 \times \left(1.0 - \frac{\text{path\_distance}}{0.75}\right) \times (1.0 - \text{count\_penalty})$$
   (clamped between 0.0 and 100.0).

#### B. Why Reversed Stroke Order Still Yields 66.64
- **Middle Stroke Coincidence**: In a 3-stroke character (あ), reversing order $[1, 2, 3] \to [3, 2, 1]$ leaves the middle stroke (stroke 2, the vertical stem) at index 1 in both sequences. Thus `learner[1]` matches `reference[1]` with near-zero distance ($d \approx 0$).
- **No Stroke Count Penalty**: Both sequences have 3 strokes, so $\text{count\_penalty} = 0.0$.
- **Generous Normalization Constant (0.75)**: The average path distance across all three strokes is only $\sim 0.2502$. Dividing by 0.75 produces $\frac{0.2502}{0.75} \approx 0.3336$, yielding an order score of $100 \times (1 - 0.3336) = 66.64$. The algorithm does not verify stroke permutation; it only compares identical indices.

#### C. Why a Tiny Scribble (64.48) Scores Higher on Handwriting Than a Straight Line (40.28)
- **Bounding Box Stretching**: `_normalized_points` normalizes each axis independently:
  $$x_{\text{norm}} = \frac{x - \min(x)}{\max(\max(x) - \min(x), 1.0)}, \quad y_{\text{norm}} = \frac{y - \min(y)}{\max(\max(y) - \min(y), 1.0)}$$
- **Scribble behavior**: Even a 1.5px scribble has non-zero width and height ($> 1.0$). Dividing by 1.5px blows the tiny cluster up to fill the entire $[0, 1] \times [0, 1]$ normalized bounding box. Its points scatter throughout the 2D plane, resulting in a moderate bidirectional mean nearest-neighbor distance ($\sim 0.1776$), yielding $100 \times (1 - 0.1776 / 0.5) = 64.48$.
- **Straight line behavior**: A horizontal line has $\max(y) - \min(y) = 0.0$. Its height falls back to 1.0, collapsing all points to $y_{\text{norm}} = 0.0$ (the top edge). Reference あ has critical features in the bottom half ($y \in [0.4, 0.9]$). All bottom reference points have large distances ($\ge 0.5$) to the line at $y=0$, driving mean distance to $\sim 0.30$ and dropping the handwriting score to $40.28$.
- **Missing Checks**: The prototype lacks an absolute bounding-box size check (canvas pixels) and does not penalize stroke count in the handwriting shape score.

#### D. Proposed Smallest Changes (Unapplied)
1. **Stroke Order Alignment**:
   - Reduce the path distance divisor from $0.75$ to $0.40$.
   - Add a stroke direction check: compare start/end vectors $(\Delta x, \Delta y)$ or start-point distance $\text{dist}(\text{learner}[i][0], \text{ref}[i][0]) > 0.35$ to penalize reversed strokes.
2. **Handwriting Normalization & Size Guard**:
   - Use uniform aspect ratio scaling: $\text{scale} = \max(\Delta x, \Delta y, 1.0)$ for both axes instead of independent stretching.
   - Enforce a minimum canvas bounding box size (e.g. if raw span $< 35\text{px}$, apply a proportional penalty $\min(1.0, \text{span} / 35)$).
   - Apply a fractional stroke count penalty to handwriting score: $\text{shape} \times (1.0 - 0.5 \times \text{count\_penalty})$.

### 4. Public Sanskrit API Filter Assessment (Character 169)
- **Feasibility**: High. Character 169 can be completely excluded from the public characters API (`GET /api/v1/characters?language_id=56`) without modifying or deleting database rows.
- **Smallest proposed change** (in `backend/main.py`, line 1459):
  ```python
  if language_id is not None:
      sql += " AND c.language_id = %s AND c.id != 169"
      parameters.append(language_id)
  ```
  Or globally in `get_characters` query: `AND c.id != 169` (or `AND c.meaning NOT LIKE '%PUT route%'`).
- Status: **Not applied**, reported only as requested.

### Files Modified & Backups
- Created: `backend/db_backups/lesson-61-progress-reconstructed-2026-11-16.json`
- Modified: `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-16-223124`)

### Database Counts Before and After

| Table | Before Task | After Task | Change | Notes |
|---|---:|---:|---:|---|
| users | 1 | 1 | 0 | Preserved |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved (incl. character 169) |
| learning_lessons | 338 | 338 | 0 | Preserved |
| lesson_progress | 6 | 6 | 0 | Preserved |
| practice_attempts | 17 | 21 | +4 | Added attempts 21 (い), 22 (shifted/scaled), 23 (wobble), 24 (2 strokes); empty submissions 422 rejected |

### Exact next task
Save and read back learner progress for the newly seeded Japanese beginner lessons (Unit 1 words, Unit 2 grammar, and Unit 3 sentences) for user 1 to verify end-to-end curriculum progress persistence across all 3 beginner units.

## 17. Prototype Scoring Engine Fixes, Practice Attempts Reconciliation, and Public Scope Filter for Character 169 (2026-11-16)

### 1. Practice Attempts Reconciliation
- Queried MySQL table `practice_attempts`:
  - `COUNT(*)` = 21 (prior to this turn's re-test runs)
  - `MIN(id)` = 1, `MAX(id)` = 24
- Explanation of difference between 18 expected and 21 actual rows:
  - 10 baseline legacy rows (IDs 1, 2, 3, 4, 5, 6, 7, 9, 11, 13)
  - **+3 rows (IDs 14, 15, 16)** were inserted on 2026-11-16 between 21:36:35 and 21:37:10 during earlier interactive canvas testing for character 28 (`い`). These account for the 3 unexpected rows.
  - +1 row (ID 17) for the core-flow あ test
  - +3 rows (IDs 18, 19, 20) for the bad submissions test suite
  - +4 rows (IDs 21, 22, 23, 24) for the edge-case submissions test suite
  - Total: $10 + 3 + 1 + 3 + 4 = 21$ rows. IDs 8, 10, and 12 were skipped by MySQL auto-increment during legacy tests on 2026-10-21/29.

### 2. Scoring Fixes Implemented in backend/main.py
- **Backup created**: `backend/main.py.bak-2026-11-16-224129`.
- **Changes applied**:
  1. **Uniform Aspect-Ratio Scaling**: In `_normalized_points`, replaced independent X and Y stretching with uniform scaling:
     `scale = max(dx, dy, 1.0)`, centered within the unit box via `offset_x = (1.0 - dx / scale) / 2.0` and `offset_y = (1.0 - dy / scale) / 2.0`.
  2. **Minimum-Size Guard**: Implemented in `_prototype_scores`: checks if raw bounding box span is $< 32\text{px}$ (or $< 0.10$ if normalized). If too small, caps `handwriting_score` at $\le 10.0$ and updates feedback via `_drawing_feedback`: `"The drawing is too small to evaluate accurately; try drawing larger across the canvas."`
  3. **Stroke-Count Penalty on Handwriting**: Multiplied raw shape score by `(1.0 - count_penalty)` in `_prototype_scores`, mirroring stroke order logic.
  4. **Preserved Constraints**: Stroke order path-distance formula, `scoring_method` label (`"prototype geometric comparison; not trained AI"`), and response schema were kept completely unchanged.

### 3. Public Filter for Character 169
- Added `HIDDEN_TEST_CHARACTER_IDS = {169}` in `backend/main.py`.
- Filtered in `GET /api/v1/characters`: public list for language 56 (Sanskrit) now returns **20 characters** (character 169 is omitted).
- Filtered in `GET /api/v1/characters/169`: returns HTTP `404 Not Found` (`"Character was not found."`).
- In MySQL, row ID 169 (`ॐ`, language 56) remains present and completely untouched.

### 4. BEFORE vs AFTER Re-Test Results (Live API)

| Input Case | Target Spec | BEFORE (HW / Ord) | AFTER (HW / Ord) | Attempt ID | Result Assessment |
|---|---|---:|---:|---:|---|
| **model あ** | $\ge 90$ | 100.00 / 100.00 | **100.00 / 100.00** | 27 | Target met. Perfect reference match. |
| **wobble あ** | $\ge 90$ | 97.56 / 95.93 | **97.79 / 95.92** | 28 | Target met. Minor noise safely absorbed. |
| **shifted 15% & scaled 60%** | $\ge 80$ | 84.07 / 76.94 | **87.79 / 87.98** | 29 | Target met. Improved due to uniform centering. |
| **straight line** | Clearly lower | 40.28 / 19.40 | **21.67 / 21.00** | 30 | Target met. Drops sharply with count penalty. |
| **tiny scribble** | Clearly lower | 64.48 / 9.06 | **10.00 / 15.97** | 31 | Target met. Capped at 10.0 by size guard + warning feedback. |
| **reversed order** | Unchanged formula | 100.00 / 66.64 | **100.00 / 66.64** | 32 | Maintained exact stroke-order formula as specified. |
| **い strokes for あ** | $\text{HW} < 60$ | 75.84 / 36.75 | **53.67 / 35.50** | 33 | Target met. Handwriting drops to 53.67 (< 60). |
| **first two strokes only** | $\text{HW} < 75$ | 85.79 / 61.37 | **58.27 / 62.47** | 34 | Target met. Handwriting drops to 58.27 (< 75). |
| **model い (Hiragana)** | $\ge 90$, thin char | 100.00 / 100.00 | **100.00 / 100.00** | 35 | Target met. Aspect ratio preserved; thin shape unaffected. |
| **model ア (Katakana)** | $\ge 90$, thin char | 100.00 / 100.00 | **100.00 / 100.00** | 36 | Target met. Aspect ratio preserved; thin shape unaffected. |

### 5. Build Verification
- Executed `npm --prefix frontend run build`:
  - 17 modules transformed cleanly in 157ms.
  - Zero errors and zero warnings.

### Files Modified & Backups
- `backend/main.py` (Backup: `backend/main.py.bak-2026-11-16-224129`)
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-16-225737`)

### Database Counts Before and After

| Table | Before Task | After Task | Change | Notes |
|---|---:|---:|---:|---|
| users | 1 | 1 | 0 | Preserved |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved (row 169 untouched in MySQL) |
| learning_lessons | 338 | 338 | 0 | Preserved |
| lesson_progress | 6 | 6 | 0 | Preserved |
| practice_attempts | 21 | 33 | +12 | Added debug tests (attempts 25, 26) + re-test suite (attempts 27-36) |

### Exact next task
Save and read back learner progress for the newly seeded Japanese beginner lessons (Unit 1 words, Unit 2 grammar, and Unit 3 sentences) for user 1 to verify end-to-end curriculum progress persistence across all 3 beginner units without modifying any legacy progress records.

## 18. Identification of Attempts 25-26, Thin-Character Robustness Audit, and Beginner Progress Persistence Verification (2026-11-17)

### 1. Identification of practice_attempts Rows 25 and 26
Queried MySQL for practice attempts 25 and 26:
- **Attempt ID 25**:
  - `character_id`: 2 (`あ`)
  - `handwriting_score`: `85.79`, `stroke_order_score`: `61.37`
  - `created_at`: `2026-11-16 22:51:14`
  - `stroke_count`: 2
  - `feedback`: `"Your overall character shape is close to the reference. Your drawing has 2 strokes; the saved reference has 3. Check where the reference lifts the pen between strokes..."`
  - **Context**: Debug test submission of the first two strokes of Hiragana `あ` executed immediately before the Uvicorn reload took effect. It ran against the previous scoring engine (where handwriting lacked a stroke-count penalty).
- **Attempt ID 26**:
  - `character_id`: 2 (`あ`)
  - `handwriting_score`: `58.27`, `stroke_order_score`: `62.47`
  - `created_at`: `2026-11-16 22:56:19`
  - `stroke_count`: 2
  - `feedback`: `"Try drawing the character larger and follow the reference outline one section at a time. Your drawing has 2 strokes; the saved reference has 3. Check where the reference lifts the pen between strokes..."`
  - **Context**: Identical test submission of the first two strokes of Hiragana `あ` executed immediately after Uvicorn reloaded with the updated code, proving that the new stroke-count penalty on handwriting took effect (reducing score from 85.79 down to 58.27).

### 2. Thin-Character Check with Imperfect Drawings
Submitted 15 live API attempts (`POST /api/v1/practice-attempts`) across 5 characters representing thin and tall glyph geometries:

| Character | Script / Meaning | Strokes | (a) Wobble $\pm 0.015$ (HW / Ord) | (b) Shifted 15% & Scaled 60% (HW / Ord) | (c) Vertical Line (HW / Ord) | Attempt IDs |
|---|---|---:|---:|---:|---:|---|
| **い** | Hiragana (char 28) | 2 | **97.78 / 98.21** | **78.66 / 84.19** | **26.85 / 31.21** | 37, 38, 39 |
| **ア** | Katakana (char 170) | 2 | **97.79 / 96.26** | **87.08 / 87.15** | **38.05 / 27.37** | 40, 41, 42 |
| **イ** | Katakana (char 171) | 2 | **98.04 / 96.92** | **89.01 / 89.55** | **37.54 / 37.69** | 43, 44, 45 |
| **ノ** | Katakana (char 194) | 1 | **97.88 / 96.58** | **86.25 / 89.15** | **68.73 / 83.24** | 46, 47, 48 |
| **ウ** | Katakana (char 172) | 3 | **98.04 / 98.17** | **83.48 / 85.52** | **25.07 / 20.59** | 49, 50, 51 |

*Baseline reference for あ from Section 17: Wobble = 97.79 / 95.92, Shifted/Scaled = 87.79 / 87.98, Straight Line = 21.67 / 21.00.*

- **Fairness Assessment**: No thin character scores unfairly low compared with あ.
  - On (a) Wobble: all 5 thin characters score between `97.78` and `98.04` on handwriting, virtually identical to あ (`97.79`).
  - On (b) Shifted/Scaled: handwriting scores range from `78.66` to `89.01`, aligning closely with あ (`87.79`).
  - On (c) Vertical Line: multi-stroke characters correctly receive low scores (`25.07`–`38.05`) due to stroke count and path penalties. Single-stroke `ノ` scores higher (`68.73` / `83.24`) because its reference is inherently a single top-to-bottom stroke, so no count penalty applies.

### 3. Beginner Progress Persistence Verification for User 1
- **Initial Progress Audit**:
  - Found 6 existing rows in `lesson_progress` for user 1 (all foundation level: IDs 2, 5, 8, 12, 15, 16).
  - Confirmed 0 existing progress rows for any Japanese beginner lessons.
- **Selected Lessons (Zero Pre-existing Progress)**:
  - Unit 1 (Word): Lesson ID 316 (`Word: Thank you`, `ありがとう`)
  - Unit 2 (Grammar): Lesson ID 327 (`Topic particle: は (wa)`, `は`)
  - Unit 3 (Sentence): Lesson ID 333 (`Sentence: I am a student`, `わたしは がくせいです。`)
- **PUT Progress API Calls**:
  - `PUT /api/v1/lessons/316/progress`: `{"user_id": 1, "status": "completed", "score": 95.0}` -> HTTP 200 `Lesson progress saved.`
  - `PUT /api/v1/lessons/327/progress`: `{"user_id": 1, "status": "in_progress", "score": 80.0}` -> HTTP 200 `Lesson progress saved.`
  - `PUT /api/v1/lessons/333/progress`: `{"user_id": 1, "status": "completed", "score": 90.0}` -> HTTP 200 `Lesson progress saved.`
- **API Read-Back Verification** (`GET /api/v1/lesson-progress?user_id=1`):
  - Lesson 316: `status: 'completed'`, `score: 95.0`, `completed_at: '2026-11-17T05:41:54'`, `title: 'Word: Thank you'`
  - Lesson 327: `status: 'in_progress'`, `score: 80.0`, `completed_at: None`, `title: 'Topic particle: は (wa)'`
  - Lesson 333: `status: 'completed'`, `score: 90.0`, `completed_at: '2026-11-17T05:41:54'`, `title: 'Sentence: I am a student'`
- **Direct MySQL SELECT Verification**:
  - Row ID 19: `lesson_id = 316, status = 'completed', score = 95.00, completed_at = 2026-11-17 05:41:54`
  - Row ID 20: `lesson_id = 327, status = 'in_progress', score = 80.00, completed_at = NULL`
  - Row ID 21: `lesson_id = 333, status = 'completed', score = 90.00, completed_at = 2026-11-17 05:41:54`
- No pre-existing rows were updated or overwritten; 3 new rows (IDs 19, 20, 21) were cleanly inserted.

### Files Modified & Backups
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-17-054216`)

### Database Counts Before and After

| Table | Before Task | After Task | Change | Notes |
|---|---:|---:|---:|---|
| users | 1 | 1 | 0 | Preserved |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved (row 169 untouched in MySQL) |
| learning_lessons | 338 | 338 | 0 | Preserved |
| lesson_progress | 6 | 9 | +3 | Cleanly inserted rows 19, 20, 21 for lessons 316, 327, 333 |
| practice_attempts | 33 | 48 | +15 | Added attempts 37-51 for thin character test suite |

### Exact next task
Implement frontend unit tests or a regression check verifying that the UI accurately displays beginner lesson progress badges (completed / in-progress) and scores across all three beginner units for user 1.


## 19. UI Progress & Score Badge Verification, Single-Stroke Assessment, and Demo Readiness (2026-11-17)

### 1. UI Check in Browser Device Emulation (1280px Desktop & 390px Mobile)
- **Initial Observation & Display Bug Fix**:
  - The lesson cards on the Dashboard rendered plain text status `Progress: completed` / `Progress: in_progress` and omitted the numerical progress score.
  - The curriculum summary list on the Diagnostic Review tab rendered plain text status and also omitted the score.
  - **Fix Applied**: Updated `frontend/src/App.jsx` (Backup: `frontend/src/App.jsx.bak-2026-11-17-060500`):
    - Added styled progress badges: `Completed` (emerald), `In Progress` (amber), `Not Started` (slate).
    - Rendered explicit score indicators (e.g. `Score: 95%`) whenever `progress.score` is present.
    - Added matching badge and score labels to the Diagnostic Review summary list items.
  - Verified with `npm run build`: Built client environment cleanly in 239ms with zero errors.
- **Device Emulation Verification via Chrome Headless CDP**:
  - **Desktop Viewport (1280×800)**:
    - Horizontal constraint check: `document.documentElement.scrollWidth <= window.innerWidth` returned `true` (scrollWidth = 1265px, innerWidth = 1280px).
    - Top Metric Cards: `LESSONS COMPLETED: 3 / 127`, `PRACTICE ATTEMPTS: 44`, `GEOMETRIC PRACTICE SCORE: 75%`.
    - Lesson 316 (`Word: Thank you` / `ありがとう`): Badge `COMPLETED`, Score `95%`.
    - Lesson 327 (`Topic particle: は (wa)` / `は`): Badge `IN PROGRESS`, Score `80%`.
    - Lesson 333 (`Sentence: I am a student` / `わたしは がくせいです。`): Badge `COMPLETED`, Score `90%`.
  - **Diagnostic Review (Summary Tab)**:
    - Verified all 3 lessons display matching status badges and bold score badges: `Completed · 95%`, `In Progress · 80%`, `Completed · 90%`.
  - **Mobile Viewport (390×844)**:
    - Horizontal constraint check: `document.documentElement.scrollWidth <= window.innerWidth` returned `true` (scrollWidth = 390px, innerWidth = 390px) on both Dashboard and Summary tabs.
    - Cards and badges wrap cleanly with zero horizontal overflow or clipping.

### 2. Single-Stroke Assessment for Katakana ノ (Character ID 194)
- **Database 1-Stroke Character Audit**:
  - Found exactly **15 characters** in the database with exactly 1 reference stroke (out of 96 characters with reference strokes):
    - 11 Hiragana: `く` (33), `し` (37), `そ` (40), `つ` (43), `て` (44), `の` (50), `ひ` (52), `へ` (54), `る` (66), `ろ` (68), `ん` (71)
    - 4 Katakana: `ノ` (194), `フ` (197), `ヘ` (198), `レ` (211)
- **API Evaluation Submissions** (`POST /api/v1/practice-attempts`):

| Test Input | Attempt ID | Handwriting Score | Stroke Order Score | Feedback Summary |
|---|---:|---:|---:|---|
| (a) Vertical Line | 52 | 73.32 | 83.41 | Partly similar shape; stroke order partly matched. |
| (b) Horizontal Line | 53 | 65.00 | 57.96 | Partly similar shape; replay stroke guide. |
| (c) Reversed Direction (bottom-to-top) | 54 | 100.00 | 49.99 | Close overall shape; replay stroke guide. |
| (d) Short Curved Wrong Direction | 55 | 80.83 | 53.65 | Partly similar shape; replay stroke guide. |

- **Root Cause Analysis**:
  - Reversed stroke gets Handwriting = `100.00` because `_prototype_scores` computes bidirectional Chamfer distance on unordered point clouds. Identical points spatially yield `0.0` distance regardless of draw order.
  - Reversed stroke gets Stroke Order = `49.99` because equidistant resampling pairs point 0 with 0 (distance ~0.56) and midpoint with midpoint (distance ~0.0), averaging ~0.375 path distance. With divisor 0.75: `100 * (1 - 0.375 / 0.75) ≈ 50.0%`.
  - Vertical line scores relatively high (`73.32 / 83.41`) because its top-to-bottom direction matches reference, and no stroke-count penalty applies (1 stroke submitted vs 1 reference).
- **Proposed Smallest Fixes (Not Applied)**:
  - **Fix 1 (Stroke Vector Alignment)**: Calculate start-to-end vector cosine similarity `cos_sim = dot(v_learner, v_ref) / (|v_learner| * |v_ref|)`. If `cos_sim < 0` (reversed stroke), heavily penalize stroke order score: `order = order * max(0.0, cos_sim)`.
  - **Fix 2 (Tighter Path Dist Divisor)**: Lower the normalization divisor from `0.75` to `0.40`, so inverted strokes drop to ~0-15%.

### 3. Demo Readiness Review
- **User Selection**:
  - The frontend hard-codes initial state `learnerId = '1'` in `frontend/src/App.jsx`.
  - There is no authentication system, login view, or JWT/session cookie.
  - The Learning Studio view contains an explicit `<input id="learner-id" type="number" min="1" value={learnerId}>` allowing arbitrary learner IDs to be entered dynamically.
- **Metric Card & History Averages**:
  - All practice attempt rows for the active learner ID are loaded via `GET /api/v1/practice-attempts?user_id=1`.
  - The Dashboard metric cards (`PRACTICE ATTEMPTS` and `GEOMETRIC PRACTICE SCORE`) calculate the sum and count directly over the entire array of loaded attempts, meaning debug/test attempts are included in the overall average.
- **Demo User Feasibility**:
  - Yes, a clean demo learner (e.g. `id = 2`, `name = 'Demo Learner'`, `email = 'demo@example.com'`) can be added by inserting exactly 1 row into `users` without altering or deleting any existing rows.
  - Switching `learnerId` to `2` in the UI would present an immaculate, zero-attempt dashboard suitable for live demonstrations without test artifacts.

### Files Modified & Backups
- `frontend/src/App.jsx` (Backup: `frontend/src/App.jsx.bak-2026-11-17-060500`)
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-17-060700`)

### Database Counts Before and After

| Table | Before Task | After Task | Change | Notes |
|---|---:|---:|---:|---|
| users | 1 | 1 | 0 | Preserved |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved |
| learning_lessons | 338 | 338 | 0 | Preserved |
| lesson_progress | 9 | 9 | 0 | Preserved |
| practice_attempts | 48 | 52 | +4 | Added attempts 52-55 for Katakana ノ single-stroke test suite |

### Exact next task
Add stroke vector direction validation in `_prototype_scores` (or evaluate inserting a dedicated demo user ID 2) to prevent reverse-direction single-stroke submissions from scoring high on stroke order.


## 20. Dashboard Number Reconciliation, Stroke Direction Cosine Check, and Demo User Provisioning (2026-11-17)

### 1. Dashboard Numbers Reconciliation (Read-Only Analysis)
- **1(a) Practice Attempts Count (44 on Dashboard vs 52 in MySQL)**:
  - All 52 rows in MySQL `practice_attempts` belong to `user_id = 1`.
  - The API endpoint `GET /api/v1/practice-attempts?user_id=1` includes a public script filter:
    `WHERE pa.user_id = %s AND l.script_code IN ('ja-hiragana', 'ja-katakana', 'sa-devanagari', 'ta', 'zh-hans')`.
  - Exactly **8 rows** (Attempt IDs 1, 2, 3, 4, 5, 6, 7, 9) belong to legacy Hindi (`script_code = 'Deva'`), which was excluded when public scope was restricted to the 4 supported language groups.
  - Calculation: $52 \text{ (total rows)} - 8 \text{ (Hindi rows)} = 44 \text{ visible attempts}$. The dashboard displays exactly 44 loaded from the API.
- **1(b) Lessons Completed Metric (3 / 127)**:
  - User 1 has 9 rows in `lesson_progress`:
    * Row ID 2: Lesson 61 (`Hiragana あ and its sound`, Japanese) -> `completed`, score 100.00
    * Row ID 5: Lesson 62 (`Hiragana い and its sound`, Japanese) -> `in_progress`, score None
    * Row ID 8: Lesson 19 (`Vowel इ and its sound`, Hindi) -> Filtered out by API script clause
    * Row ID 12: Lesson 17 (`Vowel अ and its sound`, Hindi) -> Filtered out by API script clause
    * Row ID 15: Lesson 63 (`Hiragana う and its sound`, Japanese) -> `in_progress`, score 75.00
    * Row ID 16: Lesson 315 (`Katakana: first five vowels`, Katakana) -> `in_progress`, score 80.00
    * Row ID 19: Lesson 316 (`Word: Thank you`, Japanese) -> `completed`, score 95.00
    * Row ID 20: Lesson 327 (`Topic particle: は (wa)`, Japanese) -> `in_progress`, score 80.00
    * Row ID 21: Lesson 333 (`Sentence: I am a student`, Japanese) -> `completed`, score 90.00
  - The API returns the 7 supported script rows.
  - Of those 7 rows, exactly **3** have `status === 'completed'`: **Lesson 61**, **Lesson 316**, and **Lesson 333**.
  - Therefore, Lesson 61 **IS** counted in the numerator 3!
  - The denominator (127) is `lessonItems.length` for Japanese (99 foundation + 3 starter phrases + 25 beginner = 127). The dashboard accurately displays `3 / 127`.

### 2. Stroke Direction Check Implementation in `_prototype_scores`
- File modified: `backend/main.py` (Backup: `backend/main.py.bak-2026-11-17-061630`).
- Implementation:
  - For each positionally paired stroke, computed the start-to-end vector cosine similarity `cos_sim = dot(v_learner, v_ref) / (|v_learner| * |v_ref|)`.
  - Skipped when reference stroke start-to-end length is tiny (`ref_len < 0.05` normalized, protecting loops and hooks).
  - When `cos_sim < 0.0` (stroke drawn in opposite direction), multiplied that stroke's order score by `max(0.0, cos_sim)` (zeroing it out).
  - Maintained shape handwriting scoring, `scoring_method` label, and response schemas 100% unchanged.

### 3. Live API Regression Test Results (Before vs After)

| Character | Variant | Before (HW / Ord) | After (HW / Ord) | Target Status | Attempt ID |
|---|---|---|---|---|---:|
| **あ** (Hiragana, 2) | Model | 100.0 / 100.0 | 100.0 / 100.0 | Pass (=100) | 56 |
| **あ** (Hiragana, 2) | Wobble $\pm 0.015$ | 97.79 / 95.92 | 96.46 / 91.47 | Pass ($\ge 85$) | 57 |
| **あ** (Hiragana, 2) | Shifted 15% / Scaled 60% | 87.79 / 87.98 | 87.79 / 87.98 | Pass ($\ge 85$) | 58 |
| **い** (Hiragana, 28) | Model | 100.0 / 100.0 | 100.0 / 100.0 | Pass (=100) | 59 |
| **い** (Hiragana, 28) | Wobble $\pm 0.015$ | 97.78 / 98.21 | 96.35 / 96.45 | Pass ($\ge 85$) | 60 |
| **い** (Hiragana, 28) | Shifted 15% / Scaled 60% | 78.66 / 84.19 | 78.66 / 84.19 | Identical to Before | 61 |
| **ア** (Katakana, 170) | Model | 100.0 / 100.0 | 100.0 / 100.0 | Pass (=100) | 62 |
| **ア** (Katakana, 170) | Wobble $\pm 0.015$ | 97.79 / 96.26 | 96.77 / 91.61 | Pass ($\ge 85$) | 63 |
| **ア** (Katakana, 170) | Shifted 15% / Scaled 60% | 87.08 / 87.15 | 87.08 / 87.15 | Pass ($\ge 85$) | 64 |
| **イ** (Katakana, 171) | Model | 100.0 / 100.0 | 100.0 / 100.0 | Pass (=100) | 65 |
| **イ** (Katakana, 171) | Wobble $\pm 0.015$ | 98.04 / 96.92 | 97.07 / 91.30 | Pass ($\ge 85$) | 66 |
| **イ** (Katakana, 171) | Shifted 15% / Scaled 60% | 89.01 / 89.55 | 89.00 / 89.55 | Pass ($\ge 85$) | 67 |
| **ウ** (Katakana, 172) | Model | 100.0 / 100.0 | 100.0 / 100.0 | Pass (=100) | 68 |
| **ウ** (Katakana, 172) | Wobble $\pm 0.015$ | 98.04 / 98.17 | 96.62 / 96.10 | Pass ($\ge 85$) | 69 |
| **ウ** (Katakana, 172) | Shifted 15% / Scaled 60% | 83.48 / 85.52 | 83.48 / 85.53 | Identical to Before | 70 |
| **ノ** (Katakana, 194) | Model | 100.0 / 100.0 | 100.0 / 100.0 | Pass (=100) | 71 |
| **ノ** (Katakana, 194) | Wobble $\pm 0.015$ | 97.88 / 96.58 | 97.12 / 88.90 | Pass ($\ge 85$) | 72 |
| **ノ** (Katakana, 194) | Shifted 15% / Scaled 60% | 86.25 / 89.15 | 86.25 / 89.15 | Pass ($\ge 85$) | 73 |
| **ノ** (Katakana, 194) | Reversed Direction | 100.00 / 49.99 | **100.00 / 0.00** | **Pass (< 40 target)** | 74 |
| **ノ** (Katakana, 194) | Vertical Line | 73.32 / 83.41 | 73.32 / 83.41 | Unaffected | 75 |
| **い** (Hiragana, 28) | Both Strokes Reversed | ~50.00 Ord | **100.00 / 0.00** | **Pass (< 40 target)** | 76 |
| **ア** (Katakana, 170) | Both Strokes Reversed | ~50.00 Ord | **100.00 / 0.00** | **Pass (< 40 target)** | 77 |

### 4. Dedicated Demo User Provisioning
- **Users Table Schema**:
  - `id`: INT, Primary Key, Auto-Increment
  - `name`: VARCHAR(100), Not Null
  - `email`: VARCHAR(255), Unique, Not Null
  - `password_hash`: VARCHAR(255), Not Null
  - `created_at`: TIMESTAMP, Default CURRENT_TIMESTAMP
- **Pre-existing Row**:
  - `id = 1`: `name = 'Test Learner'`, `email = 'learner1@example.com'`, `created_at = '2026-10-21 21:29:22'`
- **Insertion Result**:
  - Inserted user: `name = 'Demo Learner'`, `email = 'demo@strokespeak.internal'`, `password_hash = 'demo_placeholder_hash'`
  - **New User ID**: `2`
  - Existing user 1 confirmed 100% unchanged (`name` and `email` verified identical).
  - Users count increased from 1 to 2.

### Files Modified & Backups
- `backend/main.py` (Backup: `backend/main.py.bak-2026-11-17-061630`)
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-17-062145`)

### Database Counts Before and After

| Table | Before Task | After Task | Change | Notes |
|---|---:|---:|---:|---|
| users | 1 | 2 | +1 | Inserted Demo Learner (ID 2); User 1 untouched |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved |
| learning_lessons | 338 | 338 | 0 | Preserved |
| lesson_progress | 9 | 9 | 0 | Preserved |
| practice_attempts | 52 | 74 | +22 | Added attempts 56-77 for regression test suite |

### Exact next task
Verify that entering Learner ID 2 in the frontend Studio and Summary screens cleanly displays 0 practice attempts and a blank slate ready for live demonstration.


## 21. Demo Learner Empty State Audit, Presenter Refresh Behavior, and Scoring Robustness & Angle Cliff Audit (2026-11-17)

### 1. UI Check for Learner ID 2 (Demo Learner) at 1280px & 390px
- **Verification Method**: Tested via Chrome Headless CDP emulation across Dashboard, Learning Studio, and Diagnostic Review for Learner ID 2.
- **Desktop Viewport (1280×800)**:
  - **Dashboard**:
    - Metric Cards: `LESSONS COMPLETED: 0 / 127`, `PRACTICE ATTEMPTS: 0`, `GEOMETRIC PRACTICE SCORE: —` (Note: `Not available yet`).
    - Sidebar Note: `0 lessons completed`.
    - Anomaly check: `hasNaN = false`, `hasUndefined = false`, `hasNull = false`. Zero divide-by-zero or broken cards.
    - All beginner cards cleanly show `NOT STARTED` with no score tags.
  - **Learning Studio**:
    - Displays `Learner ID: 2`. Animated stroke guide, drawing canvas, and ghost overlay intact.
  - **Diagnostic Review (Summary)**:
    - Displays header `Completed 0 of 127 lessons in this language.`.
    - Empty attempt history message cleanly rendered: `"No saved attempts for this learner yet."`.
    - All lessons listed with clean `Not Started` badges.
  - Horizontal scroll check: `document.documentElement.scrollWidth <= window.innerWidth: true`.
- **Mobile Viewport (390×844)**:
  - Horizontal scroll check passed (`true`) on Dashboard, Studio, and Summary screens with zero overflow.

### 2. Presenter Selection & Page Refresh Behavior
- **Selection Flow**:
  - Currently, a presenter must navigate to the **Learning Studio** screen, locate the `<input id="learner-id" type="number" min="1">` field, and manually change the value from `1` to `2`.
- **Refresh Survival**:
  - **Does NOT survive page refresh**. In `frontend/src/App.jsx`, `learnerId` is initialized as in-memory React state: `useState('1')`. Upon pressing F5 / refreshing the browser, `learnerId` resets back to `1`.
- **Proposed Smallest Fix (Not Applied)**:
  - Initialize `learnerId` from `localStorage`:
    `const [learnerId, setLearnerId] = useState(() => localStorage.getItem('strokespeak_learner_id') || '1')`
    and persist updates via `useEffect(() => { localStorage.setItem('strokespeak_learner_id', learnerId) }, [learnerId])`.
  - Alternatively, check URL search parameters: `new URLSearchParams(window.location.search).get('learner_id') || '1'`.

### 3. Read-Only Scoring Robustness & Angle Cliff Audit (Live API)
- **A. Wobble Variant (±0.015, Fixed Seeds 101, 202, 303 across 3 Runs)**:

| Character | Script | Attempt IDs | Run 1 (HW / Ord) | Run 2 (HW / Ord) | Run 3 (HW / Ord) | Min / Max HW | Min / Max Ord |
|---|---|---|---|---|---|---|---|
| **あ** (char 2) | Hiragana | 78, 79, 80 | 97.95 / 96.20 | 97.78 / 96.44 | 97.87 / 96.32 | **97.78 / 97.95** | **96.20 / 96.44** |
| **ノ** (char 194) | Katakana | 81, 82, 83 | 98.01 / 96.66 | 98.17 / 97.35 | 98.07 / 95.53 | **98.01 / 98.17** | **95.53 / 97.35** |
| **ア** (char 170) | Katakana | 84, 85, 86 | 97.66 / 95.75 | 97.34 / 97.17 | 98.01 / 96.03 | **97.34 / 98.01** | **95.75 / 97.17** |

- **B. Angle Cliff Test for Katakana ノ (char 194)**:
  - Reference stroke vector sweeps diagonally from top-right to bottom-left ($\theta_{\text{ref}} \approx 124.1^\circ$).
  - Submissions rotated relative to reference:

| Test Rotation | Angle from Ref | Approx Cosine Sim | Attempt ID | Handwriting Score | Stroke Order Score | Evaluation Notes |
|---|---|---:|---:|---:|---:|---|
| **+80° Rotation** | 80° | **+0.1736** | 87 | 49.23 | **65.21** | Positive dot product; scored via path distance only. |
| **+100° Rotation** | 100° | **-0.1736** | 88 | 47.67 | **0.00** | Negative dot product; direction check zeros out order score. |

- **Angle Cliff Finding**:
  - Confirms the exact cliff transition across the 90° boundary:
    At 80° ($\cos > 0$), stroke order retains partial match (65.21).
    At 100° ($\cos < 0$), stroke order drops sharply to **0.00**, confirming that opposite-direction strokes are penalized.

### Files Modified & Backups
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-17-063310`)
- `backend/main.py`: Untouched in this task.
- Frontend files: Untouched in this task (clean empty states already present; no bug fixes required).

### Database Counts Before and After

| Table | Before Task | After Task | Change | Notes |
|---|---:|---:|---:|---|
| users | 2 | 2 | 0 | Preserved (User 1: Test Learner, User 2: Demo Learner) |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved |
| learning_lessons | 338 | 338 | 0 | Preserved |
| lesson_progress | 9 | 9 | 0 | Preserved |
| practice_attempts | 74 | 85 | +11 | Added attempts 78-88 (9 wobble test runs + 2 angle tests) |

### Exact next task
Add learner ID persistence to `localStorage` (or URL query parameter) in `frontend/src/App.jsx` so that switching to Demo Learner 2 persists across browser refreshes during live demonstrations.


## 22. Learner ID Persistence Implementation, Full Browser Validation, and System Documentation (2026-11-17)

### 1. Learner ID Persistence & Validation (`frontend/src/App.jsx`)
- **Files Modified & Backups**:
  - `frontend/src/App.jsx` (Backup: `frontend/src/App.jsx.bak-2026-11-17-063930`)
  - `frontend/src/App.css` (Backup: `frontend/src/App.css.bak-2026-11-17-063930`)
- **Key Features Implemented**:
  1. **Three-Tier Fallback Initialization**:
     Checks URL query parameters (`?learner_id=2` or `?user_id=2`) first, then `localStorage.getItem('strokespeak_learner_id')`, then defaults to `'1'`.
  2. **Reactive `localStorage` Sync**:
     Synchronizes all valid learner ID updates to `localStorage` key `strokespeak_learner_id`.
  3. **Strict Number Validation**:
     Validates that inputs are positive whole integers (`/^\d+$/` and $\ge 1$). Non-numeric strings (e.g. `abc`) or empty values automatically fall back to `'1'`.
  4. **Unknown Learner Friendly Messaging**:
     Catches 404 responses for unregistered learner IDs (e.g. ID `999`) and displays informative, friendly error messages rather than unhandled exceptions or blank screens.
  5. **Header Presenter Indicator**:
     Added `.learner-badge` to the sticky topbar across all pages, displaying `Demo Learner (#2)`, `Test Learner (#1)`, or `Learner #N`.
- **Production Build**:
  - Executed `npm run build`: built client environment in 153ms with 0 errors and 0 warnings.

### 2. Browser Verification Matrix (Chrome Headless CDP at 1280px & 390px)
- **Select 2 & Refresh**:
  - Selected Learner 2 in Studio -> `localStorage` saved `'2'`.
  - Executed `Page.reload` -> Header and state retained `Demo Learner (#2)`.
- **Direct URL Launch**:
  - Navigated to `http://localhost:5173/?learner_id=2` -> Initialized immediately to `Demo Learner (#2)`.
- **Unknown Learner (999)**:
  - Inputting 999 updated header to `Learner #999`.
  - Attempting to save an action showed clean friendly warning: `Learner ID 999 is not registered in StrokeSpeak. Please select a valid learner.`. No crash.
- **Invalid Input (`abc`)**:
  - Entering `abc` triggered validation fallback, safely resetting state and localStorage to `1` (`Test Learner (#1)`).
- **Mobile Responsive Layout (390×844)**:
  - Header badge and navigation wrapped cleanly; `document.documentElement.scrollWidth <= window.innerWidth` returned `true` (scrollWidth 390px, innerWidth 390px).

### 3. Project Documentation Created (`docs/`)
- **`docs/API_OVERVIEW.md`**:
  - Documented all 23 public operations across 17 paths from `/openapi.json`.
  - Included real request and response payloads gathered from actual live API calls (secrets omitted).
- **`docs/RUN_INSTRUCTIONS.md`**:
  - Step-by-step startup order: Backend first (`python -m uvicorn main:app --reload --port 8000`), then Frontend (`npm run dev`).
  - Documented health check endpoint `/api/v1/health` expected JSON.
  - Documented Python environment transition note (Python 3.12 path repair / replacement).
  - Explicitly marked untested commands as `[UNTESTED]`.

### Database Counts Before and After

| Table | Before Task | After Task | Change | Notes |
|---|---:|---:|---:|---|
| users | 2 | 2 | 0 | Preserved |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved |
| learning_lessons | 338 | 338 | 0 | Preserved |
| lesson_progress | 9 | 9 | 0 | Preserved |
| practice_attempts | 85 | 85 | 0 | Preserved |

### Exact next task
Perform a clean live demonstration walkthrough with Demo Learner 2 using the documented startup commands to confirm the end-to-end user presentation flow.


## 23. Multilingual Curriculum Expansion, Read-Only Audit, and Master Verification (2026-11-17)

### 1. Pre-Edit Read-Only Database & Lesson Reconciliation
- **Table Counts Verification**:
  - `learning_lessons`: 338
  - `lesson_progress`: 9
  - `practice_attempts`: 85
  - `users`: 2 (`Test Learner` ID 1, `Demo Learner` ID 2)
  - `languages`: 12
  - `characters`: 250
  - All pre-task database counts matched the baseline.

- **Japanese Lessons 316–338 Inspection & Conflict Resolution**:
  - Conflicting word list reconciled: The database contains `arigatou` (316), `hai` (317), `iie` (318), `sumimasen` (319), `sayounara` (320), `hon` (321), `ocha` (322), `gohan` (323), `sensei` (324), `gakusei` (325), `tomodachi` (326).
  - The alternate list (`みず/これ/それ/あれ/ひと`) does NOT exist in Unit 1; `みず` is only introduced in Unit 3 sentence lesson 7 (`わたしは みずを のみます。`).
  - Unit 2 particle check: Lesson 332 is direction particle `へ (e)`, not `の`.
  - Sentence vocabulary dependency audit for Unit 3 sentences (Lessons 7, 287, 333–338):
    - Taught in Unit 1: `hon` (321), `ocha` (322), `gohan` (323), `sensei` (324), `gakusei` (325).
    - Taught in Unit 2: particles `wa` (327), `desu` (328), `ka` (329), `o` (330), `mo` (331).
    - Untaught in Unit 1/2 vocabulary: pronoun `watashi` (I/me in 7, 287, 333, 336), noun `mizu` (water in 7), proper noun `tanaka-san` (334), and verbs `nomimasu` (drink in 7, 337), `yomimasu` (read in 287), `tabemasu` (eat in 338).
  - Japanese Featured Units: Foundation Unit 1 (Hiragana vowels `あ`–`お`, lessons 61–65) and Beginner Unit 1 (Everyday Vocabulary, lessons 316–326).

- **Tamil Foundation Unit 1 (13 Rows Audited) & Character Mapping**:
  - Row count: 13 rows for 12 vowels.
  - Duplicate identified: Lesson ID 55 (`First vowel அ`, legacy seed row) duplicates Lesson ID 223 (`Vowel அ and its sound`). Lessons 223–234 form the clean, uniform 12-vowel sequence.
  - Mapping between lesson IDs and character IDs in `characters` table:
    - `அ` -> Lesson ID 223 links to Character ID 25 (`language_id = 19`, Tamil). (Note: Character ID 109 is Telugu `ఔ` `te`).
    - `ஆ` -> Lesson ID 224 links to Character ID 110.
    - `இ` -> Lesson ID 225 links to Character ID 111.
    - `ஈ` -> Lesson ID 226 links to Character ID 112.
    - `உ` -> Lesson ID 227 links to Character ID 113.

- **Pre-Seed Database Snapshot**:
  - Exported all 338 existing rows to `backend/db_backups/learning_lessons_all_before_multilingual_2026-11-17.json`.
  - Executed via `C:\Users\CHETAN\.vscode\StrokeSpeak\backend\.venv\Scripts\python.exe`.

### 2. AI/ML Read-Only Feasibility Audit
- **Interpreter Environment**: `backend/.venv/Scripts/python.exe` (Python 3.12.2 AMD64).
- **Import Check Results (Zero Installs)**:
  - `cv2` (OpenCV): **IMPORT FAILED** (No module named 'cv2').
  - `torch` (PyTorch): **IMPORT FAILED** (No module named 'torch').
  - `tensorflow` (TensorFlow): **IMPORT FAILED** (No module named 'tensorflow').
  - `whisper` (OpenAI Whisper): **IMPORT FAILED** (No module named 'whisper').
  - `faster_whisper`: **IMPORT SUCCESS** (version 1.2.1).
  - `numpy`: **IMPORT SUCCESS** (version 2.5.4).
- **Handwriting Dataset Audit**:
  - Searched repository root for `mnist`, `emnist`, `kanjivg`, `etl`, `.npz`, `.h5`, `.pt`, `.onnx`, `.tflite`.
  - Result: Only Japanese Kana KanjiVG SVG source files exist in `backend/assets/kanjivg`. Zero offline ML handwriting datasets exist for Sanskrit, Tamil, or Chinese.
- **Feasibility Blockers**:
  1. *Package Policy & Application Control*: Strict mandate prohibiting new pip installs, downloads, or virtual environments.
  2. *Dataset Absence*: Total lack of labelled stroke/image training data for Sanskrit Devanagari, Tamil script, and Chinese Hanzi.
  3. *Inference & Resource Limits*: Offline CNN/RNN inference requires PyTorch/ONNX runtime; Whisper model weights (~150MB–1.5GB) cannot be bundled or downloaded.
  4. *Project Timeline*: Feature freeze at end of 18 November 2026.
- **Recommendation & Project Posture**:
  - Machine learning models (CNN classifier, OpenCV preprocessing, Whisper speech assessment) remain honestly documented as **future scope**.
  - The active geometric evaluator is accurately presented as an **algorithmic prototype** (start-to-end vector cosine similarity, dynamic aspect-ratio uniform scaling, and stroke order check), not trained AI.

### 3. Curriculum Seeding Execution (`backend/scripts/seed_featured_curriculum.py`)
- **Seeding Execution**:
  - Executable: `C:\Users\CHETAN\.vscode\StrokeSpeak\backend\.venv\Scripts\python.exe`.
  - Rows before: 338.
  - Rows newly inserted: 18.
    - Sanskrit Foundation (Unit 1): Lessons 339–343 (`अ, आ, इ, ई, उ`, matching character IDs 216–220).
    - Sanskrit Beginner (Unit 1): Lessons 344–347 (`Word: नमस्ते`, `Word: जलम्`, `Word: मित्रम्`, `Word: पुस्तकम्`).
    - Simplified Chinese Foundation Prototype (Unit 1): Lessons 348–352 (`一, 二, 三, 人, 大`, pinyin tone marks: `yī, èr, sān, rén, dà`). No Beginner unit.
    - Tamil Beginner (Unit 5): Lessons 353–356 (`Word: வணக்கம்`, `Word: நன்றி`, `Word: புத்தகம்`, `Word: தண்ணீர்`), complementing existing lesson 302 (`நான் தண்ணீர் குடிக்கிறேன்.`) without moving 302.
  - Rows after: 356.
  - Idempotency verified: Re-running the script reported 0 inserted, 18 skipped, total 356.
- **Snapshot Integrity Check**:
  - Script `verify_pre_seed_snapshot.py` checked all 338 pre-seed rows field-by-field against MySQL.
  - Result: 338 matching rows, 0 missing rows, 0 mismatches. All original rows remain 100% unmodified.

### 4. Frontend UI Implementation (`frontend/src/App.jsx` & `App.css`)
- **Backups**: `frontend/src/App.jsx.bak-2026-11-17-072430` and `frontend/src/App.css.bak-2026-11-17-072430`.
- **Featured Lesson Marking**:
  - Added `FEATURED_LESSON_IDS` set in `App.jsx` covering the 5 featured Foundation lessons per language and featured Beginner units.
  - Featured lessons render with `★ Featured` badge (`.featured-badge`) and accent styling (`.is-featured`).
  - All non-featured lessons remain fully visible in their natural database sequence.
- **Per-Language Unit Titles**:
  - Japanese unit titles kept strictly unchanged.
  - Added dedicated unit titles for Sanskrit (`Sanskrit vowels (Svara) · अ, आ, इ, ई, उ`, `Essential vocabulary (Śabda)`), Tamil (`Tamil vowels (Uyireḻuttu)`, `Sound contrasts`, `Tamil greeting`, `Phrase practice`, `Essential vocabulary & sentence practice`), and Chinese.
- **Stroke Animation Graceful Fallback**:
  - `StrokeOrderGuide` displays `"Stroke animation not available yet"` with informational note for characters without verified SVG stroke paths (Sanskrit, Tamil, Chinese).
- **Audio Voice Clarification**:
  - Sanskrit audio playback cards display: *"Reference voice: Hindi synthetic voice, approximate for Sanskrit"*.
- **Speaking Practice Integrity**:
  - Speaking practice UI clearly marked as local audio recording and reference playback only; no automated speech assessment claimed.
- **Chinese Prototype Labeling**:
  - Simplified Chinese displays `Limited Prototype` badge and warning banners indicating 5 foundation characters available with beginner units deferred.
- **Production Build**:
  - Executed `npm run build`: 17 modules transformed, built in 265ms with 0 errors.

### 5. Section 9 Master Verification Suite
- **1. Lesson Progress Persistence (Learner ID 1)**:
  - Saved progress for 3 new lessons with no prior progress rows:
    - Sanskrit Lesson 339: `status: 'completed'`, `score: 95.0`.
    - Chinese Lesson 348: `status: 'in_progress'`, `score: 85.0`.
    - Tamil Lesson 353: `status: 'completed'`, `score: 90.0`.
  - Read back via API `GET /api/v1/lesson-progress?user_id=1`: all 3 rows returned with correct status and score.
  - Read back via direct MySQL SELECT: Row IDs 22, 23, and 24 confirmed committed in `lesson_progress`.
- **2. Drawing Practice Attempts (Pending Scores Audit)**:
  - Sanskrit (Character ID 216 `अ`): `POST /api/v1/practice-attempts` returned HTTP 201 (Attempt ID 91). Scores returned `handwriting_score: None`, `stroke_order_score: None`, feedback: `"Drawing saved. No reference drawing exists for this character yet, so drawing scores are pending."`.
  - Tamil (Character ID 25 `அ`): `POST /api/v1/practice-attempts` returned HTTP 201 (Attempt ID 92). Scores returned `handwriting_score: None`, `stroke_order_score: None`, feedback: `"Drawing saved. No reference drawing exists for this character yet, so drawing scores are pending."`.
- **3. Audio Streaming Endpoint Verification**:
  - Japanese Lesson 61 (`あ`): HTTP 200, `Content-Type: audio/mpeg`, 4,224 bytes.
  - Sanskrit Lesson 339 (`अ`): HTTP 200, `Content-Type: audio/mpeg`, 4,992 bytes.
  - Tamil Lesson 223 (`அ`): HTTP 200, `Content-Type: audio/mpeg`, 5,760 bytes.
  - Chinese Lesson 348 (`一`): HTTP 200, `Content-Type: audio/mpeg`, 6,144 bytes.
  - Note: Reference audio generation uses gTTS and requires active internet access for dynamic synthesis.

### Files Modified & Backups
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-17-073700`)
- `frontend/src/App.jsx` (Backup: `frontend/src/App.jsx.bak-2026-11-17-072430`)
- `frontend/src/App.css` (Backup: `frontend/src/App.css.bak-2026-11-17-072430`)
- `backend/scripts/seed_featured_curriculum.py` (New file)
- `backend/db_backups/learning_lessons_all_before_multilingual_2026-11-17.json` (New snapshot)
- `backend/main.py`: Untouched in this task.

### Database Counts Before and After

| Table | Before Task | After Task | Change | Notes |
|---|---:|---:|---:|---|
| users | 2 | 2 | 0 | Preserved (User 1: Test Learner, User 2: Demo Learner) |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved |
| learning_lessons | 338 | 356 | +18 | 9 Sanskrit (5 Fdn, 4 Beg), 5 Chinese (Fdn), 4 Tamil (Beg) |
| lesson_progress | 9 | 12 | +3 | Added progress for User 1 on new lessons 339, 348, 353 |
| practice_attempts | 85 | 88 | +3 | Added attempts 90, 91 (Sanskrit), 92 (Tamil) |

### Exact next task
Conduct the final presenter rehearsal walkthrough with Learner 2 in browser emulation across 390px and 1280px viewports to verify all four language tabs and featured curriculum badges.


## 24. Final System Verification, Process Audit, and Full Database Export (2026-11-17)

### 1. New Lessons & Character Mapping Audit (IDs 339–356)
- Audited all 18 new lessons from MySQL:
  - Sanskrit Foundation (339–343): Confirmed linked to Character IDs 216–220 (`अ, आ, इ, ई, उ`), all belonging to Language ID 56.
  - Sanskrit Beginner (344–347): 4 vocabulary words (`Word: नमस्ते`, `Word: जलम्`, `Word: मित्रम्`, `Word: पुस्तकम्`).
  - Simplified Chinese Foundation (348–352): Confirmed linked to Character IDs 241–245 (`一, 二, 三, 人, 大`), all belonging to Language ID 58.
  - Tamil Beginner (353–356): 4 vocabulary words (`Word: வணக்கம்`, `Word: நன்றி`, `Word: புத்தகம்`, `Word: தண்ணீர்`) in Unit 5, sorted at lesson orders 1, 2, 3, 4 before existing sentence lesson 302 (`நான் தண்ணீர் குடிக்கிறேன்.`, order 302).
- `FEATURED_LESSON_IDS` in `frontend/src/App.jsx` verified per language and level.

### 2. Live API Audit & Legacy Language Filtering
- Public languages endpoint (`GET /api/v1/languages`) returns only the 4 supported public scripts (`ja-hiragana`, `sa-devanagari`, `zh-hans`, `ta`).
- Japanese Hiragana retains all 127 lessons in original sequence (ID 61 to 289).
- Queries for legacy languages (IDs 1, 6, 8, 9, 18, 20, 21) cleanly return empty arrays (`{"lessons": []}`).

### 3. Practice Attempts Audit (Attempt 90 & Missing 89)
- Attempt 90 confirmed in MySQL: User ID 1, Character ID 216 (`अ`), scores `None/None`, feedback noting pending drawing scores.
- Attempt 89 confirmed as an uncommitted InnoDB auto-increment gap from prior test schema validation; 0 rows were deleted.

### 4. Cross-Viewport Browser Audit (Headless Chrome CDP at 1280px & 390px)
- `scrollWidth <= innerWidth`: Returned `true` across all 4 languages on both Desktop (1280px) and Mobile (390px).
- Featured badges (`★ Featured`) visible and correctly count 5 per language level.
- Simplified Chinese displays `Limited Prototype` banners.
- Sanskrit displays synthetic Hindi voice disclaimer.
- Non-Kana characters display `"Stroke animation not available yet"`.
- Drawing canvas and audio recording controls functional on both viewports.
- Production build confirmed with `npm run build` (231ms).

### 5. Backend Health Check & Process Audit
- `GET /api/v1/health` returned HTTP 200: `{"status": "healthy", "service": "StrokeSpeak API", "database": "connected"}`.
- Interpreter: `C:\Users\CHETAN\.vscode\StrokeSpeak\backend\.venv\Scripts\python.exe`.
- Command: `uvicorn main:app --reload --port 8000`.
- `pyvenv.cfg` home path `C:\Users\CHETAN\AppData\Local\Programs\Python\Python312` confirmed existing on disk.
- Package imports verified: `fastapi` (0.143.2), `uvicorn` (0.54.0), `mysql.connector` (26.7.0).

### 6. Full Database Export
- Saved to `backend/db_backups/full_export_2026-11-17.json` (1.28 MB).
- Table counts exported:
  - `characters`: 250
  - `languages`: 12
  - `learning_lessons`: 356
  - `lesson_progress`: 12
  - `practice_attempts`: 88
  - `users`: 2
  - Total rows: 720

### Files Modified & Backups
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-17-150700`)
- `backend/REPORT_FOR_CLAUDE_REVIEW.txt` (New file)
- `backend/db_backups/full_export_2026-11-17.json` (New snapshot)
- `backend/main.py`: Untouched in this task.

### Exact next task
Perform the live user demonstration rehearsal for the four language tabs using Demo Learner 2 in the browser.


## 25. Comprehensive Documentation Suite Creation (2026-11-17)

### 1. New Documentation Assets Created in `docs/`
- `docs/DEMO_SCRIPT.md` (10-minute click-by-click live presentation script for Demo Learner 2, including fallback matrix for network, server, and canvas glitches).
- `docs/TEST_CHECKLIST.md` (Feature-by-feature tick checklist correlating every functional component to its verified section in `HANDOFF_REPORT.md`, with physical environment viva items marked `[UNVERIFIED]`).
- `docs/SCREENSHOT_CHECKLIST.md` (Numbered inventory of 13 screenshots required for the project report and slide deck with exact file names, viewports, setup steps, and academic captions).
- `docs/LIMITATIONS_AND_FUTURE_SCOPE.md` (Honest viva preparation guide documenting the geometric evaluator as an algorithmic prototype, explaining why CNN/Whisper/OpenCV were excluded, and detailing KanjiVG attribution and gTTS dependencies).
- `docs/PROJECT_REPORT_CONTENT.md` (Formal draft thesis chapters covering Introduction, Objectives, Architecture, Database Design, API Overview, Implementation, Testing Results, Limitations, and Conclusion).
- `docs/PPT_CONTENT.md` (14-slide presentation outline with 3–5 bullet points per slide and complete spoken speaker notes).
- `docs/RUN_INSTRUCTIONS.md` (Updated with Section 7: Cold-Start Procedure, marked `[UNTESTED]`).

### 2. Strict Constraints Maintained
- **Codebase Integrity**: Zero edits to `backend/main.py`, zero edits to `frontend/src/App.jsx` or CSS.
- **Database Freeze**: Zero database row updates, insertions, drops, or deletions. Database count remains exactly 720 rows.
- **Credentials & Environment**: Zero environment variables, passwords, or API keys printed or exposed.
- **Package Stability**: Zero pip, npm, or venv package installations or modifications.
- **Service Continuity**: Running FastAPI Uvicorn process (port 8000) and Vite frontend server (port 5173) remained active without restarts.
- **Learner Isolation**: Learner 2 remained completely untouched (0 attempts, 0 progress rows) to preserve its clean demonstration state.

### Files Modified & Backups
- `docs/RUN_INSTRUCTIONS.md` (Backup: `docs/RUN_INSTRUCTIONS.md.bak-2026-11-17-152100`)
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-17-152100`)
- `backend/REPORT_FOR_CLAUDE_REVIEW.txt` (Backup: `backend/REPORT_FOR_CLAUDE_REVIEW.txt.bak-2026-11-17-152100`)
- `docs/DEMO_SCRIPT.md` (New file)
- `docs/TEST_CHECKLIST.md` (New file)
- `docs/SCREENSHOT_CHECKLIST.md` (New file)
- `docs/LIMITATIONS_AND_FUTURE_SCOPE.md` (New file)
- `docs/PROJECT_REPORT_CONTENT.md` (New file)
- `docs/PPT_CONTENT.md` (New file)

### Exact next task
Capture the 13 required screenshots listed in `docs/SCREENSHOT_CHECKLIST.md` and rehearse the 10-minute presentation using `docs/DEMO_SCRIPT.md` with Demo Learner 2 (`?learner_id=2`).


## 26. Documentation Fact-Checking & Empirical Rigor Audit (Chunk 1 of 4) (2026-11-17)

### 1. Verification & Corrections Applied to `docs/`
- **Promised Scores Replaced with Empirical Ranges**: Removed all ungrounded score promises (such as "~90%+" or "< 40%"). Replaced with exact recorded test numbers from Sections 8, 9, 10:
  - Baseline reference trace: 100.0% shape, 100.0% order (Section 9).
  - Wobble perturbation (±0.015): 88.7% – 94.6% shape, 100.0% order (Section 9).
  - Translation & scale (15% shift, 60% scale): 87.2% – 95.8% shape, 100.0% order (Section 9).
  - Reverse direction on single-stroke character (`ノ`): 0.0% order score (Section 8 & 9).
  - Directional angle variation: 80° retains 88.4% order score; 100° drops to 0.0% (Section 10).
  - Multi-stroke reversed sequence: 66.7% order score due to positional pairing (Section 9).
- **Synthetic Trace Disclosure**: Added explicit disclosures across all documentation files that all automated tests to date used synthetic coordinate traces generated mathematically from reference vector paths. Freehand human drawings exhibit natural velocity variations, hook artifacts, and local tremors, and may score differently; human drawing tests remain marked `[UNVERIFIED]`.
- **Database Schema & Counts Corrected**:
  - `users` table schema in `PROJECT_REPORT_CONTENT.md` corrected from erroneous `username` to real column `name` (VARCHAR(100)), `email` (VARCHAR(255)), and `password_hash`.
  - Confirmed total row counts: exactly 720 rows across 6 tables (`users` 2, `languages` 12, `characters` 250, `learning_lessons` 356, `lesson_progress` 12, `practice_attempts` 88).
  - Confirmed curriculum counts: 356 total lessons (127 Japanese Hiragana, 1 Japanese Katakana, 9 Sanskrit, 23 Tamil, 5 Chinese).
- **Rehearsal & Profile Separation**:
  - Rehearsals restricted strictly to Learner 1.
  - Learner 2 strictly preserved in clean state (0 attempts, 0 progress) for the live demo.
  - "Spare Demo Learner" described as PLANNED (to be created in Chunk 2), not as already existing.
- **Privacy & Security Notes Added**:
  - Noted that `backend/db_backups/full_export_2026-11-17.json` contains placeholder password hashes and must not be published or shared publicly.
  - Noted that the application operates with placeholder accounts without user authentication/login.
- **Run Instructions & Command Audit**:
  - Confirmed interpreter path `C:\Users\CHETAN\.vscode\StrokeSpeak\backend\.venv\Scripts\python.exe` on disk.
  - Confirmed `python -m uvicorn main:app --reload --port 8000`.
  - Confirmed `frontend/package.json` scripts (`dev`, `build`, `lint`, `preview`); noted that `npm run test` is not defined.
  - Cold-start procedure kept marked `[UNTESTED]`.

### 2. Database Changes
- **NONE**: Zero database writes, zero insertions, zero updates, zero deletes. Table count remains 720 rows.

### Files Modified & Backups
- `docs/DEMO_SCRIPT.md` (Backup: `docs/DEMO_SCRIPT.md.bak-2026-11-17-154500`)
- `docs/TEST_CHECKLIST.md` (Backup: `docs/TEST_CHECKLIST.md.bak-2026-11-17-154500`)
- `docs/SCREENSHOT_CHECKLIST.md` (Backup: `docs/SCREENSHOT_CHECKLIST.md.bak-2026-11-17-154500`)
- `docs/LIMITATIONS_AND_FUTURE_SCOPE.md` (Backup: `docs/LIMITATIONS_AND_FUTURE_SCOPE.md.bak-2026-11-17-154500`)
- `docs/PROJECT_REPORT_CONTENT.md` (Backup: `docs/PROJECT_REPORT_CONTENT.md.bak-2026-11-17-154500`)
- `docs/PPT_CONTENT.md` (Backup: `docs/PPT_CONTENT.md.bak-2026-11-17-154500`)
- `docs/RUN_INSTRUCTIONS.md` (Backup: `docs/RUN_INSTRUCTIONS.md.bak-2026-11-17-154500`)
- `docs/API_OVERVIEW.md` (Backup: `docs/API_OVERVIEW.md.bak-2026-11-17-154500`)
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-17-154500`)
- `backend/REPORT_FOR_CLAUDE_REVIEW.txt` (Backup: `backend/REPORT_FOR_CLAUDE_REVIEW.txt.bak-2026-11-17-154500`)

### Exact next task
Proceed with Chunk 2: Insert the Spare Demo Learner row into MySQL, verify before/after counts, and confirm users 1 and 2 remain unchanged.


## 28. Spare Demo Learner Provisioning & Documentation Alignment (Chunk 2) (2026-11-17)

### 1. Database Schema & User Verification
- `users` table schema inspected:
  - `id`: INT, Primary Key, Auto-Increment
  - `name`: VARCHAR(100), Not Null
  - `email`: VARCHAR(255), Unique, Not Null
  - `password_hash`: VARCHAR(255), Not Null
  - `created_at`: TIMESTAMP, Default: CURRENT_TIMESTAMP
- Script executed: `backend/scripts/add_spare_learner.py` via `C:\Users\CHETAN\.vscode\StrokeSpeak\backend\.venv\Scripts\python.exe`.
- **First Run**:
  - Inserted exactly 1 row: `name = 'Spare Demo Learner'`, `email = 'spare@strokespeak.internal'`, mirroring the placeholder password hash.
  - Assigned ID: `3`.
  - Confirmed: `users 1 and 2 unchanged: true` (all columns compared silently in memory).
  - Users count increased from 2 to 3.
- **Second Run (Idempotency)**:
  - Detected existing user with email `spare@strokespeak.internal` (ID: 3).
  - 0 rows inserted; output: `IDEMPOTENCY_CHECK: User with email spare@strokespeak.internal already exists with ID: 3. No row inserted.`
  - Users count remained 3.
- **Practice & Progress Counts Confirmed**:
  - `practice_attempts` unchanged at 88 (User 3 has 0 attempts).
  - `lesson_progress` unchanged at 12 (User 3 has 0 progress rows).
  - Zero writes made for User 3.

### 2. Documentation Updates
- Updated `docs/DEMO_SCRIPT.md`, `docs/TEST_CHECKLIST.md`, and `docs/RUN_INSTRUCTIONS.md` reflecting that the Spare Demo Learner exists with User ID 3 and URL `http://localhost:5173/?learner_id=3`, reserved strictly for repeat demonstrations, never used for rehearsals or tests.

### 3. Database Counts Summary
| Table | Before Task | After Task | Change | Notes |
|---|---:|---:|---:|---|
| users | 2 | 3 | +1 | Inserted Spare Demo Learner (ID 3); Users 1 and 2 unchanged |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved |
| learning_lessons | 356 | 356 | 0 | Preserved |
| lesson_progress | 12 | 12 | 0 | Preserved (User 3 has 0 rows) |
| practice_attempts | 88 | 88 | 0 | Preserved (User 3 has 0 rows) |
| **Total Rows** | **720** | **721** | **+1** | Exactly one row added |

### Files Modified & Backups
- `backend/scripts/add_spare_learner.py` (New script)
- `backend/scripts/verify_spare_learner_counts.py` (New script)
- `docs/DEMO_SCRIPT.md` (Backup: `docs/DEMO_SCRIPT.md.bak-2026-11-17-160800`)
- `docs/TEST_CHECKLIST.md` (Backup: `docs/TEST_CHECKLIST.md.bak-2026-11-17-160800`)
- `docs/RUN_INSTRUCTIONS.md` (Backup: `docs/RUN_INSTRUCTIONS.md.bak-2026-11-17-160800`)
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-17-160800`)
- `backend/REPORT_FOR_CLAUDE_REVIEW.txt` (Backup: `backend/REPORT_FOR_CLAUDE_REVIEW.txt.bak-2026-11-17-160800`)

### Exact next task
Proceed with Chunk 3 of 4: Cold-start prep & read-only command verification, or Chunk 4: Rehearsal dry-run on Learner 1 and screenshot capture.



## 27. Documentation Number Correction & Post-Change Scoring Alignment (Chunk 1B) (2026-11-17)

### 1. Document Corrections Against Section 20 Table 3
- **Japanese Lesson Count Reconciliation**:
  - Confirmed Japanese curriculum has exactly 127 lessons (99 Foundation including Katakana lesson 315, 25 Beginner, 2 Elementary, 1 Advanced).
  - Removed all occurrences of double-counting (previously written as "127 + 1 = 128") across all documentation files.
- **Empirical Scoring Range Alignment (Post-Change Results Only)**:
  - Audited `HANDOFF_REPORT.md` Section 20 Table 3 (Attempt IDs 56 through 77) executed following the start-to-end vector cosine direction check implementation.
  - Replaced broad synthetic estimates with exact min/max observed post-change values across all 6 test Kana (`あ, い, ア, イ, ウ, ノ`):
    * **Wobble $\pm 0.015$**: Handwriting shape scores 96.35% – 97.12% (min 96.35% for `い` Attempt 60, max 97.12% for `ノ` Attempt 72); stroke order scores 88.90% – 96.45% (min 88.90% for `ノ` Attempt 72, max 96.45% for `い` Attempt 60). (Attempts 57, 60, 63, 66, 69, 72).
    * **Shifted 15% right & scaled to 60%**: Handwriting shape scores 78.66% – 89.00% (min 78.66% for `い` Attempt 61, max 89.00% for `イ` Attempt 67); stroke order scores 84.19% – 89.55% (min 84.19% for `い` Attempt 61, max 89.55% for `イ` Attempt 67). (Attempts 58, 61, 64, 67, 70, 73).
    * **Model Baseline Trace**: 100.0% shape and 100.0% order (Attempts 56, 59, 62, 65, 68, 71).
- **Reversed Order Audit & Unverified Marking**:
  - Reversed single stroke on `ノ` (Attempt 74) confirmed at 0.00 order score.
  - Reversed two-stroke characters on `い` (Attempt 76) and `ア` (Attempt 77) confirmed at 0.00 order score.
  - The score 66.64 for a 3-stroke character (`あ`) was measured in Section 16 *prior* to the direction check. Because no post-change test was recorded for a 3-stroke reversed character, all references to ~66.7% were removed and explicitly replaced with: *"not re-measured after the direction change (UNVERIFIED)"*.

### 2. Database Changes
- **NONE**: Zero database writes, zero insertions, zero updates, zero deletes. Table count remains strictly 720.

### Files Modified & Backups
- `docs/DEMO_SCRIPT.md` (Backup: `docs/DEMO_SCRIPT.md.bak-2026-11-17-160100`)
- `docs/TEST_CHECKLIST.md` (Backup: `docs/TEST_CHECKLIST.md.bak-2026-11-17-160100`)
- `docs/SCREENSHOT_CHECKLIST.md` (Backup: `docs/SCREENSHOT_CHECKLIST.md.bak-2026-11-17-160100`)
- `docs/LIMITATIONS_AND_FUTURE_SCOPE.md` (Backup: `docs/LIMITATIONS_AND_FUTURE_SCOPE.md.bak-2026-11-17-160100`)
- `docs/PROJECT_REPORT_CONTENT.md` (Backup: `docs/PROJECT_REPORT_CONTENT.md.bak-2026-11-17-160100`)
- `docs/PPT_CONTENT.md` (Backup: `docs/PPT_CONTENT.md.bak-2026-11-17-160100`)
- `docs/RUN_INSTRUCTIONS.md` (Backup: `docs/RUN_INSTRUCTIONS.md.bak-2026-11-17-160100`)
- `docs/API_OVERVIEW.md` (Backup: `docs/API_OVERVIEW.md.bak-2026-11-17-160100`)
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-17-160100`)
- `backend/REPORT_FOR_CLAUDE_REVIEW.txt` (Backup: `backend/REPORT_FOR_CLAUDE_REVIEW.txt.bak-2026-11-17-160100`)

### Exact next task
Proceed with Chunk 2: Insert the Spare Demo Learner row into MySQL, verify before/after counts, and confirm users 1 and 2 remain unchanged.


## 28. Spare Demo Learner Provisioning & Documentation Alignment (Chunk 2) (2026-11-17)

### 1. Database Schema & User Verification
- `users` table schema inspected:
  - `id`: INT, Primary Key, Auto-Increment
  - `name`: VARCHAR(100), Not Null
  - `email`: VARCHAR(255), Unique, Not Null
  - `password_hash`: VARCHAR(255), Not Null
  - `created_at`: TIMESTAMP, Default: CURRENT_TIMESTAMP
- Script executed: `backend/scripts/add_spare_learner.py` via `C:\Users\CHETAN\.vscode\StrokeSpeak\backend\.venv\Scripts\python.exe`.
- **First Run**:
  - Inserted exactly 1 row: `name = 'Spare Demo Learner'`, `email = 'spare@strokespeak.internal'`, mirroring the placeholder password hash.
  - Assigned ID: `3`.
  - Confirmed: `users 1 and 2 unchanged: true` (all columns compared silently in memory).
  - Users count increased from 2 to 3.
- **Second Run (Idempotency)**:
  - Detected existing user with email `spare@strokespeak.internal` (ID: 3).
  - 0 rows inserted; output: `IDEMPOTENCY_CHECK: User with email spare@strokespeak.internal already exists with ID: 3. No row inserted.`
  - Users count remained 3.
- **Practice & Progress Counts Confirmed**:
  - `practice_attempts` unchanged at 88 (User 3 has 0 attempts).
  - `lesson_progress` unchanged at 12 (User 3 has 0 progress rows).
  - Zero writes made for User 3.

### 2. Documentation Updates
- Updated `docs/DEMO_SCRIPT.md`, `docs/TEST_CHECKLIST.md`, and `docs/RUN_INSTRUCTIONS.md` reflecting that the Spare Demo Learner exists with User ID 3 and URL `http://localhost:5173/?learner_id=3`, reserved strictly for repeat demonstrations, never used for rehearsals or tests.

### 3. Database Counts Summary
| Table | Before Task | After Task | Change | Notes |
|---|---:|---:|---:|---|
| users | 2 | 3 | +1 | Inserted Spare Demo Learner (ID 3); Users 1 and 2 unchanged |
| languages | 12 | 12 | 0 | Preserved |
| characters | 250 | 250 | 0 | Preserved |
| learning_lessons | 356 | 356 | 0 | Preserved |
| lesson_progress | 12 | 12 | 0 | Preserved (User 3 has 0 rows) |
| practice_attempts | 88 | 88 | 0 | Preserved (User 3 has 0 rows) |
| **Total Rows** | **720** | **721** | **+1** | Exactly one row added |

### Files Modified & Backups
- `backend/scripts/add_spare_learner.py` (New script)
- `backend/scripts/verify_spare_learner_counts.py` (New script)
- `docs/DEMO_SCRIPT.md` (Backup: `docs/DEMO_SCRIPT.md.bak-2026-11-17-160800`)
- `docs/TEST_CHECKLIST.md` (Backup: `docs/TEST_CHECKLIST.md.bak-2026-11-17-160800`)
- `docs/RUN_INSTRUCTIONS.md` (Backup: `docs/RUN_INSTRUCTIONS.md.bak-2026-11-17-160800`)
- `backend/HANDOFF_REPORT.md` (Backup: `backend/HANDOFF_REPORT.md.bak-2026-11-17-160800`)
- `backend/REPORT_FOR_CLAUDE_REVIEW.txt` (Backup: `backend/REPORT_FOR_CLAUDE_REVIEW.txt.bak-2026-11-17-160800`)

### Exact next task
Proceed with Chunk 3 of 4: Cold-start prep & read-only command verification, or Chunk 4: Rehearsal dry-run on Learner 1 and screenshot capture.






---

## 29. Cold-Start Prep, Environment Audit & Launchers (Chunk 3 of 4) (2026-11-17)

### 1. Python Virtual Environment Audit [RAN AND VERIFIED]
- **Python Binary**: `C:\Users\CHETAN\.vscode\StrokeSpeak\backend\.venv\Scripts\python.exe`
- **Python Version**: CPython `3.12.2` (64-bit on Windows)
- **Configuration (`backend\.venv\pyvenv.cfg`)**:
  - `home = C:\Users\CHETAN\AppData\Local\Programs\Python\Python312`
  - `version = 3.12.2`
  - Home folder exists on disk: `True`
- **Core Library Imports & Versions**:
  - `fastapi`: `0.143.2` (verified import)
  - `uvicorn`: `0.54.0` (verified import)
  - `pydantic`: `2.14.1` (verified import)
  - `mysql.connector`: `26.7.0` (from `mysql-connector-python 26.7.0`, verified import)
- **CLI Check**: `python -m uvicorn --version` returned `Running uvicorn 0.54.0 with CPython 3.12.2 on Windows`.
- **Dependencies Audit (`pip list` vs `requirements.txt`)**:
  - `fastapi` (0.143.2): Satisfied
  - `uvicorn[standard]` (0.54.0): Satisfied
  - `mysql-connector-python` (26.7.0): Satisfied
  - `python-dotenv` (1.2.1): Satisfied
  - `gTTS` (2.5.4): Satisfied
  - Differences/Missing: None. All requirements installed and satisfied.

### 2. Active Processes and Ports Audit [RAN AND VERIFIED]
- **Port 8000 (Backend API)**:
  - Status: LISTENING
  - Process ID: `19676`
  - Command Line: `"C:\Users\CHETAN\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn main:app --reload`
- **Port 5173 (Frontend Dev Server)**:
  - Status: LISTENING
  - Process ID: `4036`
  - Command Line: `"node" "C:\Users\CHETAN\.vscode\StrokeSpeak\frontend\node_modules\.bin\\..\vite\bin\vite.js"`
- **Port 8001 (Secondary Backend Instance)**:
  - Status: LISTENING
  - Process ID: `22936`
  - Command Line: `"C:\Users\CHETAN\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn main:app --port 8001`

### 3. Frontend Architecture & CORS Findings [RAN AND VERIFIED]
- **`frontend\node_modules`**: Exists and verified.
- **Scripts in `frontend\package.json`**:
  - `"dev"`: `vite`
  - `"build"`: `vite build`
  - `"lint"`: `oxlint`
  - `"preview"`: `vite preview`
- **Dev Server Port**: 5173 (Vite default; proxy forwards `/api` calls).
- **Frontend API Base URL**:
  - Relative `/api/v1/...` calls in `frontend\src\App.jsx` (e.g. line 301 `/api/v1/languages`, line 351 `/api/v1/lessons`, line 378 `/api/v1/lessons/{id}`, line 586 `/api/v1/practice/submit`).
  - Proxied to `http://127.0.0.1:8000` via `frontend\vite.config.js` (lines 10–16: `server.proxy['/api'].target = 'http://127.0.0.1:8000'`).
- **Backend CORS Settings (`backend\main.py`)**:
  - `CORSMiddleware` is **NOT** configured in `backend\main.py`.
  - Allowed origins configured in FastAPI: None.
  - Browser same-origin requests are maintained via Vite's proxy (`localhost:5173` -> `127.0.0.1:8000`), which bypasses browser CORS restrictions. Direct cross-origin browser fetches would fail CORS preflight. Per strict instructions, read-only audit only; `main.py` was not edited.

### 4. Configuration Names and Database Connection Check [RAN AND VERIFIED]
- **Variable Names Defined in `backend\.env` (Values Redacted)**:
  - `DB_HOST`
  - `DB_PORT`
  - `DB_NAME`
  - `DB_USER`
  - `DB_PASSWORD`
  - `STROKESPEAK_TRANSCRIPTION_PROVIDER`
  - `OPENAI_API_KEY`
- **Variable Names Read by Backend Code**:
  - `DB_HOST`, `DB_NAME`, `DB_PASSWORD`, `DB_PORT`, `DB_USER`: All present in `.env`.
  - `OPENAI_API_KEY`, `STROKESPEAK_TRANSCRIPTION_PROVIDER`: Present in `.env`.
  - `STROKESPEAK_OPENAI_TRANSCRIPTION_MODEL`, `STROKESPEAK_WHISPER_MODEL`: Missing in `.env`, but have safe default constants in code.
- **MySQL Connection Test**:
  - Executed `SELECT 1;` using project's `app.db.database.get_db_connection()`.
  - Result: `(1,)` (Returned True, connection verified).

### 5. File System & Privacy Verification [RAN AND VERIFIED]
- **`backend\assets\kanjivg`**:
  - `ATTRIBUTION.md` (1,523 bytes), `COPYING` (20,595 bytes), attribution backups.
  - Subdirectory `backend\assets\kanjivg\kanji`: Exactly 92 SVG files for Japanese Kana (total size: 195,862 bytes / 191.27 KB).
- **`backend\db_backups`**:
  - `full_export_2026-11-17.json`: Verified present (1,280,168 bytes / 1.22 MB).
  - 12 other historical table snapshots verified.
- **`docs\`**:
  - 8 core documents plus timestamped backups verified.
- **Privacy & Security Warnings**:
  - `backend\.env`: Contains plain-text database credentials and API key. Must NOT be committed to public VCS or shared.
  - `backend\db_backups\full_export_2026-11-17.json`: Contains full `users` table export with placeholder `password_hash` strings. Must NOT be publicly shared.
  - `backend-dev.*.log` and `frontend-dev.*.log`: Audited; zero plain-text passwords or keys found.
  - `docs/PROJECT_REPORT_CONTENT.md`: Discusses schema column name `password_hash` as documentation; no live passwords/secrets exposed.

### 6. New Files Created (Cold-Start Suite) [RAN AND VERIFIED]
- **`docs\COLD_START_CHECKLIST.md`**: Numbered 8-step cold-start runbook with exact commands, expected results, and troubleshooting lines for ports, Application Control policy blocks, MySQL services, and learner IDs. Explicitly marked `UNTESTED until run by hand`.
- **`start_backend.bat`**: Root launcher running `cd backend` and `.\.venv\Scripts\python.exe -m uvicorn main:app --port 8000`. (Created, NOT executed).
- **`start_frontend.bat`**: Root launcher running `cd frontend` and `npm run dev`. (Created, NOT executed).

### 7. Scripts Backed Up
- `backend/scripts/inspect_users.py`: Backed up to `backend/scripts/inspect_users.py.bak-2026-11-17-161400`.
  - Changes made: Added `DESCRIBE users`, `SHOW INDEX FROM users`, and queried `id, name, email, created_at` without outputting the `password_hash` value.

### Exact Next Task
Proceed with Chunk 4: Rehearsal dry-run on Learner 1 (and/or manual cold-start execution) and final screenshot capture.


---

## 30. Read-Only Verification of Transcription, Audio Paths & Configuration (Chunk 3B) (2026-11-17)

### 1. STROKESPEAK_TRANSCRIPTION_PROVIDER [RAN AND VERIFIED]
- **Configured Value**: `openai` (from `backend\.env`).

### 2. Audio and Transcription Paths Audit [RAN AND VERIFIED]
- **Frontend (`frontend\src\App.jsx`)**:
  - `startRecording()` (L657) / `stopRecording()` (L699): Uses `navigator.mediaDevices.getUserMedia` and `MediaRecorder` on user click (`onClick` at L1293).
  - Recorded audio stays local: Converts chunks to a `Blob` and sets a local Object URL (`URL.createObjectURL(audioBlob)`) for `<audio controls src={audioUrl} />` (L1305).
  - Caption at L1306 confirms: *"Your recording stays locally in this browser for playback. Speech assessment is not active; compare your pronunciation directly with the reference audio."*
  - Functions `savePronunciationAudio()` (L606) and `transcribePronunciation()` (L642) are defined but completely unwired in the UI (0 call sites in `App.jsx`).
  - `FormData` is NOT used anywhere in `App.jsx`.
  - Reference audio elements (`/api/v1/lessons/{id}/reference-audio` at L935, L1051, L1341) download synthesized speech via gTTS and never upload audio.
  - **Conclusion**: Recorded audio is NEVER uploaded to the backend or any external service from the frontend UI.
- **Backend (`backend\main.py`)**:
  - Routes:
    - `GET /api/v1/lessons/{lesson_id}/reference-audio` (L1009): Synthesizes audio using gTTS and returns MP3.
    - `PUT /api/v1/practice-attempts/{attempt_id}/pronunciation-audio` (L821): Saves base64 audio to DB `practice_attempts.audio_data`.
    - `POST /api/v1/practice-attempts/{attempt_id}/pronunciation-assessment` (L588): Text comparison only.
    - `POST /api/v1/practice-attempts/{attempt_id}/transcribe` (L653): If `STROKESPEAK_TRANSCRIPTION_PROVIDER="openai"`, sends temporary audio file to `https://api.openai.com/v1/audio/transcriptions`.
  - **Conclusion**: No audio can leave the machine without an explicit programmatic HTTP POST to the transcribe endpoint; zero audio leaves automatically or from the web UI.

### 3. Launcher Files Audit [RAN AND VERIFIED]
- `start_backend.bat`:
  - Command: `.\.venv\Scripts\python.exe -m uvicorn main:app --port 8000`
  - `--reload` is correctly omitted.
  - Paths are correct; zero secrets inside.
- `start_frontend.bat`:
  - Command: `npm run dev`
  - Paths are correct; zero secrets inside.

### 4. Vite Configuration & Preview Audit [RAN AND VERIFIED]
- `frontend\vite.config.js`:
  - Proxy target: `http://127.0.0.1:8000` via `server.proxy['/api']`.
  - Preview proxy: None configured (`preview` block is omitted).
  - Direct opening of `frontend\dist\index.html`: Will NOT reach API (fails same-origin relative `/api` paths and backend lacks CORS headers).

### 5. Cold-Start Checklist Verification [RAN AND VERIFIED]
- `docs\COLD_START_CHECKLIST.md` verified:
  - Step 1 explicitly commands checking and stopping ports 8000, 5173, and 8001.
  - Step 4 explicitly commands running `npm run dev`.

### 6. Database Changes
- **NONE** (Zero database writes; all tables preserved).


---

## 31. Documentation Corrections, Empirical Rigor Alignment & Safety Disclosures (Chunk 4A) (2026-11-17)

### 1. Curriculum Lesson Counts Reconciled [RAN AND VERIFIED]
- **Japanese Total**: Exactly 127 lessons (99 Foundation, 25 Beginner, 2 Elementary, 1 Advanced). Katakana lessons are already included inside these 127 lessons and are not counted twice. Removed every occurrence of "127 + 1 = 128" or "128" lessons.
- **Sanskrit**: Exactly 9 lessons (5 Foundation, 4 Beginner).
- **Tamil**: Exactly 23 lessons (18 Foundation, 5 Beginner).
- **Simplified Chinese**: Exactly 5 foundation prototype lessons (`一, 二, 三, 人, 大`).
- **Database Total**: Exactly 356 rows in `learning_lessons` across all languages.
- Corrected in `docs/COLD_START_CHECKLIST.md`, `docs/PROJECT_REPORT_CONTENT.md`, `docs/PPT_CONTENT.md`, `docs/LIMITATIONS_AND_FUTURE_SCOPE.md`, and `docs/TEST_CHECKLIST.md`.

### 2. Score Ranges Aligned to Post-Change Empirical Results [RAN AND VERIFIED]
- Audited `HANDOFF_REPORT.md` Section 20 Table 3 (post-direction check):
  - **Baseline Model Trace**: 100.0% shape, 100.0% order (Attempts 56, 59, 62, 65, 68, 71).
  - **Wobble $\pm 0.015$ (Post-Change)**:
    - Handwriting shape: min 96.35% (`い`, Attempt 60) to max 97.12% (`ノ`, Attempt 72).
    - Stroke order: min 88.90% (`ノ`, Attempt 72) to max 96.45% (`い`, Attempt 60).
    - Tested on all 6 Kana: `あ` (57), `い` (60), `ア` (63), `イ` (66), `ウ` (69), `ノ` (72).
  - **Shifted 15% right & scaled to 60% (Post-Change)**:
    - Handwriting shape: min 78.66% (`い`, Attempt 61) to max 89.00% (`イ`, Attempt 67).
    - Stroke order: min 84.19% (`い`, Attempt 61) to max 89.55% (`イ`, Attempt 67).
    - Tested on all 6 Kana: `あ` (58), `い` (61), `ア` (64), `イ` (67), `ウ` (70), `ノ` (73).
  - All automated benchmarks disclosed as using synthetic coordinate traces; human handwriting tests marked `[UNVERIFIED]`.

### 3. Reversed Order Status and Unverified Marking [RAN AND VERIFIED]
- **3-Stroke Reversed Order**: Stated explicitly as *"not re-measured after the direction change (UNVERIFIED)"*. The earlier 66.64 figure was measured before the direction check in Section 16 (Attempt 41).
- **Post-Change Reversed Results Cited**:
  - Single-stroke `ノ` (Attempt 74): 100.00 shape / 0.00 stroke order.
  - Two-stroke `い` (Attempt 76): 100.00 shape / 0.00 stroke order.
  - Two-stroke `ア` (Attempt 77): 100.00 shape / 0.00 stroke order.

### 4. Audio and Pronunciation Honesty Disclosures [RAN AND VERIFIED]
- Incorporated in `docs/LIMITATIONS_AND_FUTURE_SCOPE.md`, `docs/PROJECT_REPORT_CONTENT.md`, `docs/PPT_CONTENT.md`, and `docs/API_OVERVIEW.md`:
  (a) The app records speech locally in the browser and plays it back; it does not upload, save or score it.
  (b) The backend contains routes for saving audio (`PUT /api/v1/practice-attempts/{attempt_id}/pronunciation-audio`), for transcription through a configured provider (`POST /api/v1/practice-attempts/{attempt_id}/transcribe`), and for comparing recognized text with the expected text (`POST /api/v1/practice-attempts/{attempt_id}/pronunciation-assessment`). These routes are **not used by the app**, were **never called with real audio** in this project, and the transcription route would send audio to an external service (such as OpenAI) if someone called it (all untested behaviors of those routes are marked `[UNVERIFIED]`).
  (c) Text comparison is not phonetic accuracy or accent evaluation.
  (d) Whisper, OpenCV and CNN are not implemented.

### 5. Run Notes and Architecture Updates [RAN AND VERIFIED]
- In `docs/RUN_INSTRUCTIONS.md` and `docs/COLD_START_CHECKLIST.md`:
  - Run frontend with `npm run dev` (proxies `/api` to `127.0.0.1:8000`).
  - Built `dist` folder does not work without a reverse proxy.
  - Backend has no CORS middleware by design in this version.
  - Stop the port 8001 test server if it is running.

### 6. Swagger Demo Safety Rule [RAN AND VERIFIED]
- Added warning box in `docs/DEMO_SCRIPT.md` and `docs/SCREENSHOT_CHECKLIST.md`:
  - When using Swagger `/docs`, only press Execute on `GET` requests (`/health`, `/languages`, `/lessons`).
  - Never press Execute on the `transcribe` or `pronunciation-audio` routes during presentations.

### 7. Database Integrity & Row Count Preservation
- **Database writes in Chunk 4A**: **NONE**.
- Confirmed MySQL row count remains exactly **721 rows** (`users`: 3, `languages`: 12, `characters`: 250, `learning_lessons`: 356, `lesson_progress`: 12, `practice_attempts`: 92; User 2 and User 3 remain at 0 attempts and 0 progress rows).


---

## 32. Submission Packaging, Database Setup Runbook & Clean Artifacts (Chunk 4B) (2026-11-17)

### 1. Database Setup Runbook Creation (`docs/DATABASE_SETUP.md`) [RAN AND VERIFIED]
- Created `docs/DATABASE_SETUP.md` providing step-by-step instructions for initializing the StrokeSpeak platform on a clean machine:
  1. MySQL 8.0 installation and database creation (`strokespeak`, `utf8mb4`).
  2. MySQL user creation (`strokespeak_user`) with placeholder credentials.
  3. Environment file setup (`backend/.env.example` -> `backend/.env`).
  4. Relational schema generation via `backend/create_tables.py`.
  5. Chronological seed script execution order matching the actual development sequence from `HANDOFF_REPORT.md`:
     `seed_data.py` -> `scripts/fix_japanese_labels.py` -> `scripts/seed_katakana.py` -> `scripts/seed_sanskrit.py` -> `scripts/seed_tamil_extra.py` -> `scripts/seed_chinese.py` -> `scripts/seed_katakana_lesson.py` -> `scripts/seed_reference_strokes.py` -> `scripts/seed_japanese_beginner.py` -> `scripts/seed_featured_curriculum.py` -> `scripts/add_spare_learner.py`.
  6. Verification of final counts via `scripts/show_table_counts.py`.
  7. Alternative fast restore using `backend/db_backups/full_export_2026-11-17.json`.
- Explicitly marked: `UNTESTED on a fresh machine`. None of the seed scripts were executed during this documentation task.

### 2. Environment Configuration Template (`backend/.env.example`) [RAN AND VERIFIED]
- Created `backend/.env.example` containing exact variable names matching `backend/.env` with safe placeholder values:
  `DB_HOST=localhost`, `DB_PORT=3306`, `DB_NAME=strokespeak`, `DB_USER=root`, `DB_PASSWORD=YOUR_PASSWORD_HERE`, `STROKESPEAK_TRANSCRIPTION_PROVIDER=openai`, `OPENAI_API_KEY=leave-empty`.
- Zero real credentials, passwords, or API keys copied.

### 3. Read-Only Table Counts Script (`backend/scripts/show_table_counts.py`) [RAN AND VERIFIED]
- Script created in `backend/scripts/show_table_counts.py` using `app.db.database.get_db_connection()`.
- Executed once via `C:\Users\CHETAN\.vscode\StrokeSpeak\backend\.venv\Scripts\python.exe`:
  - `users`: 3 rows (Test Learner ID 1, Demo Learner ID 2, Spare Demo Learner ID 3)
  - `languages`: 12 rows
  - `characters`: 250 rows
  - `learning_lessons`: 356 rows
  - `lesson_progress`: 12 rows
  - `practice_attempts`: 99 rows (increased from baseline 88 due to active user drawings on Learner 1)
  - Total rows: 732 rows across all 6 tables.
  - Public lessons: Japanese 127, Tamil 23, Sanskrit 9, Katakana 1, Chinese 5 (165 public lessons total; 191 legacy internal lessons).

### 4. Submission Staging Folder (`C:\Users\CHETAN\StrokeSpeak-submission-staging`) [RAN AND VERIFIED]
- Created via robocopy with strict exclusion filters:
  `/XD .venv .venv* node_modules __pycache__ dist /XF .env *.bak-* full_export_*.json *.log`.
- Verified exclusions:
  - `.env` files: 0 found (Confirmed absent).
  - `full_export_*.json`: 0 found (Confirmed absent).
  - `.bak` files: 0 found (Confirmed absent).
  - `.log` files: 0 found (Confirmed absent).
- Sensitive text scan: Exactly 9 files contain `password_hash` or `sk-`:
  - All occurrences verified as SQL schema DDL (`create_tables.py`), query columns (`main.py`), demo placeholder assignments (`add_spare_learner.py`), report documentation (`HANDOFF_REPORT.md`, `PROJECT_REPORT_CONTENT.md`, `DATABASE_SETUP.md`), or SVG CSS `mask-type:alpha` attributes (`favicon.svg`, `vite.svg`). Zero live passwords or secret keys exist in the staging directory.
- Staging contents: `backend/` (138 files, 888 KB), `docs/` (10 files, 112 KB), `frontend/` (16 files, 193 KB), `start_backend.bat` (80 B), `start_frontend.bat` (34 B). Total: 166 files (~1.19 MB).

### 5. Submission ZIP Archive (`C:\Users\CHETAN\StrokeSpeak-submission-2026-11-17.zip`) [RAN AND VERIFIED]
- Generated from staging folder using PowerShell `Compress-Archive`.
- File size: 350,467 bytes (342.25 KB / 0.33 MB).
- Total archive entries: 173 (166 files).
- Exclusions confirmed inside ZIP: 0 `.env`, 0 `full_export`, 0 `.bak`, 0 `.log`.
- Staging directory left intact at `C:\Users\CHETAN\StrokeSpeak-submission-staging`.

### 6. Database Changes
- **NONE** (Zero database writes performed by agent in Chunk 4B; all tables preserved).


---

## 33. Read-Only Provenance Audit, Audio Assessment Reconciliation & Documentation Alignment (Chunk 4D) (2026-11-17)

### 1. Provenance Audit of Practice Attempts Above ID 88 [RAN AND VERIFIED]
- **Baseline Attempts Accounting**:
  - Baseline practice attempts count recorded at the end of Section 23/24 was **88 rows** (inclusive of test rows 90, 91 for Sanskrit and 92 for Tamil, with auto-increment gap at 89).
- **Audit of Subsequent Practice Attempts (IDs 93–103, Reaching 99 Rows)**:
  - `id 93`: User 1, Char 2 (`あ`), 4 strokes, HW 64.50, Ord 37.16, pron 'not_submitted', 2026-11-17 16:23:11
  - `id 94`: User 1, Char 2 (`あ`), 3 strokes, HW 87.72, Ord 16.60, pron 'not_submitted', 2026-11-17 16:23:36
  - `id 95`: User 1, Char 2 (`あ`), 2 strokes, HW 51.04, Ord 16.39, pron 'not_submitted', 2026-11-17 16:24:01
  - `id 96`: User 1, Char 2 (`あ`), 3 strokes, HW 79.97, Ord 41.01, pron 'not_submitted', 2026-11-17 16:24:24
  - `id 97`: User 1, Char 2 (`あ`), 4 strokes, HW 51.15, Ord 16.44, pron 'not_submitted', 2026-11-17 16:24:48
  - `id 98`: User 1, Char 2 (`あ`), 5 strokes, HW 53.04, Ord 52.97, pron 'not_submitted', 2026-11-17 16:35:31
  - `id 99`: User 1, Char 28 (`い`), 2 strokes, HW 71.52, Ord 77.14, pron 'not_submitted', 2026-11-17 16:37:27
  - `id 100`: User 1, Char 29 (`う`), 2 strokes, HW 80.11, Ord 79.71, pron 'not_submitted', 2026-11-17 16:38:25
  - `id 101`: User 1, Char 29 (`う`), 2 strokes, HW 80.11, Ord 79.71, pron 'not_submitted', 2026-11-17 16:39:00
  - `id 102`: User 1, Char 30 (`え`), 4 strokes, HW 41.14, Ord 31.78, pron 'not_submitted', 2026-11-17 16:39:49
  - `id 103`: User 1, Char 30 (`え`), 4 strokes, HW 41.14, Ord 31.78, pron 'not_submitted', 2026-11-17 16:40:01
- **Provenance Determination**:
  - Audit of tool execution transcripts confirms that zero agent scripts submitted any practice attempts during this session.
  - The timestamps spaced 12 seconds to 11 minutes apart, varying stroke counts (2 to 5 strokes), and logical progression through sequential Hiragana vowel lessons (`あ` -> `い` -> `う` -> `え`) provide direct evidence of interactive canvas drawings submitted via the browser UI (`http://localhost:5173/?learner_id=1`).

### 2. Attempt 11 Provenance & Audio Audit [RAN AND VERIFIED]
- **MySQL Record Facts**:
  - `id`: 11, `user_id`: 1, `character_id`: 2 (`あ`), `created_at`: `2026-11-16 07:23:36`.
  - `audio_data IS NOT NULL`: **False** (`audio_data`: NULL, 0 bytes stored). `audio_mime_type`: NULL.
  - Pronunciation columns: `pronunciation_status`: 'completed', `pronunciation_score`: 100.00, `transcribed_text`: 'a', `pronunciation_feedback`: 'Excellent match. The spoken sounds closely match the reference pronunciation.'.
- **HANDOFF_REPORT.md Evidence (Section 1, Lines 159–161, 191)**:
  - Quotation (Line 160): *"Typed pronunciation assessment on attempt 11 returned expected `a`, submitted `a`, score 100.0 and text-comparison feedback. This is transcript-text scoring, not microphone-based scoring."*
  - Quotation (Line 161): *"Audio upload, hosted/local transcription, reference audio, and tutorial-video update routes were not called. They remain unverified in this work."*
  - Quotation (Line 191): *"POST `/api/v1/practice-attempts/{attempt_id}/pronunciation-assessment` — typed-text example only; updates the selected attempt and is not audio transcription: `{"transcribed_text":"a"}`"*
- **Conclusions**:
  - Real recorded audio was **NOT involved** (0 bytes stored).
  - Provider used was **typed text string comparison** via `POST /api/v1/practice-attempts/11/pronunciation-assessment` (`{"transcribed_text": "a"}`). Neither local Whisper nor OpenAI was used.
  - Hosted request to OpenAI: **No evidence found.** The transcribe route was never called.

### 3. Attempts 14, 15, 16 Provenance & Scorer Version [RAN AND VERIFIED]
- **Character**: 28 (`い`). Created on `2026-11-16` at `21:36:35`, `21:36:53`, `21:37:10`.
- **HANDOFF_REPORT.md Quotation (Section 17, Line 593)**:
  *"**+3 rows (IDs 14, 15, 16)** were inserted on 2026-11-16 between 21:36:35 and 21:37:10 during earlier interactive canvas testing for character 28 (`い`). These account for the 3 unexpected rows."*
- **Scorer Version**: Produced **BEFORE** the stroke-count penalty and uniform aspect-ratio scaling changes (which were implemented later that night at 22:41 in Section 17, backed up in `backend/main.py.bak-2026-11-16-224129`).

### 4. Submission Staging Folder Read-Only Audit (`C:\Users\CHETAN\StrokeSpeak-submission-staging`) [RAN AND VERIFIED]
- (a) **KanjiVG SVGs**: Exactly 92 SVG files present in `backend/assets/kanjivg/kanji`. `ATTRIBUTION.md` (True), `COPYING` (True).
- (b) **Files named `.env*`**: Exactly 1 file: `backend/.env.example`.
- (c) **Frontend files**: `package.json`, `vite.config.js`, `src/`, `public/`, `package-lock.json`, `index.html` confirmed present.
- (d) **Dependencies**: `backend/requirements.txt` (True), `frontend/package-lock.json` (True).
- (e) **Top-level README in staging**: **False** (No top-level `README.md` exists at staging root; staging folder was left unmodified).

### 5. Documentation Alignment & Precision [RAN AND VERIFIED]
- Updated `LIMITATIONS_AND_FUTURE_SCOPE.md`, `PROJECT_REPORT_CONTENT.md`, `PPT_CONTENT.md`, `API_OVERVIEW.md`, and `TEST_CHECKLIST.md`:
  - Accurately documented that Attempt 11 tested text-based pronunciation assessment via typed text string comparison, while real audio was never uploaded, stored, or transcribed.
  - Reconciled database totals: 732 rows across all 6 tables, including 99 practice attempts on Learner 1.
  - Clarified Japanese lesson counts: MySQL database contains 127 lessons under `ja-hiragana` (Language ID 5) plus 1 lesson under `ja-katakana` (Language ID 57; Lesson 315), presented as 127 lessons in the unified student tutor interface.

### 6. Database Changes
- **NONE** (Zero database writes performed by agent in Chunk 4D; all tables preserved).

---

## 34. Real Human-Drawing Results Audit & Live Table Row Counts (Chunk 4E Revised) (2026-11-17)

### 1. Audit of Real Human-Drawing Practice Attempts (IDs 93–109) [RAN AND VERIFIED]
- **Read-Only Database Query**:
  Executed query with NO upper limit:
  `SELECT id, character_id, JSON_LENGTH(stroke_data) AS stroke_count, handwriting_score, stroke_order_score, created_at FROM practice_attempts WHERE id > 92 AND user_id = 1 ORDER BY id ASC`.
- **Practice Attempts Metadata**:
  - `total_count`: 105
  - `MAX(id)`: 109
- **Why Chunk 4D Query Stopped at ID 103 (Code & Timestamp Evidence)**:
  - Inspection of `scratch\query_attempts_above_88.py` confirms that the SQL query had **NO hardcoded upper limit**: `SELECT ... FROM practice_attempts WHERE id > 88 ORDER BY id ASC`.
  - Chunk 4D executed that query at `2026-11-17 16:53:20`. At that exact timestamp, row ID 103 (created at `16:40:01`) was the latest row in the MySQL table.
  - Rows 104 through 109 were submitted between `16:54:24` and `16:57:11` during an active browser session while Chunk 4D was executing.
- **Character Reference Stroke Verification**:
  - `あ` (ID: 2): 3 reference strokes
  - `い` (ID: 28): 2 reference strokes
  - `う` (ID: 29): 2 reference strokes
  - `え` (ID: 30): 2 reference strokes
  - `か` (ID: 31): 3 reference strokes

### 2. Complete Empirical Table of Human Mouse Drawing Attempts (Learner 1) [RAN AND VERIFIED]

| Attempt ID | Character (Glyph / ID) | Strokes Drawn | Ref Strokes | Handwriting Score | Stroke Order Score | Created At | Pattern / Evaluator Observation |
|---:|:---:|:---:|:---:|:---:|:---:|:---|:---|
| 93 | あ (ID 2) | 4 | 3 | 64.50 | 37.16 | 2026-11-17 16:23:11 | Extra stroke drawn (4 vs 3 ref strokes) |
| 94 | あ (ID 2) | 3 | 3 | 87.72 | 16.60 | 2026-11-17 16:23:36 | Right stroke count; high shape, strict order drop |
| 95 | あ (ID 2) | 2 | 3 | 51.04 | 16.39 | 2026-11-17 16:24:01 | Missing stroke drawn (2 vs 3 ref strokes) |
| 96 | あ (ID 2) | 3 | 3 | 79.97 | 41.01 | 2026-11-17 16:24:24 | Right stroke count; moderate order match |
| 97 | あ (ID 2) | 4 | 3 | 51.15 | 16.44 | 2026-11-17 16:24:48 | Extra stroke drawn (4 vs 3 ref strokes) |
| 98 | あ (ID 2) | 5 | 3 | 53.04 | 52.97 | 2026-11-17 16:35:31 | Multiple extra strokes (5 vs 3 ref strokes) |
| 99 | い (ID 28) | 2 | 2 | 71.52 | 77.14 | 2026-11-17 16:37:27 | Right stroke count; balanced shape and stroke order |
| 100 | う (ID 29) | 2 | 2 | 80.11 | 79.71 | 2026-11-17 16:38:25 | Right stroke count; strong shape and stroke order match |
| 101 | う (ID 29) | 2 | 2 | 80.11 | 79.71 | 2026-11-17 16:39:00 | Identical score to 100 (probably same drawing submitted twice) |
| 102 | え (ID 30) | 4 | 2 | 41.14 | 31.78 | 2026-11-17 16:39:49 | Fragmented stroke sequence (4 vs 2 ref strokes) |
| 103 | え (ID 30) | 4 | 2 | 41.14 | 31.78 | 2026-11-17 16:40:01 | Identical score to 102 (probably same drawing submitted twice) |
| 104 | か (ID 31) | 9 | 3 | 26.69 | 16.44 | 2026-11-17 16:54:24 | Multi-stroke scribble test (9 vs 3 ref strokes) |
| 105 | か (ID 31) | 3 | 3 | 87.14 | 71.45 | 2026-11-17 16:55:07 | Right stroke count; high shape match and solid stroke order |
| 106 | か (ID 31) | 3 | 3 | 86.80 | 71.23 | 2026-11-17 16:55:32 | Right stroke count; consistent high shape and stroke order |
| 107 | か (ID 31) | 3 | 3 | 87.13 | 55.94 | 2026-11-17 16:56:15 | Right stroke count; good shape, order partly matched |
| 108 | か (ID 31) | 3 | 3 | 79.41 | 63.90 | 2026-11-17 16:56:55 | Right stroke count; consistent shape match |
| 109 | か (ID 31) | 2 | 3 | 41.89 | 26.15 | 2026-11-17 16:57:11 | Incomplete drawing (2 of 3 reference strokes) |

### 3. Key Empirical & Pedagogical Conclusions [RAN AND VERIFIED]
- **Synthetic vs Human Disclosure**: Earlier tests in this project used synthetic traces generated from the reference strokes; one person then drew these attempts with a mouse.
- **Exploratory Sample (Not Accuracy)**: Results are a small exploratory sample from one person on 5 characters and are not an accuracy measure. Do not call any of this "accuracy".
- **Handwriting Shape Score Correlation**: Drawings that matched the reference stroke count scored significantly higher on handwriting shape (71.52% to 87.72%). Incomplete or extra-stroke drawings were penalized heavily.
- **Stroke Order Score Variance**: Stroke-order scores for human drawings were often lower than shape scores and varied widely (for example, `あ` with 3 strokes scored 16.60 in attempt 94 and 41.01 in attempt 96), which is expected because stroke order is compared strictly position by position, and may also reflect the drawer's own stroke order or direction (UNVERIFIED which).
- **Duplicate Submissions Without Clearing Canvas**: Pairs of attempts with identical scores (such as 100/101 and 102/103) were the same drawing submitted twice without clearing the canvas.
- **Demo Rehearsal Guidelines Added to DEMO_SCRIPT.md**:
  - Press Submit once, then press Clear or Reset before next drawing.
  - Human drawings score lower than synthetic ones, especially on stroke order; do not promise high scores aloud.
  - For "correct drawing" step, use a character that has scored well (`い` or `う`, from the table); use `あ` for stroke replay.
  - Mention stroke-order scoring is strict and can show "partly matched" even when the shape looks right.

### 4. Database Table Row Counts (`backend/scripts/show_table_counts.py`) [RAN AND VERIFIED]
- Executed on `2026-11-17 17:47`:
  - `users`: 3 rows (Test Learner ID 1, Demo Learner ID 2, Spare Demo Learner ID 3)
  - `languages`: 12 rows
  - `characters`: 250 rows
  - `learning_lessons`: 356 rows (Japanese `ja-hiragana` 127, Tamil `ta` 23, Sanskrit `sa-devanagari` 9, Katakana `ja-katakana` 1, Chinese `zh-hans` 5; 165 public, 191 legacy)
  - `lesson_progress`: 13 rows (incremented from 12 upon completion of lesson 64 for Learner 1)
  - `practice_attempts`: 105 rows (MAX(id): 109)
  - **Total rows across all 6 tables**: **739 rows**.
- Replaced all hard-coded attempt and total row counts across documentation with:
  `as of 2026-11-17 17:47: 105 practice attempts, 739 total rows (regenerate with backend\scripts\show_table_counts.py)`.
- **Pre-Presentation Check Reminder**: Always execute `backend\scripts\show_table_counts.py` before any presentation to check and verify the latest live row counts.

### 5. Database Changes
- **NONE** (Zero database writes performed by agent in Chunk 4E; all tables strictly preserved).


---

## 35. Read-Only Verification, Diagnosis Synthesis & Extended Human Drawing Test (Chunks 4E-CHECK, 4F, 4E-ADD) (2026-11-17)

### 1. Chunk 4E-CHECK Read-Only Verification [RAN AND VERIFIED]
- **Character Metadata Column Audit**:
  Verified via read-only SELECT query on `characters` table for IDs 2, 28, 29, 30, 31, 32:
  - ID 2: `あ` (Hiragana a, 3 strokes)
  - ID 28: `い` (Hiragana i, 2 strokes)
  - ID 29: `う` (Hiragana u, 2 strokes)
  - ID 30: `え` (Hiragana e, 2 strokes)
  - ID 31: `か` (Hiragana ka, 3 strokes)
  - ID 32: `き` (Hiragana ki, 4 strokes)
- **Practice Attempts Missing ID Audit**:
  - `COUNT(*)`: 112 practice attempts.
  - `MAX(id)`: 116.
  - Absent IDs from 1 to 116: `ids 8, 10, 12 and 89 are absent; cause not independently verified`.
- **Learner 1 Deliberate Traces (IDs 110–116)**:
  - All 7 attempts submitted on Character 2 (`あ`), Learner 1, between 17:52:52 and 17:55:55:
    - ID 110: 2 strokes drawn, Handwriting 56.82, Stroke Order 47.67
    - ID 111: 3 strokes drawn, Handwriting 88.71, Stroke Order 16.95
    - ID 112: 3 strokes drawn, Handwriting 88.22, Stroke Order 88.01
    - ID 113: 3 strokes drawn, Handwriting 88.10, Stroke Order 87.75
    - ID 114: 3 strokes drawn, Handwriting 87.74, Stroke Order 28.21
    - ID 115: 3 strokes drawn, Handwriting 88.02, Stroke Order 87.78
    - ID 116: 3 strokes drawn, Handwriting 87.86, Stroke Order 88.06

### 2. Chunk 4F Stroke Order Diagnosis & Evaluator Findings [RAN AND VERIFIED]
- **Storage of Drawn Strokes**:
  - Verified that `practice_attempts` stores drawn stroke vectors in the `stroke_data` JSON column (DOM $(x, y)$ coordinate points and millisecond timestamps).
- **Geometric Comparison against KanjiVG Reference Strokes**:
  - Chunk 4F compared the stored stroke data with the reference strokes.
  - In attempts 111 and 114 the strokes were drawn in a different order from the reference (111: vertical, vertical, horizontal; 114: vertical, horizontal, loop).
  - Attempt 94 is a best fit for a different order (weaker evidence).
  - Attempt 96 has a zero-length first stroke (a dot) and two diagonal strokes; the cause of the dot is UNVERIFIED.
  - In four traces drawn in the reference order (112, 113, 115, 116) stroke order scored 87.75 to 88.06.
  - Attempt 110 (2 strokes) was not analysed in 4F.
  - This is one person and a tiny sample. Do NOT write that the scorer is "not too strict" or "is accurate".
- **Observed Scorer Limitations (Not Changed in Code)**:
  - (a) Stroke order is compared position by position, so swapping two strokes of the same drawing cost about 60 to 70 points on stroke order while handwriting stayed about 88 (shape ignores order).
  - (b) A zero-length stroke (a tap) counts as a stroke.
  - (c) The direction check is a hard switch at cosine 0 (cosines of -0.005 and -0.13 are both set to 0).
  - (d) Strokes 2 and 3 of あ both point downward, so swapping them is penalised only by path distance.

### 3. Chunk 4E-ADD Part A Verification Results [RAN AND VERIFIED]
- **A1. Stored `stroke_data` JSON Text Comparison**:
  - Attempts 100 vs 101: **IDENTICAL**.
  - Attempts 102 vs 103: **IDENTICAL**.
  - Wording applied: `"identical stored stroke data, so the same drawing was saved twice"`.
- **A2. Live Database Row Counts (`backend/scripts/show_table_counts.py`)**:
  - Exact output line as of 2026-11-17 18:10:16:
    `as of 2026-11-17 18:10: 112 practice attempts, 746 total rows (regenerate with backend\scripts\show_table_counts.py)`
  - Table breakdown: `users`: 3, `languages`: 12, `characters`: 250, `learning_lessons`: 356, `lesson_progress`: 13, `practice_attempts`: 112. Total: 746 rows.
- **A3. `backend/main.py` vs Newest Backup Audit**:
  - `backend/main.py`: size 66967 bytes, modified 2026-11-17 06:16:45, SHA-256 `68f4f3c881e615676e6c4448d81cc35f6d4119bd2eb28056836d8b26556bc39f`.
  - Newest backup `backend/main.py.bak-2026-11-17-061630`: size 66237 bytes, modified 2026-11-16 22:56:03, SHA-256 `4d75899c7531e03db8816ca7ff96ac0811c723733b1678f64109df89cc428f5d`.
  - Identical: **False** (`main.py` was modified at 06:16:45 when that backup was created, and has remained untouched since).
- **A4. Chunk 4F Created Files & Environment Safety**:
  - Files created in Chunk 4F:
    - `C:\Users\CHETAN\.vscode\StrokeSpeak\backend\scratch\diagnose_あ_stroke_order.py`
    - `C:\Users\CHETAN\.gemini\antigravity\brain\ef6c5a04-a48a-4702-a9c0-44e5461eece1\.system_generated\steps\2319\output.txt`
  - Inside project folder: ONLY files in `backend\scratch\` were created; nothing outside `scratch\`.
  - Exit code 1 explanation: PowerShell stripped backslashes from nested quotes `[\"handwriting_score\"]` inside inline `python -c` parameter string, causing Python `SyntaxError: unterminated string literal`.
  - Side effects of importing from `main.py` in Chunk 4F: Instantiated in-memory FastAPI `app = FastAPI(...)` object. It did NOT open a database connection (`get_db_connection` is imported, not called at module level), did NOT start a server process, and did NOT start background tasks.

### 4. Extended Human Drawing Test Table (IDs 93–116) [RAN AND VERIFIED]

| Attempt ID | Character (Glyph / ID) | Strokes Drawn | Ref Strokes | Handwriting Score | Stroke Order Score | Created At | Pattern / Observation |
|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|:---|
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

- **Sample Context**: Sample is 24 attempts by one person with a mouse on 5 characters; IDs 110–116 are a deliberate careful trace of あ.
- **Handwriting Range for Matching Stroke Count**: 71.52 to 88.71.
- **B8 Verification**: Audited all 5 project documents and `HANDOFF_REPORT.md` for `"お"` next to ID 31. Result: **0 occurrences**; character 31 is everywhere correctly documented as `"か"`.

### 5. Database Changes
- **NONE** (Zero database writes performed in Chunks 4E-CHECK, 4F, and 4E-ADD; all tables strictly preserved).


---

## 36. Systematic Documentation Alignment & Synthetic-Trace Provenance (Chunk 4A) (2026-11-17)

### 1. Part 0: Read-Only Audit of `backend/main.py` [RAN AND VERIFIED]
- **0.1 All Backups of `backend/main.py`**:
  - `backend/main.py`: size 66967 bytes, modified 2026-11-17 06:16:45, SHA-256 `68f4f3c881e615676e6c4448d81cc35f6d4119bd2eb28056836d8b26556bc39f`
  - `main.py.bak-2026-11-16`: size 51524 bytes, modified 2026-10-29 19:50:21, SHA-256 `199232bc31fbaf3fc3e4fa62518057abd00e14cbfc0ac620d2186aba4f8843c9`
  - `main.py.bak-2026-11-16-065834`: size 57729 bytes, modified 2026-11-16 06:43:44, SHA-256 `bcd5724a64b3defaadb6fe3effe47a6718217832706af521c80ed8c43ae1da42`
  - `main.py.bak-2026-11-16-071138`: size 60902 bytes, modified 2026-11-16 07:00:56, SHA-256 `e5fd5d25d7582d7ebc643033cfee1c3acad88c3b374d4e6a740c6fcc3b2420fe`
  - `main.py.bak-2026-11-16-075813`: size 60917 bytes, modified 2026-11-16 07:11:38, SHA-256 `2b1fde92e6756f4e36ee1561f5f7c7f64668be8fec063b8fda1d631fc6763fdd`
  - `main.py.bak-2026-11-16-154340`: size 61815 bytes, modified 2026-11-16 07:58:13, SHA-256 `04807c60900207ded251b9f680a611a2e028547b05a741cc3ee68c71cb21a449`
  - `main.py.bak-2026-11-16-163603`: size 63382 bytes, modified 2026-11-16 15:43:40, SHA-256 `ace7c92eaf90e8cde371a0dbe867108c488133bfba81a8f7aee431470c63145f`
  - `main.py.bak-2026-11-16-224129`: size 64775 bytes, modified 2026-11-16 16:38:13, SHA-256 `0d06e23945b645a6b03bac1b03b621349fe1126c05e55e31b38dee61ea1f3c60`
  - `main.py.bak-2026-11-17-061630`: size 66237 bytes, modified 2026-11-16 22:56:03, SHA-256 `4d75899c7531e03db8816ca7ff96ac0811c723733b1678f64109df89cc428f5d`
- **0.2 Unified Diff & Scope Explanation**:
  - Unified diff of `main.py.bak-2026-11-17-061630` against `main.py`: exactly 730 bytes added.
  - Function modified: only `_evaluate_strokes(learner, reference, is_too_small)` (lines 356–385).
  - Scope: Changes stroke-order calculation to per-stroke evaluation with start-to-end vector cosine check (`cos_sim < 0` clamps to 0). It does NOT touch anything except the direction check in stroke-order scoring; handwriting shape scoring and response schemas remain 100% untouched.
- **0.3 Environment Variable Names**:
  - `OPENAI_API_KEY`, `STROKESPEAK_OPENAI_TRANSCRIPTION_MODEL`, `STROKESPEAK_TRANSCRIPTION_PROVIDER`, `STROKESPEAK_WHISPER_MODEL` (names only, no values).
- **0.4 Scratch Files**:
  - `backend/scratch/read_prompt.py` (temporary script for reading transcripts without quote stripping) confirmed present.
  - Chunk 4F `output.txt` confirmed present at `C:\Users\CHETAN\.gemini\antigravity\brain\ef6c5a04-a48a-4702-a9c0-44e5461eece1\.system_generated\steps\2319\output.txt`.

### 2. Part A: Synthetic-Trace Chronological Verification [RAN AND VERIFIED]
- **A1. Practice Attempts 57 to 73 Timestamp Audit**:
  - Executed read-only query on MySQL: `SELECT id, character_id, user_id, handwriting_score, stroke_order_score, created_at FROM practice_attempts WHERE id BETWEEN 57 AND 73 ORDER BY id ASC`.
  - Cutoff timestamp: `2026-11-17 06:16:45`.
  - Result: All 17 attempts (57 to 73) were created between `2026-11-17 06:21:09` and `2026-11-17 06:21:10`.
  - **Status: ALL AFTER 06:16:45**. None predate the direction check. All reflect post-change directional scoring.
- **A2. Search Across Documentation**:
  - Comprehensive audit performed across all markdown files for specified terms.
- **A3. Swagger Safety Warning**:
  - Standardized safety rule added across `RUN_INSTRUCTIONS.md`, `DEMO_SCRIPT.md`, and `API_OVERVIEW.md`.

### 3. Part B: Documentation Policy Harmonization [RAN AND VERIFIED]
- **B1. Synthetic Trace Score Ranges**:
  - Model baseline reference traces: 100
  - Wobble variants ($\pm 0.015$): handwriting 96.35 to 97.12 and order 88.90 to 96.45 (attempts 57, 60, 63, 66, 69, 72)
  - Shifted 15% and scaled to 60%: handwriting 78.66 to 89.00 and order 84.19 to 89.55 (attempts 58, 61, 64, 67, 70, 73)
  - Labeled everywhere: "synthetic traces generated from the reference strokes, not human drawings".
- **B2. Curriculum & Lesson Nomenclature**:
  - Everywhere aligned to: `"127 lessons under ja-hiragana (99 Foundation, 25 Beginner, 2 Elementary, 1 Advanced) plus 1 lesson under ja-katakana"`.
  - Removed "Katakana lessons included" and every "128". Public lessons total 165 (127 + 23 Tamil + 9 Sanskrit + 1 Katakana + 5 Chinese), 191 legacy; counts as of 2026-11-17.
- **B3. Audio & Pronunciation Canonical Disclaimer**:
  - Everywhere aligned to: `"Pronunciation SCORING is not implemented. The app records speech locally in the browser and plays it back for self-comparison with the reference audio. No audio is uploaded. The backend contains routes for saving audio, transcription (provider configured as openai) and text comparison, but the app does not call them. Attempt 11 was a typed-text test through the text-comparison route (no audio). Text comparison is string matching and does not evaluate accent or phonetics. CNN, OpenCV preprocessing and Whisper are future scope, not implemented."`
  - Removed claims that audio routes were "never used" and claims of pronunciation scoring, accuracy or speech recognition.
- **B4. Human Drawing Score Expectation**:
  - Replaced all score promises with: `"human drawings by one person scored from about 16 to 88; do not promise a score"`.
- **B5. Swagger `/docs` Safety Rule**:
  - Added to `RUN_INSTRUCTIONS.md`, `DEMO_SCRIPT.md`, and `API_OVERVIEW.md`:
    `"In Swagger (/docs) press Execute only on GET routes. Never press Execute on transcribe, pronunciation-audio or pronunciation-assessment, or on any POST/PUT/DELETE route; they can create rows or call an external service."`

### 4. Database Changes
- **NONE** (Zero database writes performed in Chunk 4A; all tables strictly preserved).

---

## 37. Current Continuation Checkpoint (2026-11-20)

### Completed in this continuation
- Public language API was verified to expose exactly four entries: Japanese (`ja-hiragana`), Sanskrit (Devanagari) (`sa-devanagari`), Tamil (`ta`), and Simplified Chinese (`zh-hans`). Katakana remains part of the Japanese tutor rather than a separate public language. No Arabic, Hindi, Telugu, Malayalam, Kannada, or Korean was exposed.
- Corrected the frontend label from `Simplified Chinese (Limited Prototype)` to `Simplified Chinese`; removed Hindi wording from public Devanagari fallback copy and renamed internal sequence variables to Devanagari-neutral names. Sanskrit reference audio is described as an approximate synthetic Indic voice. No legacy language rows were changed or deleted.
- Added immediate display of a just-submitted quiz result in the section quiz attempt history. Existing quiz submission behavior and API contract were preserved.
- Added and applied an additive migration for beginner section quizzes. Current totals: 10 quizzes and 48 questions across the currently available sections: Japanese 3, Sanskrit 3, Tamil 2, Simplified Chinese 2. Quiz attempts remain 0; no sample learner answers were submitted.
- User-specific lesson progression is connected to the quiz API. Live API check for user 2: Japanese Foundation 99/99 lesson rows are marked unlocked; Beginner 25 and Elementary 2 are locked because Foundation is not complete. The three Japanese Beginner quizzes show 11, 6, and 8 lessons respectively and remain unavailable until their section requirements are met.
- Local speech provider configuration is `local`; Faster-Whisper is installed. The transcription endpoint writes a transcript and normalized text-similarity score only after a saved audio attempt is transcribed. No audio was uploaded to a hosted provider and no speech score was fabricated.
- Frontend production build succeeded with Vite 8.3.5 on 2026-11-20.

### Preserved learner data / evidence
- Attempt 218 remains the real Japanese `あ` attempt owned by user 2. Current values: handwriting 84.02, stroke order 83.81, pronunciation `NULL`; it was not overwritten or repeated. The CNN classified it as `お` with 99.6% confidence despite three drawn strokes matching the reference count. This is a model error to investigate, not a corrected/fabricated score.
- Total practice attempts at checkpoint: 132. New section quiz attempt rows: 0. Existing practice rows and lesson progress were not modified by the quiz migration.
- The existing model verification/integration scripts passed on their supplied sample images earlier in this continuation. A read-only comparison of the available `あ`/`お` training images found 20/20 per class correctly recognized. The 200-image Hiragana dataset, with 20 base images per class and only three validation/test images per class, is too small to establish robustness on real learner drawings. Do not retrain until more genuine labeled errors are reviewed.

### Next real-user actions required
1. Open the Japanese Hiragana lesson for `い` with learner ID 2, draw the character yourself, and save once. The current practice screen was prepared with an empty canvas; no attempt was created by this continuation.
2. Record a genuine pronunciation sample on that saved attempt and use the local Faster-Whisper assessment. Report the returned attempt ID, transcript, and any Windows audio decoder error. Do not use the hosted OpenAI provider unless the user separately chooses it and understands API billing.
3. Open each eligible section quiz and complete it as a learner only after its lessons are complete; then confirm unlock progression through the live UI/API.
4. Continue testing CNN behavior with genuine labeled examples. Keep model predictions and geometric stroke scores clearly distinguished in feedback.
5. Generate tutorial video content only after the script-specific stroke/audio references are verified; keep current public language scope and Japanese Hiragana/Katakana grouping.

### Current run state
- FastAPI was started locally on `127.0.0.1:8000` during this continuation (PID 31132 at startup). Health and quiz endpoints responded successfully. If it has stopped, restart using PowerShell from the project root:
  - Backend: `Set-Location C:\Users\CHETAN\.vscode\StrokeSpeak\backend; .\.venv\Scripts\Activate.ps1; python -m uvicorn main:app --reload`
  - Frontend in a second terminal: `Set-Location C:\Users\CHETAN\.vscode\StrokeSpeak\frontend; npm run dev`
- For local pronunciation scoring, keep `STROKESPEAK_TRANSCRIPTION_PROVIDER=local`; do not print or share `.env` contents.
## 38. Local Speech and Tutorial Readiness (2026-11-20)

- Read-only Windows dependency check succeeded: PyAV 13.1.0 imports, Faster-Whisper imports, and PyAV reports WebM/Matroska demuxing plus Opus decoding support. This only confirms installed runtime components load; real microphone audio has not yet been decoded or scored. Keep the first genuine audio check on local provider, and preserve any exact decoder error if one occurs.
- The existing generated tutorial is registered as ready for lesson 61, Japanese Hiragana `あ`, and the frontend contains a `<video>` player for ready lesson videos. One MP4 exists under `backend/static/videos/` (about 1.18 MB). The current generator narration and stroke script are hardcoded for `あ`; do not reuse it for another glyph or language until the generator is generalized and references are verified.
- No microphone was opened, no synthetic voice sample was saved, no practice or quiz rows were created, and no video was generated in this checkpoint.
- Next learner checkpoint remains: use learner ID 2 to draw `い` and save once; record and save a real pronunciation sample on that new attempt, then run the local transcription assessment.
## 39. Remaining Work Inventory and Estimate (2026-11-20)

### Verified checkpoint
- Backend API and MySQL are connected; frontend was restarted and returned HTTP 200.
- Use `http://127.0.0.1:5173/?learner_id=3` for the next clean learner run. Learner 3 currently has no attempts or lesson progress; learner 2 has 17 historical attempts. The next useful validation is Japanese Hiragana `い`.
- Public API language groups: Japanese, Sanskrit (Devanagari), Tamil, Simplified Chinese. Japanese includes both Hiragana and Katakana in one tutor.
- Live curriculum inventory: Japanese combined Hiragana/Katakana 128 lessons; Sanskrit 26; Tamil 32; Simplified Chinese 14. Available advanced/intermediate curriculum varies by script; do not describe every level as complete.
- Active quiz inventory: 10 beginner section quizzes / 48 questions; zero quiz attempts. GET routes and current locks have been verified. A learner's successful submission and earned unlock remain unverified.
- Video inventory: one ready Japanese Hiragana `あ` tutorial. The generator is generalized for the other three groups but holds those candidates until reference provenance and genuine learner validation are established.

### Remaining validation matrix
- **Handwriting:** 1 of 41 target characters has a real recorded attempt (Japanese `あ`, attempt 218); 40 target-character samples remain: 9 Hiragana, 10 Sanskrit, 12 Tamil, and 9 Simplified Chinese. Each must be drawn by the learner. Attempt 218 remains the regression case and must not be repeated or overwritten.
- **Speech:** 0 of 4 script-group microphone validations completed. Save a real recording on an attempt for Japanese, Sanskrit, Tamil, and Simplified Chinese, then run local Faster-Whisper and record the true transcript, score, attempt ID, and any decoder errors. Runtime imports/codec availability passed, but this is not an end-to-end audio result.
- **CNN error analysis:** Attempt 218's `あ`→`お` error is recorded. Available sample-image comparison was 20/20 correct in each of those two classes. A verified root cause or low-risk correction is still outstanding; do not retrain until more genuine labeled samples are reviewed.
- **Quizzes/progression:** Backend and frontend implementation plus data seeding are complete. One real learner quiz submission and subsequent unlock transition still need to be completed after the learner finishes the prerequisite lessons.
- **Integration:** Frontend production build, backend health, public language list, lesson/quiz GETs, and supplied-sample model inference have passed. Real mic, saved learner stroke flow for the remaining characters, quiz POST/unlock, and persistence across the complete flow remain to be checked.
- **Tutorial videos:** 1 of 4 script-group demonstrations exists. Three more remain held until references have verified provenance and target characters have genuine learner validation; never overwrite the existing video.

### Overall estimate
- **About 70% complete; about 30% remains.** This is a project estimate, not a measured test metric. The principal app, API, database, CNN inference, geometric scoring, speech endpoint, quiz feature, and one tutorial are implemented. Most remaining effort is evidence-based validation with genuine learner inputs, improving confidence in the CNN error analysis, one quiz/unlock walkthrough, and three safe video demonstrations.
- The current manual matrix is at **1/41 handwriting targets and 0/4 speech script groups**. Next, use learner 3 to draw Hiragana `い`, save once, then record and assess speech on that genuine attempt. Do not manufacture those samples.
## 40. CNN Regression Evidence Boundary (2026-11-20)

- Read-only schema inspection confirms `practice_attempts` stores timestamped `stroke_data` and audio, but no canvas image column. Attempt 218's original raster passed to CNN was not retained. Therefore the exact original pixels, thickness, and preprocessing path for that prediction cannot now be reconstructed from the database.
- Do not label a raster redrawn from stored coordinates as the exact original CNN input. Any future vector reconstruction must be identified as an approximation and kept separate from Attempt 218's recorded result.
- Safest next evidence is the next real learner drawing for `い` and the remaining planned characters. To make later CNN regressions diagnosable, consider an explicit retention decision for cropped canvas images before adding persistent image storage; this checkpoint did not change the schema.
## 41. Guarded Multi-Script Tutorial Generator (2026-11-20)

- Added `backend/app/ml/script_demo_video.py`, which reuses Sensei Kai and the existing smartboard renderer while reading each target character's actual normalized stroke vectors from MySQL. It renders generic, accurate stroke-following instructions instead of reusing the Japanese `あ` narration/three-stroke assumptions. It includes a language-specific spoken target via existing gTTS support (Hindi synthetic voice is used for Sanskrit as an approximation).
- Added `backend/scripts/generate_script_demo_videos.py`. Default invocation is a dry run. It targets these verified database records: Sanskrit `अ` lesson 339 (5 reference strokes), Tamil `அ` lesson 223 (3), Simplified Chinese `一` lesson 348 (1). It refuses to overwrite files and requires `--validated-lesson-id` for each lesson before generation/registration.
- Python compilation, dry-run inventory, and four-scene renderer smoke checks passed across Hiragana `い`, Sanskrit `अ`, Tamil `அ`, and Simplified Chinese `一` using their stored reference vectors. These checks validate code/rendering only; they do not establish linguistic correctness or count as learner handwriting/speech tests.
- No new video was generated or registered because none of the three target script characters has a confirmed genuine learner drawing yet. Existing Japanese `あ` video remains untouched. Database learner rows remain unchanged.
- Open `http://127.0.0.1:5173/?learner_id=3` for a clean profile. The next actionable step remains a real learner drawing and save, followed by a real voice recording and local assessment.
## 42. Female AI Teacher Update (2026-11-20)

- Updated the procedural Sensei Kai avatar to a female educator design: shoulder-length dark hair, glasses, small gold earrings, teal scarf, and StrokeSpeak indigo/navy clothing and board colors. The updated render is used by both the existing video generator and the guarded multi-script generator.
- Added a validated `variant` query parameter to `GET /api/v1/lessons/{lesson_id}/video`; file selection stays within the lesson video directory and supports versioned filenames. This avoids overwriting or ambiguously selecting the previous video.
- Generated a new Japanese Hiragana `あ` tutorial at `backend/static/videos/ja_hiragana_2_lesson61_female-v2.mp4`. The lesson 61 database metadata now points to `/api/v1/lessons/61/video?variant=female-v2`. The original `ja_hiragana_2_lesson61.mp4` remains untouched.
- Verified both video routes return HTTP 200 and valid MP4 (`video/mp4`) content. The new clip is 1280×720, about 32 seconds, and includes one audio stream. This changes tutorial media metadata only; learner attempts, scores, and progress were not changed.
## Realistic Female Tutor Portrait Update (2026-11-20)

- Added `backend/static/images/sensei_aoi_realistic_v1.png`, an original transparent photorealistic female educator portrait in an indigo blazer and teal scarf.
- Updated `backend/app/ml/video_generator.py` to composite that portrait beside the teaching board with a subtle vertical idle motion. The former procedural illustration remains as a fallback when the portrait asset is unavailable.
- Generated a new, versioned Japanese Hiragana `あ` tutorial: `backend/static/videos/ja_hiragana_2_lesson61_realistic-v3.mp4`. It is approximately 32 seconds with H.264 video and AAC narration. The video is a still realistic portrait composited over animated lesson graphics; it is not a live-action or lip-synced teacher recording.
- Verified the new file decodes (964 frames) and updated lesson 61's video metadata to `/api/v1/lessons/61/video?variant=realistic-v3`, status `ready`. The original and female-v2 videos remain unchanged.
- This metadata update did not change practice attempts, learner scores, or progress.


## Female Voice and Audio-Synchronized Tutor (2026-11-20)

- Updated `backend/app/ml/video_generator.py` to synthesize narration locally with the installed female Windows voice Microsoft Zira Desktop. No API key or hosted speech service is used. gTTS remains a fallback if Windows speech synthesis is unavailable.
- The realistic portrait mouth opening follows narration PCM amplitude at the corresponding video timestamp; the portrait keeps its natural closed smile during quiet intervals. This is waveform-level mouth synchronization, not phoneme-accurate face capture or a live-action talking-head model.
- Generated a separate 30.27-second version: `backend/static/videos/ja_hiragana_2_lesson61_female-lipsync-v4.mp4`. H.264/AAC decode passed (908 video frames). GET `/api/v1/lessons/61/video?variant=female-lipsync-v4` returned HTTP 200 with `video/mp4`.
- Lesson 61 metadata now points to the v4 URL and remains `ready`. Earlier video files remain available and unchanged. Learner attempts, scores, and progress were not modified.


## Multi-Script Tutor Voice and Windows Dry-Run Fix (2026-11-20)

- Updated `backend/app/ml/script_demo_video.py` so English teaching narration uses the same local female Windows voice as the Japanese demo (gTTS fallback retained), while each target character's script-specific sound remains generated with the language voice configured for that script.
- Replaced the unrelated looping mouth animation with waveform-based mouth opening using the synchronized narration PCM timeline. This shares the same limitation: it follows speech and pauses but is not phoneme-accurate lip capture.
- Fixed `backend/scripts/generate_script_demo_videos.py` dry-run output to print portable Unicode code points instead of raw non-ASCII glyphs, avoiding a Windows PowerShell `cp1252` encoding crash.
- Python compilation succeeded. Read-only dry run lists the remaining canonical targets and references: Sanskrit U+0905 lesson 339 (5 strokes), Tamil U+0B85 lesson 223 (3 strokes), Simplified Chinese U+4E00 lesson 348 (1 stroke). No demo videos were generated, no lesson metadata was registered, and no learner rows were changed; the generator still requires genuine learner drawing validation before those demos are generated.


## Tamil Course Ordering Correction (2026-11-20)

- Added `backend/scripts/normalize_tamil_lesson_order.py`, an idempotent MySQL transaction that refuses to move lessons with saved learner progress.
- Moved lesson 301 (the polite water request) from the Tamil foundation consonant section to beginner unit 1, order 5, following the four beginner words; that section quiz already contains five questions.
- Reordered the vowel contrast lesson 300 to foundation unit 2 order 6 and Tamil greeting lesson 56 to foundation unit 3 order 5. Normalized the single elementary/advanced grammar lesson units (303/304) to unit 1, order 1.
- Existing records for these five lesson IDs had no user progress. Lesson content, references, attempts, scores, quiz attempts, and hidden-language rows were not modified. The live `/api/v1/lessons` response reflects the corrected order.

## 47. Stroke Reference Provenance Disclosure (2026-11-20)

- Corrected the public Sanskrit, Tamil, and Simplified Chinese reference metadata for 32 records. The earlier source and license labels were unsupported; those original values remain in `previous_source_label` and `previous_license_label`, while the active provenance status is `unverified` and the license field says not to redistribute.
- No stored stroke vectors or learner records were changed. The guarded demo generator now refuses to generate/register those three tutorial videos until the paths have verified provenance and genuine learner validation.
- Updated the learning interface to show a visible “Draft stroke guide” warning whenever reference metadata has `provenance_status: unverified`, so the animation is not presented as authoritative.
- Japanese Kana remains attributed to KanjiVG. The provenance migration and guarded dry-run were applied/checked against the public scope only; hidden legacy languages remain excluded.

## 48. Script-Specific Speech Language Codes (2026-11-20)

- Faster-Whisper's installed tokenizer supports Sanskrit (`sa`), so Sanskrit recordings now request Sanskrit transcription rather than being silently classified with the Hindi language code. This improves language conditioning; a real learner recording is still required to validate recognition quality.
- Added Japanese Katakana to the reference-audio voice map. Katakana lessons now use the existing Japanese gTTS voice instead of returning “Reference speech is not configured”.
- gTTS has no Sanskrit voice in the installed package; Sanskrit reference playback remains an explicitly labeled approximate Hindi/Indic synthetic voice in the UI. No attempt rows or scores were added or changed.

## 49. Honest Speech Score Messaging (2026-11-20)

- The practice screen now calls the output “Transcript similarity” and explains that the score compares recognized text with the target; it does not yet measure phoneme-level articulation. This matches the current Whisper + normalized text similarity implementation and avoids implying an acoustic phonetics model is already working.
- Frontend production build passed after adding both this explanation and the unverified-reference draft warning.

## 50. Consolidated Completion Checkpoint (2026-11-20)

- Current verified counts remain: handwriting 1/41 planned characters (40 genuine learner drawings outstanding), real microphone validation 0/4 script groups, learner quiz submissions/unlocks 0, and ready script-group tutorials 1/4. UI/build and API implementation changes in entries 47–49 do not increase learner-validation counts.
- The multi-script video generator is now generalized and guarded; rendering for Sanskrit, Tamil, and Simplified Chinese remains on hold until source provenance and genuine learner validation are available.
- Fixed transcription conditioning for Sanskrit and reference TTS routing for Katakana. The learner-facing score text accurately describes the existing transcript-similarity algorithm.
- No new attempts, scores, recordings, quiz submissions, or progress were fabricated. Next real learner validation remains drawing Hiragana `い`, saving it, then recording and assessing a real sample; quiz progression requires a real learner to complete its prerequisites and submit the quiz.

## 51. Combined Japanese Tutor and Current-State Documentation (2026-11-20)

- Integrated the standalone Katakana five-vowel summary, lesson 315, into the primary Japanese language row (language 5), Foundation unit 3, order 6. Existing unit lessons retain orders 1–5; existing progress was preserved (learner 1 remains `in_progress`, score 80).
- The guarded transactional migration `scripts/integrate_katakana_summary_lesson.py` verifies the exact source/target state and is safe to rerun. Live `GET /api/v1/lessons?language_id=5&user_id=1` now returns lesson 315 and 128 total Japanese lessons; the Katakana-vowels unit returns six ordered lessons.
- Read-only quiz audit across all four public tutor groups confirmed 10 quiz records / 48 questions and a corresponding quiz for every Beginner unit. This does not validate a learner’s pass or unlock transition; learner quiz attempts remain zero.
- Read-only table-count utility reports users 3, languages 12, characters 250, learning_lessons 391, lesson_progress 17, practice_attempts 132 (805 total). Public script rows include 200 lessons; 191 legacy lessons remain hidden. Learner counts are IDs 1: 107 attempts/15 progress, 2: 17/0, 3: 0/0.
- Added `docs/CURRENT_PROJECT_STATUS.md` and corrected current-state claims in limitations, run instructions, demo/PPT/report/API/database/screenshot/test documentation. Documentation now identifies learner 3 as the clean profile, discloses draft stroke provenance, and describes transcription output as transcript similarity.


## 52. Simplified Chinese Stroke Data Attribution (2026-11-20)

- Verified the upstream `hanzi-writer-data` repository documentation and pinned npm package version 2.0.1, which attributes its data to Make Me a Hanzi and declares the Arphic Public License. Added the ten exact starter-glyph JSON files, package metadata, and full `ARPHICPL.TXT` under `backend/data/reference_strokes/hanzi-writer-data-2.0.1/`.
- Added `backend/scripts/import_hanzi_writer_reference_strokes.py`. It validates the package/version/license files, imports upstream ordered medians into normalized strokes and SVG paths, records source URLs and SHA-256 hashes, and creates a pre-import MySQL rollback backup. Applied it to the ten `zh-hans` rows only.
- The database now marks these records `source_attributed` while `instructional_review_status` remains `pending`. UI warns learners that the source has not been reviewed by a qualified instructor. Future demo output calls these “reference dataset strokes” and exposes source credit.
- No learner data was added or changed. The Chinese demo remains withheld until instructional review and a genuine learner drawing validation; Sanskrit and Tamil still need source provenance work as well as real learner validation.


## 53. Attributed Devanagari Starter Paths (2026-11-20)

- Verified Lipi's model card: its Devanagari pen-hand centerlines are hand-drawn in writing order and licensed CC BY 4.0. Pinned revision `c547139c82130da50827a1f2bffb995254395600`; vendored its model card, 52 KB weights artifact, and CC BY 4.0 legal text.
- Added `backend/scripts/import_lipi_devanagari_reference_strokes.py`, which parses the Safetensors header and arrays without new dependencies, validates the pinned SHA-256, extracts exact glyph boundaries, writes normalized paths, and creates a pre-import rollback backup. Imported only exact standalone glyphs अ, इ, उ, ऊ, ए; composite/other vowel forms remain unverified.
- Metadata is `source_attributed`, while `instructional_review_status` is `pending`; the interface displays that status. The video renderer now uses source-specific concise attribution. The video generator holds Sanskrit/Chinese references pending qualified review.
- Current active unverified source rows: Sanskrit 5, Tamil 12. No learner data was created or changed.

## 54. Language Reviewer Worksheet (2026-11-20)

- Added `docs/REFERENCE_REVIEW_WORKSHEET.md` with exact IDs/statuses for 14 Sanskrit vowels, 12 Tamil vowels, and 10 sourced Chinese starter characters.
- The worksheet separates data-license/source attribution from pedagogical sequence approval and lists the evidence a reviewer must record. It also preserves the genuine learner-drawing gate for tutorial generation.
- This is a review aid only; it makes no approvals and changes no database or learner records.


## 55. Sanskrit Foundation Vowel Sequence (2026-11-20)

- Audited the live lesson rows and found ॠ, ऌ, ॡ already existed in the character table but were omitted from the Foundation vowel unit; the sequence jumped from ऋ to ए. Added lessons 392–394 and reordered unit 1 to अ आ इ ई उ ऊ ऋ ॠ ऌ ॡ ए ऐ ओ औ.
- Added concise explanations and IAST transliterations; the Library of Congress 2012 Sanskrit/Prakrit romanization table supports the spellings. Because these three vowels have no reviewed stroke paths and Sanskrit TTS is approximate, the lessons do not claim exact stroke/audio assessment.
- Added `backend/scripts/complete_sanskrit_vowel_lessons.py` with state checks, a pre-change backup at `backend/data/backups/before_sanskrit_complete_vowel_set.json`, and refusal to move existing lessons with progress. Live `/api/v1/lessons?language_id=56` returns all 14 in order. Existing lesson progress rows remained 17; no attempt/score/quiz/progress rows were added or changed.
- Current counts: 394 total learning lessons, 203 public lessons, 808 total rows across the six core tables. Sanskrit now has 29 lessons (Foundation 19, Beginner 10).


## 56. Signed Learner Sessions and Account Ownership (2026-11-21)

- Added `backend/app/security.py`, a stdlib HMAC-SHA256 access-token helper with an eight-hour expiry, issuer check, constant-time signature comparison, bearer dependencies, learner-scope checks, and an administrator ID allowlist. A random 64-character `STROKESPEAK_AUTH_SECRET` is configured in the local backend `.env`; its value was never printed. `STROKESPEAK_ADMIN_USER_IDS` is empty by default.
- Registration now returns a signed token and login tokens are validated. `/api/v1/auth/me` resolves the account from its Bearer token. Attempts, recording uploads/transcription/assessment, attempt history, lesson progress, and quiz listing/details/submissions are bound to the authenticated user. Shared lesson, language, character, video, and reference-stroke mutations require the configured admin allowlist.
- Added React account registration/sign-in, token persistence/session restore/sign-out, a shared token-aware API helper, and hid instructor reference maintenance from learner accounts. The manual learner-ID control was removed.
- Python syntax compilation, FastAPI OpenAPI generation (26 paths), and the Vite production build succeeded. No learner rows, scores, attempts, or progress were created or changed by this work. The user still must restart backend/frontend and sign in once to validate their local account end-to-end.
- Remaining deployment limits: localStorage Bearer token, no HTTPS on local development, refresh/revocation and account recovery are not implemented; configure an admin account ID intentionally before using shared content maintenance.


## 57. Prototype Stroke Scoring Noise Handling (2026-11-21)

- Added arc-length resampled local-tangent direction comparison to the geometric stroke-order prototype. Direction disagreement now changes the score gradually instead of using a hard negative-cosine switch.
- Added scoring-only removal of unmatched stationary taps when the reference has no stationary stroke to compare. If a reference contains stationary strokes, the same number of learner taps is preserved. The original learner stroke arrays remain stored unchanged; the API reports `ignored_stationary_stroke_count` and includes the tap note in feedback.
- This affects only future practice scores; previous attempt rows and scores were not recalculated. Python syntax compilation passed. No new drawings or benchmark claims were created. One-to-one stroke index alignment still penalizes swapped or inserted moving strokes and remains a known prototype limitation pending genuine learner evidence.

## 58. Lipi ऋ Reference Path and Review Gate (2026-11-21)

- Extended the pinned Lipi importer to include the exact standalone ऋ (U+090B) glyph. Database character ID 222 now has three normalized strokes with `provenance_status: source_attributed`, CC BY 4.0 attribution, and `instructional_review_status: pending`.
- Created `backend/data/reference_strokes/backups/before_lipi_rishi_extension_2026-11-21.json` before importing. A read-only verification confirmed zero practice attempts for character 222; the import changed reference metadata only and did not modify learner records.
- Updated the Lipi source README, reference-review worksheet, current status and limitations. The instructor must verify the three-stroke form/order against the chosen Sanskrit writing convention before this path is treated as instructional or used to release a Sanskrit tutorial.
- The five other active Sanskrit draft paths and twelve Tamil paths remain unverified. This update adds no learner drawings, scores, recordings, quiz submissions, video registrations, or instructor approvals.

## 59. Authenticated Script Demo Registration (2026-11-21)

- Fixed `backend/scripts/generate_script_demo_videos.py` to preflight the signed administrator token against `/api/v1/auth/me` before rendering, then include the Bearer token on the protected tutorial-video registration request. Token entry is hidden with `getpass` and the token is never printed.
- The generator still enforces attributed/approved reference metadata and the explicit genuine-drawing validation gate. Its read-only dry run currently holds Sanskrit `अ` lesson 339 for instructor review, Tamil `அ` lesson 55 for unverified provenance, and Chinese `一` lesson 348 for instructor review. No video was generated or registered because source review and learner evidence remain pending.
- Updated the safe run instructions and current project status. Python syntax parsing passed; no database or learner rows changed.

## 60. Fingerprinted Instructor Reference Review (2026-11-21)

- Added `backend/app/reference_paths.py` to fingerprint ordered normalized point paths plus source SVG paths and viewBox, excluding capture timestamps.
- Added administrator-only `POST /api/v1/characters/{character_id}/reference-review` and an instructor form in the existing app panel. Review records include reviewer-provided name/qualification, standard, writing convention, decision, notes, server UTC timestamp, and the geometry SHA-256. Approval requires attributed source/license metadata and an explicit exact-path attestation; reviewer credentials remain self-reported.
- `GET` marks a stale approval pending when its fingerprint no longer matches. The script-demo generator requires `approved` plus the exact current fingerprint. Canvas edits cannot overwrite source-attributed paths. A changed draft gets a rollback backup, loses stale SVG paths/source attribution, and remains unverified/pending.
- The instructor checklist now reflects references already loaded from the database and counts only the selected tutor group. The unavailable-reference message no longer claims that Japanese is the only sourced group.
- Backend syntax/OpenAPI generation reports 27 paths; the Vite production build succeeded. The read-only video dry run still holds three candidates. No review was submitted, no learner rows changed, and no video was rendered.


## 61. Final Audit Cleanup (2026-11-21)

- Disabled the legacy spare-learner seeder because it created users with a placeholder password hash. It now performs no database operations and directs the developer to normal account registration. Existing database rows were left untouched.
- Updated the legacy submission package README to describe the current four-language scope, implemented feature limits, and authoritative setup/status documents; removed obsolete demo-password instructions. The packager now excludes backup artifacts, local editor settings, and likely private upload/recording folders. The packager was not run.
- Marked the old hard-angle scoring measurements as historical in the project report and checklist. The active gradual local-tangent scorer and unchanged historical score rows are described in Section 57.
- Verification: AST parsing succeeded for 13 backend Python files; FastAPI generated 27 OpenAPI paths including the protected reference-review and tutorial-video routes; the React/Vite production build succeeded. No learner drawings, recordings, scores, quiz attempts, reviews, or videos were created.


## 62. Read-Only Database Snapshot Refresh (2026-11-21)

- Read aggregate counts from MySQL without modifying rows: users 4, languages 12, characters 250, learning_lessons 394, lesson_progress 17, practice_attempts 132 (809 rows across these six core tables); section_quizzes 10, section_quiz_questions 48, section_quiz_attempts 0.
- Public lesson counts remain Japanese 128, Sanskrit 29, Tamil 32, Simplified Chinese 14 (203 total). Japanese Katakana remains part of the same tutor and is represented by its combined public-language group.
- Refreshed the current status, report snapshot, PPT talk-track, and checklist header to remove the older 808-row/three-user snapshot. No learner data was read beyond aggregate counts and no database writes were made.


## 63. Documentation Count and Account-Guidance Reconciliation (2026-11-21)

- Refreshed the setup runbook, limitations page, presentation notes, screenshot checklist, and demo run instructions with the live 809-row/203-public-lesson snapshot.
- Removed stale instructions that named old learner profiles for login; the current guidance says to register a real account, because two placeholder-hash accounts are disabled.
- A final active-document scan found no remaining current-state 808-row or stale demo-password claims. Older dated test records remain labeled historical. No database writes were made.


## 64. Retired Unverified Reference Writers (2026-11-21)

- Replaced `correct_tamil_reference_strokes.py`, `apply_stage5a2_handwriting_updates.py`, and `seed_stage5a_reference_strokes.py` with no-write stubs. Their prior generated geometry carried unverified source/license claims; current runbooks do not depend on them. Backups preserve the historical source for review.
- No MySQL records, reference paths, provenance fields, review decisions, or learner data were changed. The current status now reports four user rows without an obsolete per-user breakdown.


## 65. Legacy Package Output Safety (2026-11-21)

- Changed the old submission helper to refuse deleting an existing staging directory and refuse overwriting an existing ZIP. It was not run, so no external staging/archive files were touched.


## 66. Stored Audio Metadata Audit (2026-11-21)

- A read-only aggregate query found one Sanskrit `U+0905` attempt with 4,992 bytes of `audio/mpeg`, a completed transcription, and a speech score. The audio bytes and transcript text were not opened. MIME/metadata do not establish that it was captured from a learner microphone, so it is not counted toward the 0/4 genuine microphone validation matrix.
- Japanese Hiragana has one transcribed/scored attempt without a saved audio blob; Katakana, Tamil, and Chinese have no saved public-scope audio blobs in this audit. No database values were changed.


## 67. Retired Synthetic Attempt Writers (2026-11-21)

- Replaced `audit_stage5a3_handwriting.py`, `verify_section5_api.py`, and `verify_stage5a_scoring.py` with no-write stubs. The former versions posted generated reference traces as practice attempts and deleted the created rows after checks.
- Backups preserve the old scripts for audit. None were run in this turn; no practice attempt was created or deleted. The status document now distinguishes authentic learner validation from synthetic scoring smoke traces.


## 68. Explicit Katakana CNN Coverage (2026-11-21)

- Added `ja-katakana` to the model registry as `UNTRAINED`, with no model file/classes and a clear note that geometric practice remains available. The recognition API can now report `script_not_trained` instead of treating the public Katakana script as unknown.
- Documented current trained coverage: 10 Hiragana, 10 Sanskrit, 12 Tamil, and 9 Simplified Chinese classes (41 total). Updated the old sample-verification script's final label to call its results a one-sample smoke check, not an accuracy estimate.
- No model training, learner data, or database writes were performed.


## 69. Final CNN Coverage Wording (2026-11-21)

- Corrected the numbered implementation summary to distinguish four trained models from the fifth registered script code (Katakana, untrained). The full list of covered classes and limitations is now consistent with the API response.


## 70. Exact Project Title Consistency (2026-11-21)

- Aligned the browser tab, presentation title slide, presentation metadata, and generated submission README template with the approved title: **StrokeSpeak: An AI-Powered Multilingual Handwriting and Pronunciation Learning and Assessment Platform**.
- This is a documentation/UI metadata change only; no application behavior, database content, learner evidence, or model claims changed.


## 71. Clean Submission Archive (2026-11-21)

- Created `backend/scratch/StrokeSpeak-submission-v4-2026-11-21.zip` (1,094 files; 16,113,380 bytes). The staging and archive paths are guarded against overwriting existing files.
- The archive passed ZIP CRC validation and a member-name scan: no virtual environments, build caches, backups, uploads, recordings, handoff log, or secret environment files were included. Only `backend/.env.example` is present as a safe configuration template.
- Package metadata uses the approved project title and the README describes current feature limitations. No learner data or database rows were changed while packaging.


## 72. Visible AI Teacher Motion (2026-11-21)

- Investigated the reported poster-like teacher. The active lesson 61 URL referenced `female-lipsync-v4`; frame inspection showed the realistic portrait was nearly static while only the lesson board changed. The old renderer moved the cutout by about two pixels and opened the mouth by only a few pixels.
- Updated the portrait renderer with visible sway/lean and speech mouth movement. Generated a separate 30.3-second `ja_hiragana_2_lesson61_female-lipsync-v5.mp4` using the locally installed Microsoft Zira Desktop voice. The original v4 video remains untouched. A frame comparison on the teacher region rose from 1.48 to 11.03 mean pixel levels; visual contact-sheet inspection confirms the pose and mouth visibly change. This is still 2D portrait compositing, not live-action animation or phoneme-accurate lip sync.
- Preserved the database lesson URL and added a narrow lesson-61 compatibility mapping so its existing `female-lipsync-v4` URL serves the v5 clip. The lesson modal now requests automatic inline playback and retains normal video controls. No database rows were changed.
- Frontend production build passed. A temporary API on port 8001 returned HTTP 200 and `video/mp4` for the existing lesson URL, with the v5 filename; the temporary server was stopped.


## 73. Updated Animated-Teacher Submission Package (2026-11-21)

- Built `backend/scratch/StrokeSpeak-submission-v5-2026-11-21.zip` after the motion renderer, API compatibility route, autoplay UI, and project status were updated. The earlier v4 archive and its staging directory remain untouched.
- The v5 package includes the new `female-lipsync-v5` clip and the matching source changes; generated staging/archive files remain excluded from the archive itself.


## 74. Katakana Dataset Intake and Training Pipeline (2026-11-22)

- Added `backend/data/katakana_dataset/README.md`, `backend/scripts/preflight_katakana_dataset.py`, and `backend/scripts/train_katakana_cnn.py`. The pipeline requires all 46 standard Katakana classes, readable unique images, writer IDs, a source checksum, citation, and a manifest explicitly recording that the user accepted AIST's current terms. Training splits by writer before sampling and only augments the training split.
- Identified AIST ETL6 as a candidate source: its official overview describes 46 Katakana classes; AIST's terms say use is free, AIST retains copyright, and database redistribution is limited to the official site. The raw dataset is not included in project packages. Source: https://etlcdb.db.aist.go.jp/the-etl-character-database/ and https://etlcdb.db.aist.go.jp/download2/.
- No dataset download, synthetic image generation, model training, registry update, or database write occurred. The Katakana registry remains `UNTRAINED` until a user obtains/accepts the source terms, installs the dataset, and reviews the writer-held-out results.
- Updated the package builder to exclude every Katakana dataset file except its README; the training script writes draft artifacts under the excluded data directory and does not activate them.


## 75. Katakana-Ready Submission Package (2026-11-22)

- Built `backend/scratch/StrokeSpeak-submission-v6-2026-11-22.zip` (1,098 entries; 17,574,853 bytes) from the guarded v6 packager.
- The ZIP passes CRC integrity verification and includes the Katakana dataset README, read-only preflight, and writer-disjoint training script. Only the README is present under `backend/data/katakana_dataset/`; no ETL6 image payload or annotations are packaged.
- `backend/scripts/preflight_katakana_dataset.py` correctly reports that ETL6 and the user-accepted terms manifest are absent. The CNN registry remains `UNTRAINED`; no training, registry change, or database write was performed.
- All four user-facing docs reviewed during this change state the same coverage: four trained models / 41 classes, with Katakana untrained. This ZIP is a clean code handoff, not evidence that pending learner or instructor validation is complete.


## 76. Sequential Course-Level Access (2026-11-22)

- Fixed the backend lesson path so only Foundation is initially open. Beginner requires completed Foundation and keeps its existing section-by-section quiz gate; Elementary requires all Beginner sections and quizzes; Intermediate requires all Elementary lessons; Advanced requires all Intermediate lessons. Later units within Intermediate/Advanced wait for completion of the prior unit.
- The same rule now applies to both `GET /api/v1/lessons` unlock flags and `PUT /api/v1/lessons/{lesson_id}/progress`, so a direct API request cannot mark a locked higher-level lesson complete. Missing prerequisite levels remain locked instead of letting a learner skip ahead.
- Updated `docs/CURRENT_PROJECT_STATUS.md` and the generated submission README with the current progression. Backend syntax compilation succeeded and FastAPI generated 27 OpenAPI paths. No learner data or database rows were changed.
- Created `backend/scratch/StrokeSpeak-submission-v7-2026-11-22.zip` (1,098 entries; 17,577,501 bytes). ZIP CRC/content checks passed; Katakana payload is limited to its README; scratch/backups, ETL6 images, and annotation files are absent.


## 77. Module-by-Module Course Sequence (2026-11-22)

- Extended the shared lesson unlock helper so Foundation and Elementary units also unlock in order. Beginner units retain their prior-unit completion and quiz gates; Intermediate and Advanced require the whole preceding level, then the prior unit within their own level.
- Confirmed the public lesson structure with an aggregate-only MySQL query. It found multiple Foundation modules across each tutor group, so the existing all-open Foundation behavior allowed learners to skip modules. No learner-specific rows were queried or changed.
- Backend compilation succeeded and FastAPI still generates 27 OpenAPI paths. No test suite was run and no database write occurred.
- Built `backend/scratch/StrokeSpeak-submission-v8-2026-11-22.zip` (1,098 entries; 17,577,632 bytes). CRC and member checks passed; no staging/scratch/backups, ETL6 images, or annotations are included.
- Frontend course-level selector still needs a visible locked state for Intermediate/Advanced; lesson actions already respect the API's per-lesson `is_unlocked` flag. Keep that UI task in the separate frontend workstream.


## 78. Administrator Quiz Preview (2026-11-22)

- Added admin-only `GET /api/v1/admin/section-quizzes/{quiz_id}/preview`, which returns quiz questions/options and the answer key without checking learner prerequisites.
- Added admin-only `POST /api/v1/admin/section-quizzes/{quiz_id}/preview-grade`, which scores submitted preview answers in memory and returns whether the quiz would pass. It does not insert a `section_quiz_attempts` row, unlock a learner, or alter progress. The regular learner GET/POST routes retain all prerequisite gates.
- Added `docs/QUIZ_AUTHOR_PREVIEW.md` with account-ID setup, Swagger usage, and a sample preview-grade request. The creator's account must be explicitly listed in `STROKESPEAK_ADMIN_USER_IDS`; signing up alone does not make an account an administrator.
- Backend compilation succeeded. FastAPI generated 29 OpenAPI paths, including both new routes. Built `backend/scratch/StrokeSpeak-submission-v9-2026-11-22.zip` (1,099 entries; 17,579,574 bytes); CRC and content checks passed. No database rows were changed.

## 79. Quiz UI, Review, and Final Verification (2026-11-22)

- Completed the dedicated learner quiz panel with one-question navigation, numbered question selection, answer revision, answered count, submit validation, score/pass result, retry support, recent attempts, and per-question answer review with linked lesson notes. The global app shell was not edited.
- Learner quiz submissions now return review details (selected and correct options, correctness, and lesson notes) without changing the persisted attempt JSON schema. Existing prerequisite and unlock checks remain in force.
- Read-only database audit: 10 Beginner quizzes and 48 questions exist across the current public language groups; pass threshold is 70%; section_quiz_attempts remains at 0. No quiz submissions or learner rows were created or changed.
- Verification completed: npm --prefix frontend run build passed; npm --prefix frontend run lint exited 0 with pre-existing warnings in unchanged App.jsx; Python compilation passed for app/quiz_api.py and main.py; FastAPI OpenAPI generation includes the learner and admin quiz routes. No automated backend unit/integration test suite was present, so the interactive MySQL password diagnostic was not run.
- Built and validated backend/scratch/StrokeSpeak-submission-v10-2026-11-22.zip (1,105 entries; 17,592,046 bytes). ZIP CRC and content checks passed; no local environment, learner upload/recording, scratch staging, or backup artifacts were packaged.
- The admin preview still requires the owner to add their own account ID to STROKESPEAK_ADMIN_USER_IDS and restart the backend. Do not infer an account ID or promote a learner account without the owner’s verified ID.
- Remaining evidence is real learner validation: complete a quiz and confirm progression using an actual account; handwriting and microphone matrices still need genuine samples. These are validation tasks, not claims of completed AI accuracy.


## 80. Final Integration Regression and Video Handoff (2026-11-22)

- Quiz progression regression passed 39/39 checks using a uniquely registered temporary learner and real MySQL/API calls. It covered unauthorized and premature access, Foundation and section completion, failed retry without unlock, exact score calculation, pass unlock, later-section lesson gate, attempt history, account scope, admin authorization, and read-only admin preview. The temporary account, two quiz-attempt rows, and 117 lesson-progress rows created by that scenario were deleted; no existing learner progress was touched.
- Authentication/drawing/speech API smoke passed 16/16 checks using another temporary account. Registration/login, signed profile, reference retrieval, geometric/stroke-order feedback, typed transcript assessment, malformed-audio rejection, no-audio transcription guard, and history passed. The drawing was the stored reference trace used only as a synthetic software fixture; it is not human handwriting evidence. No microphone/audio was uploaded. The temporary attempt/account were deleted.
- Public scope resolved to four selector entries: Japanese (with both Hiragana and Katakana in the same tutor), Sanskrit, Tamil, and Simplified Chinese. Lesson counts were Japanese 128, Sanskrit 29, Tamil 32, Chinese 14. One labeled dataset image per trained CNN returned the expected class in each of four models; this is a four-sample smoke check, not a 41-class accuracy or learner benchmark. Katakana remains untrained.
- Video integration initially found four stale published URLs returning HTTP 404. Updated only the tutorial_video_url fields for lessons 339, 55, 223, and 348 to the current lesson-ID route, using an isolated temporary admin account. All five current video mappings (including Japanese lesson 61) now return HTTP 200 video/mp4. PyAV confirmed 1280x720, 30 FPS, H.264/AAC and decodable duration for each available file. The Japanese mapping and every video file were left untouched.
- Updated backend/scripts/update_video_urls.py to use the working lesson-ID routes. Original copy is backend/scripts/update_video_urls.py.bak-2026-11-22-video-route-integration. No Antigravity-owned video generator or media file was edited.
- Frontend production build passed. Lint exited 0 with existing warnings in App.jsx. Python syntax checks passed for main.py, app/quiz_api.py, and the URL updater; FastAPI exposes 29 OpenAPI paths; the stroke helper smoke script passed.
- Read-only snapshot after cleanup: users 4, lesson_progress 17, practice_attempts 132, section_quiz_attempts 0. The four URL fields are the only persistent database fields changed in this integration.
- Reviewed Antigravity’s FINAL_STROKESPEAK_VALIDATION_REPORT.md as an external handoff. Its four video URLs were stale and its acoustic-scoring claim does not match current code, which explicitly says pronunciation scoring is normalized transcript similarity, not acoustic analysis. Its claim of 41 passing CNN classes is not established by this regression; only one labeled image per trained script was checked. Its Google-login and forgot-password claims are not present in App.jsx. Do not use its READY status as final project sign-off without reconciling these discrepancies.
- Safety issue to return to Antigravity: backend/scripts/generate_multilingual_videos.py calls a generator that opens fixed output filenames and uses shutil.copyfile for Tamil lesson 223 without checking for existing files. Do not rerun it; it could overwrite the current videos. No Antigravity-owned files were changed.
- Final submission ZIP was not built. v10 remains a checkpoint until the generator is made non-overwriting and qualified linguistic/reference review, genuine handwriting evidence (currently 1/41), and genuine microphone validation (0/4) are reconciled. Browser-level visual learner walkthrough also remains human-facing; API progression was exercised end-to-end on the isolated account.
