# StrokeSpeak Current Project Status

**Read-only database counts, public language response, and quiz/video regression checks were rechecked on 2026-11-22 against local MySQL and the FastAPI code.** The current source of truth is this file; older report, checklist, and demo documents may retain historical descriptions and should be reconciled before submission.

## Product scope

The public tutor has exactly four language groups:

- Sanskrit (Devanagari)
- Japanese (Hiragana and Katakana in one tutor)
- Tamil
- Simplified Chinese

Hindi, Telugu, Malayalam, Kannada, Korean, and Arabic are not exposed. Their legacy database rows remain hidden.

## Live database snapshot

The read-only table-count utility reported **809 total rows** across the six core tables:

| Table | Rows |
| --- | ---: |
| users | 4 |
| languages | 12 |
| characters | 250 |
| learning_lessons | 394 |
| lesson_progress | 17 |
| practice_attempts | 132 |

The separate quiz tables contain **10 section quizzes**, **48 questions**, and **0 learner quiz submissions**.

There are **203 lessons tagged to public language script rows** (191 legacy lessons are hidden). The learner-facing counts are:

| Tutor group | Current lessons | Levels present |
| --- | ---: | --- |
| Japanese (combined Hiragana + Katakana) | 128 | Foundation 100, Beginner 25, Elementary 2, Advanced 1 |
| Sanskrit | 29 | Foundation 19, Beginner 10 |
| Tamil | 32 | Foundation 24, Beginner 6, Elementary 1, Advanced 1 |
| Simplified Chinese | 14 | Foundation 9, Beginner 5 |

The standalone Katakana vowel summary (lesson 315) is now included in Japanese Foundation, Katakana unit, order 6. Its existing learner progress row was preserved. The Japanese tutor therefore includes all 92 Kana and 128 lessons in one language selection.

Four user rows currently exist; two legacy placeholder-hash accounts cannot authenticate. Individual histories are account-bound, and the frontend does not let a visitor select another learner by ID. Register a real account for a clean profile.

## Implemented and checked

- Retired three legacy generated-reference writers that used unverified geometry and unsupported source/license labels. Their replacements perform no database writes; existing paths remain unchanged.
- Retired three legacy scoring/audit scripts that submitted generated reference traces as learner attempts and deleted them after checking. They now perform no network or database actions; genuine validation requires learner drawings.
- FastAPI/Uvicorn API and MySQL connectivity; the live health route reports `database: connected`. The current OpenAPI schema contains 29 paths, including administrator-only geometry review and quiz preview/non-persistent grading endpoints. Quiz preview does not create learner attempts or unlock learner progress.
- Signed learner account flow in React: registration/login, session restore, sign out, 8-hour HMAC Bearer tokens, learner-owned practice/progress/quiz routes, and admin-only shared curriculum writes. Backend imports/OpenAPI generation and the Vite production build succeeded after these changes. The local user still needs to restart both servers and sign in once to verify the live account flow.
- React/Vite/Tailwind learner app; the production build passed after the latest UI changes.
- Japanese Hiragana and Katakana character practice in one tutor, with 92 KanjiVG-attributed Kana stroke guides.
- Sanskrit, Tamil, and Simplified Chinese lesson/character data, canvas drawing, attempt persistence, and geometric reference comparison where paths are available. The geometric prototype now arc-length-resamples paths, applies a gradual local direction penalty, and ignores unmatched stationary taps during scoring; raw learner stroke data remains stored as drawn, and saved historical scores were not recalculated. Ten Simplified Chinese starter references now use pinned hanzi-writer-data 2.0.1 median paths under the Arphic Public License; the complete license and source JSON files are vendored with attribution and a rollback backup. Six exact standalone Sanskrit vowels (अ, इ, उ, ऊ, ऋ, ए) now use hand-drawn Devanagari paths from the pinned Lipi model under CC BY 4.0; its model card and license are vendored with a rollback backup. Both sources are attributed, but qualified instructional review remains pending.
- Four trained TorchScript CNN models cover 41 classes: Japanese Hiragana 10, Sanskrit 10, Tamil 12, and Simplified Chinese 9. Japanese Katakana is public and has geometric practice feedback. Its CNN remains explicitly untrained because no ETL6 dataset is installed; a guarded 46-class intake and writer-disjoint training pipeline is ready for a user-acquired, terms-accepted dataset. Model inference and sample-image checks do not establish real-world handwriting accuracy; dataset provenance varies and some training data is synthetic.
- Browser recording, audio persistence, local Faster-Whisper transcription and normalized transcript similarity. Sanskrit uses Whisper's `sa` code; the installed gTTS package has no Sanskrit voice, so Sanskrit reference playback remains an explicitly labeled Hindi/Indic approximation.
- Ten section quizzes with 48 questions. Read-only API audit confirmed that every Beginner unit in all four tutor groups has a corresponding quiz. Course access now follows ordered modules and levels: Foundation units unlock after the prior unit; Beginner starts after Foundation and each later Beginner unit needs the previous unit quiz; Elementary follows all Beginner sections and unlocks its units in order; Intermediate follows all Elementary lessons; Advanced follows all Intermediate lessons. Missing prerequisite levels stay locked. Configured administrators also have read-only quiz preview and non-persistent preview grading; learner attempts still require prerequisites and are the only actions that affect learner progress. The React quiz panel supports numbered question navigation, revising answers before submission, per-question correctness with lesson-linked notes, retries, and recent attempt history.
- Five original Sensei Kai lesson files (Japanese 61, Sanskrit 339, Tamil 55 and 223, Simplified Chinese 348) were audited and decode. The audit found 1–21 ms audio/video duration differences; this is not phoneme-accurate lip sync. English captions are burned in. The original Japanese v5 voice is reported as Zira Desktop. The user then requested that the tutor stop moving. All five public lesson URLs now point to new teacher-static-v2 renders: Japanese 61, Sanskrit 339, Tamil 55 and 223, and Simplified Chinese 348. Previous moving, closed-mouth v1, and original videos remain available as rollback files. See FINAL_VALIDATION_WORKSHEET.md for per-video findings.
- The renderer now holds the female tutor's position, scale, tilt, and body still while preserving the narration-driven closed, parted, and open mouth poses; lesson-board and stroke animations continue. Five new teacher-static-v2 files were generated, and only the five public lesson URLs were changed. Existing MP4s remain preserved. All five learner routes returned HTTP 200/video/mp4, all audio/video streams decoded, and frame comparisons confirm the body stays fixed while the mouth changes during narration. Narration remains English Microsoft Zira Desktop.
- Seventeen Sanskrit/Tamil references remain unverified and not authorized for redistribution (five Sanskrit and twelve Tamil); their earlier unsupported labels remain historical metadata. Six Sanskrit references and ten Chinese references now have pinned, attributed sources, but neither set has passed qualified instructional review.

## Work that still needs learner or domain evidence

- Formal target-character handwriting validation matrix: **1/41** verified target cases; the remaining cases need genuine drawings. The existing exploratory human-mouse sample is small and is not an accuracy benchmark.
- End-to-end real microphone validation: **0/4** tutor groups. A metadata-only check found one Sanskrit `audio/mpeg` record with a completed transcript and score, but its origin is not independently verified, so it is not counted. Genuine learner recordings must be saved and assessed for Japanese, Sanskrit, Tamil, and Chinese; never count typed text or synthetic audio as microphone validation.
- Quiz progression: disposable-account API regression passed for locked access, lesson prerequisites, failed retry, passing score, next-section unlock, history, authorization, and non-persistent admin preview. All temporary rows and accounts were removed; there are still **0** retained learner quiz attempts.
- Tutorial video release: candidate files and database links are technically available for all four groups, but only the existing Japanese tutorial has prior release approval. Sanskrit, Tamil, and Chinese candidates still need qualified reference/language review and genuine learner drawing validation. The bulk generator now refuses existing outputs unless --overwrite is explicitly supplied, stages and validates outputs before atomic publishing, and has 8/8 overwrite-safety tests passing. No video was generated or replaced in this work. The bulk generator still bypasses the per-reference approval workflow, so it remains on hold for instructional release.
- Curriculum depth: the four groups have uneven levels; Sanskrit and Chinese currently stop after Beginner. Additional lessons require careful linguistic review and trustworthy source material.
- Account security and reference review: registration/login use signed, 8-hour HMAC Bearer tokens; attempts, recordings, lesson progress, and quizzes are bound to the authenticated account. Shared writes require an ID in `STROKESPEAK_ADMIN_USER_IDS` (empty by default). The instructor panel records reviewer-supplied qualification, standard/convention, decision, UTC time, and a SHA-256 fingerprint of the exact paths. Approvals are a human attestation, not independently verified credentials; the guarded per-lesson video path requires a current approved fingerprint and an administrator token. The shared bulk video script bypasses that review path. The overwrite guard is now implemented and tested; reference authorization still needs to be enforced in the release workflow. It remains on hold for release until source/reference review is complete. Canvas edits to source-attributed paths are blocked; changed drafts are backed up and marked unverified. HTTPS, token refresh/revocation, and live sign-in validation remain before production use.

## Safe local run

Start MySQL service `MySQL80`, then open two PowerShell terminals:

```powershell
Set-Location "C:\Users\CHETAN\.vscode\StrokeSpeak\backend"
& .\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

```powershell
Set-Location "C:\Users\CHETAN\.vscode\StrokeSpeak\frontend"
npm run dev
```

Open `http://localhost:5173/`, create an account or sign in, and use that account for the session. API docs are at `http://127.0.0.1:8000/docs`. Register a new account when you need a clean profile.

## Important score wording

Handwriting and stroke-order values are geometric prototype estimates. The speech value is **transcript similarity**, not acoustic/phoneme-level pronunciation analysis. CNN sample checks are not a validated accuracy claim. Keep these distinctions in project reports and demonstrations.


## Chinese stroke-reference source checkpoint (2026-11-20)

The ten Simplified Chinese starter glyphs (一, 二, 三, 人, 大, 小, 口, 日, 月, 山) now use ordered median paths from `hanzi-writer-data` 2.0.1, derived from Make Me a Hanzi and licensed under the Arphic Public License. The package JSON files and full license are kept in `backend/data/reference_strokes/hanzi-writer-data-2.0.1/`. The migration script records per-file SHA-256 hashes and the normalization/timing transformation. A pre-import MySQL backup is at `backend/data/reference_strokes/backups/before_hanzi_writer_data_2.0.1.json`. Database provenance is `source_attributed`; instructional review remains `pending`. No learner attempts, drawings, scores, recordings, or progress were created.


## Devanagari source checkpoint (updated 2026-11-21)

Six exact standalone vowels (अ, इ, उ, ऊ, ऋ, ए) now use ordered hand-drawn Devanagari centerline points embedded in Lipi's pinned `weights.safetensors` model (revision `c547139c82130da50827a1f2bffb995254395600`). These six paths remain pending qualified Sanskrit instructor review. Character ID 222 (ऋ, U+090B) has a three-stroke extracted path added on 2026-11-21; a row-only pre-import backup is `backend/data/reference_strokes/backups/before_lipi_rishi_extension_2026-11-21.json`. A read-only check confirmed zero attempts for character 222 and no learner data changes. The Sanskrit Foundation unit now teaches the complete 14-vowel inventory in order; lessons 392–394 add ॠ, ऌ, ॡ between ऋ and ए. Their spelling/transliteration follows the Library of Congress romanization table, but they still lack reviewed stroke vectors and pronunciation audio remains approximate. The model card, weights artifact, and license text are vendored under `backend/data/reference_strokes/lipi-devanagari-c547139c82130da50827a1f2bffb995254395600/`; the importer is `backend/scripts/import_lipi_devanagari_reference_strokes.py`. The standalone forms आ, ई, ऐ, ओ, औ remain on their previous unverified stroke references. Rollback backups are in `backend/data/reference_strokes/backups/` and `backend/data/backups/`.

## Final integration validation checkpoint (2026-11-22)

- Previously recorded regressions: quiz progression 39/39 and authentication/drawing/speech API 16/16. Current checks on 2026-11-22: video overwrite safety 8/8; CNN registry loaded all four groups and 7/7 sample-image inference calls matched their expected labels; all five lesson-ID video endpoints returned HTTP 200 with video/mp4; after remapping, all five updated lesson endpoints returned the teacher-static-v2 filenames. The former v4 URL still resolves to v5 as a backward-compatible route; all five mapped videos decode; Vite production build passed to a temporary output directory. Backend syntax was verified without writing bytecode. These are software/sample checks, not genuine learner evidence.
- Formal target-character handwriting validation remains 1/41; the attempt/character identity for the single counted case must be traced before it can be marked in the worksheet. Genuine microphone validation remains 0/4.
- A dedicated browser learner walkthrough was not completed: browser-control safety stopped the isolated attempt before it reached the app. No account or learner data changed.
- Antigravity video/reference integration status is not confirmed in the local handoff available at this checkpoint. No Antigravity-owned files were edited. Final ZIP is not ready; see FINAL_VALIDATION_WORKSHEET.md.
