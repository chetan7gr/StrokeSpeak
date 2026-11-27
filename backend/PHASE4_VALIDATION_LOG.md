# StrokeSpeak Phase 4 Validation Log

Last updated: 2026-11-20

This log tracks real learner validation. Only results retrieved from MySQL after a genuine learner action belong here. Synthetic model samples and renderer checks must remain labeled separately.

## Handwriting matrix: 1 / 41 complete

| Group | Target | Status / evidence |
|---|---|---|
| Japanese Hiragana | あ | Complete · Attempt 218 · geometry 84.02 · stroke order 83.81 · CNN predicted お at 99.6% · 3/3 strokes · pronunciation pending |
| Japanese Hiragana | い, う, え, お, か, き, く, け, こ | Pending genuine learner drawings |
| Sanskrit (Devanagari) | अ, आ, इ, ई, उ, ऊ, ए, ऐ, ओ, औ | Pending genuine learner drawings |
| Tamil | அ, ஆ, இ, ஈ, உ, ஊ, எ, ஏ, ஐ, ஒ, ஓ, ஔ | Pending genuine learner drawings |
| Simplified Chinese | 一, 二, 三, 人, 大, 口, 日, 月, 山 | Pending genuine learner drawings |

**Preserve Attempt 218.** Its CNN mismatch is a regression case. The original raster was not stored in MySQL, so a reconstructed image must never be described as the exact model input.

## Speech matrix: 0 / 4 script groups complete

| Public group | Target audio | Result |
|---|---|---|
| Japanese (Hiragana / Katakana) | Real browser microphone recording | Pending |
| Sanskrit (Devanagari) | Real browser microphone recording | Pending |
| Tamil | Real browser microphone recording | Pending |
| Simplified Chinese | Real browser microphone recording | Pending |

Use local Faster-Whisper. Record only actual attempt IDs, transcripts, scores, and errors. PyAV/Faster-Whisper imports and WebM/Opus decoder availability were checked; no real recording has yet been assessed.

## Other end-to-end checks

- Core API, MySQL health, public language filtering, lesson and quiz GET routes: checked.
- Four CNN models on supplied sample images: checked; those results are not learner validation.
- Frontend production build: passed.
- Beginner quiz content: 10 sections / 48 questions. Learner quiz submission and progression unlock: pending.
- Tutorial videos: Japanese Hiragana `あ` demo is ready in a female-teacher version; the original MP4 is preserved. Sanskrit/Tamil/Simplified Chinese demos await real validation of their target references. New video generator is guarded and will not overwrite existing media.

## Next learner action

The app is prepared for learner 2 at `http://127.0.0.1:5173/?learner_id=2`, with Hiragana `い` selected and an empty canvas. Draw `い`, save once, then record speech on that new attempt and run local assessment. Update this log only from the returned database result.
## 43. Realistic Female Tutor Portrait Version (2026-11-20)

- Added an original transparent photorealistic female teacher portrait and composited it beside the animated board in the video renderer. The procedural female illustration remains a fallback.
- Generated a separate Japanese Hiragana `あ` tutorial version (`ja_hiragana_2_lesson61_realistic-v3.mp4`); previous videos were preserved. The clip decodes as H.264 + AAC, about 32 seconds / 964 frames. Narration is still the existing generated audio; the portrait itself is not live-action or lip-synced.
- Lesson 61's metadata now points to `/api/v1/lessons/61/video?variant=realistic-v3`, status `ready`. The API GET route is the final delivery check.
- Rendering and registration are media checks only; they do not add learner drawing, speech, or quiz validation evidence.


## 44. Female Narration and Audio-Synchronized Mouth (2026-11-20)

- The latest Japanese Hiragana `あ` tutorial uses local Microsoft Zira Desktop female narration. No paid speech API was used; gTTS remains a fallback in the generator.
- Portrait mouth opening is driven by the generated narration's PCM amplitude at each video timestamp, so it follows speech and pauses. This is waveform-level synchronization, not phoneme-viseme accuracy or a live-action talking head.
- `ja_hiragana_2_lesson61_female-lipsync-v4.mp4` decoded successfully (H.264/AAC, 30.27 seconds, 908 frames). Its API route returned HTTP 200 and `video/mp4`; lesson 61 metadata is `ready` and points to `?variant=female-lipsync-v4`.
- This is renderer/media validation only; learner handwriting, speech assessment, and quiz validation counts are unchanged.


## 45. Multi-Script Tutor Voice and Windows Console Fix (2026-11-20)

- Multi-script demo code now shares the local female Windows English narration and waveform-timed mouth opening. Script-specific target pronunciation remains on its configured gTTS language voice; Sanskrit currently uses Hindi voice as an explicitly approximate synthetic pronunciation.
- The demo generator's read-only candidate inventory now prints Unicode code points, so Windows PowerShell's legacy console encoding no longer crashes on Devanagari/Tamil/Chinese characters. Compilation and dry run passed; it reports the three references (lessons 339, 223, 348).
- Dry run generated no media and wrote no database rows. Remaining demo rendering is gated on genuine learner drawing validation; this count was not fabricated.


## 46. Tamil Lesson Sequence Repair (2026-11-20)

- Fixed five known Tamil ordering anomalies with an idempotent transactional migration and no learner progress on affected lesson IDs: foundation vowel contrast now follows the consonant lesson list; a polite phrase now follows the four beginner words in Beginner Unit 1 (the unit has five quiz questions); the Tamil greeting follows its four character-form lessons; elementary and advanced each start at Unit 1 / Lesson 1.
- Read-only live API check confirmed the corrected levels, units, and order values. No learner attempts, scores, quiz submissions, or hidden-language rows changed.

## 47. Stroke Reference Provenance Disclosure (2026-11-20)

- 32 Sanskrit/Tamil/Simplified Chinese stroke reference records now carry explicit unverified provenance; the previous unsupported source/license labels are retained as historical metadata. Stroke vectors and learner data were untouched.
- Generator dry run holds all three multi-script demo candidates pending verified references and genuine learner validation.
- Frontend displays a draft warning when the API marks a reference `provenance_status: unverified`.
- Japanese Kana source attribution remains unchanged. Hidden legacy script rows remain excluded.

## 48. Script-Specific Speech Language Codes (2026-11-20)

- Installed Faster-Whisper tokenizer confirms support for `sa`; Sanskrit audio transcription now uses that code instead of Hindi. Recognition quality still needs validation with actual Sanskrit learner samples.
- Japanese Katakana lesson reference audio now resolves to the Japanese voice map.
- Installed gTTS has no Sanskrit language entry, so the Sanskrit reference voice remains an approximate Hindi/Indic synthetic fallback and is labeled as approximate in the UI. No learner attempts or scores were changed.

## 49. Honest Speech Score Messaging (2026-11-20)

- Learner feedback now labels the Whisper-derived value “Transcript similarity” and states that it is text comparison, not phoneme-level articulation analysis. This reflects the implemented scoring method.
- Frontend production build passed with the new message and draft-reference warning.

## 50. Consolidated Completion Checkpoint (2026-11-20)

- Learner evidence counts are unchanged: 1/41 handwriting targets, 0/4 real speech groups, 0 real quiz submissions/unlocks, and 1/4 ready script-group videos.
- Sanskrit now uses Whisper's Sanskrit tokenizer code; Katakana reference pronunciation uses Japanese TTS. Sanskrit TTS remains an explicitly approximate Indic voice.
- Interface now distinguishes transcript similarity from phoneme-level pronunciation assessment and marks unverified stroke guides as drafts.
- No learner attempts, scores, recordings, quiz submissions, or progress were fabricated. Remaining learner actions are genuine and cannot be completed by code generation.

## 51. Combined Japanese Tutor and Current-State Documentation (2026-11-20)

- Lesson 315 is now in the main Japanese tutor (Foundation / Katakana vowel unit / order 6). The live API returns 128 Japanese lessons; its prior learner progress (`in_progress`, score 80 for learner 1) was preserved.
- Confirmed the 10 quizzes/48 questions cover every Beginner unit across Japanese, Sanskrit, Tamil, and Simplified Chinese. No learner quiz submission or unlock has been fabricated.
- Current DB counts: 3 users, 12 languages, 250 characters, 391 lessons, 17 progress rows, and 132 practice attempts (805 total). Public lesson rows: 200; hidden legacy rows: 191.
- Added `docs/CURRENT_PROJECT_STATUS.md` and reconciled stale run/demo/report/API/test documentation with current behavior and limitations.
