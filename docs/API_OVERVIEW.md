# StrokeSpeak API Overview

> **Current-state note (2026-11-22):** The OpenAPI schema contains 29 paths. Registration and login now return signed 8-hour Bearer tokens; learner-specific attempt, recording, lesson-progress, and quiz routes enforce token ownership. Quiz submission returns a score and per-question correctness/teaching notes after completion. Shared curriculum writes, quiz answer-key preview, and non-persistent quiz grading require an ID in `STROKESPEAK_ADMIN_USER_IDS`. Quiz preview is documented in [QUIZ_AUTHOR_PREVIEW.md](QUIZ_AUTHOR_PREVIEW.md) and does not save learner attempts. Consult [CURRENT_PROJECT_STATUS.md](CURRENT_PROJECT_STATUS.md) for current counts and evidence limits. This remains a local project implementation; use HTTPS and a production token/session design before deployment.

This document specifies every public endpoint available in the live StrokeSpeak FastAPI backend (`v0.1.0`), derived from `/openapi.json` and verified with live calls. All secrets and credentials are removed.

> [!NOTE]
> **Proxy & CORS Architecture**: When running locally, the frontend is started with `npm run dev`, which proxies `/api` calls directly to `127.0.0.1:8000`. The built `frontend/dist` folder does not work without a proxy server, and the backend has no CORS middleware by design in this version.

> [!WARNING]
> **Swagger UI (/docs) Safety Rule**: In Swagger (/docs) press Execute only on GET routes. Never press Execute on transcribe, pronunciation-audio or pronunciation-assessment, or on any POST/PUT/DELETE route; they can create rows or call an external service.

---

## 1. System & Health

### `GET /`
- **Purpose**: Root health ping confirming the backend is reachable.
- **Request**: `GET http://127.0.0.1:8000/`
- **Response**:
```json
{
  "project": "StrokeSpeak",
  "message": "Backend is running!"
}
```

### `GET /api/v1/health`
- **Purpose**: System health and database connectivity probe.
- **Request**: `GET http://127.0.0.1:8000/api/v1/health`
- **Response**:
```json
{
  "status": "healthy",
  "service": "StrokeSpeak API",
  "database": "connected"
}
```

---

## 2. Authentication

### `POST /api/v1/auth/register`
- **Purpose**: Registers a new learner account.
- **Request**: `POST http://127.0.0.1:8000/api/v1/auth/register`
```json
{
  "name": "Jane Learner",
  "email": "jane@example.com",
  "password": "Password123!"
}
```
- **Response**:
```json
{
  "message": "Account created successfully.",
  "user": {
    "id": 4,
    "name": "Jane Learner",
    "email": "jane@example.com",
    "role": "learner"
  },
  "token": "<signed access token>"
}
```

### `POST /api/v1/auth/login`
- **Purpose**: Authenticates a user with email and password, returning user profile and session token.
- **Request**: `POST http://127.0.0.1:8000/api/v1/auth/login`
```json
{
  "email": "your-account@example.com",
  "password": "your-password"
}
```
- **Response (200 OK)**:
```json
{
  "message": "Login successful.",
  "user": {
    "id": 4,
    "name": "Jane Learner",
    "email": "jane@example.com",
    "role": "learner"
  },
  "token": "<signed access token>"
}
```
- **Error (401 Unauthorized)**:
```json
{
  "detail": "Invalid email or password."
}
```

### `GET /api/v1/auth/me`
- **Purpose**: Returns the account encoded in the verified Bearer token. The client cannot choose an account ID.
- **Request**: `GET http://127.0.0.1:8000/api/v1/auth/me` with `Authorization: Bearer <signed access token>`.
- **Response (200 OK)**:
```json
{
  "user": {
    "id": 2,
    "name": "Demo Learner",
    "email": "jane@example.com",
    "role": "learner",
    "created_at": "2026-11-17 00:00:00"
  }
}
```

---

### Learner and administrator access
The frontend signs in or creates an account, stores the returned token in browser local storage, and attaches it as `Authorization: Bearer <token>`. Tokens expire after eight hours; sign in again after expiry. Learner attempt, audio, progress and quiz endpoints derive ownership from the token. Do not send another learner's ID. Shared curriculum writes and reference reviews require an account ID intentionally listed in `STROKESPEAK_ADMIN_USER_IDS`; this setting is empty by default. New registrations receive the `learner` role by default. Keep both `.env` and access tokens private.

## 3. Languages

### `GET /api/v1/languages`
- **Purpose**: Lists public supported language groups (Sanskrit, Japanese, Tamil, Simplified Chinese).
- **Request**: `GET http://127.0.0.1:8000/api/v1/languages`
- **Response**:
```json
{
  "languages": [
    {
      "id": 5,
      "name": "Japanese",
      "script_code": "ja-hiragana",
      "character_language_ids": [5, 57]
    },
    {
      "id": 56,
      "name": "Sanskrit (Devanagari)",
      "script_code": "sa-devanagari"
    },
    {
      "id": 58,
      "name": "Simplified Chinese",
      "script_code": "zh-hans"
    },
    {
      "id": 19,
      "name": "Tamil",
      "script_code": "ta"
    }
  ]
}
```

### `GET /api/v1/languages/{language_id}`
- **Purpose**: Fetches details for a specific supported language.
- **Request**: `GET http://127.0.0.1:8000/api/v1/languages/5`
- **Response**:
```json
{
  "language": {
    "id": 5,
    "name": "Japanese",
    "script_code": "ja-hiragana"
  }
}
```

### `POST /api/v1/languages`
- **Purpose**: Adds a new supported language or script group.
- **Request**:
```json
{
  "name": "Japanese Katakana",
  "script_code": "ja-katakana"
}
```
- **Response**:
```json
{
  "message": "Language added successfully.",
  "language_id": 57
}
```

### `PUT /api/v1/languages/{language_id}`
- **Purpose**: Updates an existing language name or script code.
- **Request**:
```json
{
  "name": "Sanskrit (Devanagari)",
  "script_code": "sa-devanagari"
}
```
- **Response**:
```json
{
  "message": "Language updated successfully."
}
```

---

## 4. Characters & Reference Strokes

### `GET /api/v1/characters?language_id={language_id}`
- **Purpose**: Lists learning characters for a given language.
- **Request**: `GET http://127.0.0.1:8000/api/v1/characters?language_id=5`
- **Response**:
```json
{
  "characters": [
    {
      "id": 2,
      "language_id": 5,
      "language_name": "Japanese",
      "character_text": "あ",
      "meaning": "Japanese Hiragana character",
      "pronunciation_text": "a",
      "has_reference": 1
    }
  ]
}
```

### `GET /api/v1/characters/{character_id}`
- **Purpose**: Retrieves a single character's details.
- **Request**: `GET http://127.0.0.1:8000/api/v1/characters/2`
- **Response**:
```json
{
  "character": {
    "id": 2,
    "language_id": 5,
    "language_name": "Japanese",
    "character_text": "あ",
    "meaning": "Japanese Hiragana character",
    "pronunciation_text": "a",
    "has_reference": 1
  }
}
```

### `GET /api/v1/characters/{character_id}/reference-strokes`
- **Purpose**: Returns the saved normalized point sequence and SVG paths for stroke order replay.
- **Request**: `GET http://127.0.0.1:8000/api/v1/characters/194/reference-strokes`
- **Response**:
```json
{
  "character_id": 194,
  "reference_available": true,
  "stroke_count": 1,
  "reference_source": {
    "source": "KanjiVG",
    "license": "CC BY-SA 3.0",
    "strokes": [
      {
        "path_id": "kvg:030ce-s1",
        "d": "M66.39,23.17c0.23,0.66,0.22,1.3-0.08,1.96c-4.49,9.81-18.06,34.12-39.7,56.87"
      }
    ]
  },
  "stroke_data": [
    [
      { "x": 0.663945, "y": 0.231651, "time": 0 },
      { "x": 0.266055, "y": 0.820000, "time": 160 }
    ]
  ]
}
```

### `PUT /api/v1/characters/{character_id}/reference-strokes`
- **Purpose**: Saves an administrator-drawn reference. A changed source-attributed path is blocked; a changed draft is backed up, cleared of the old SVG paths/source attribution, and marked unverified with review pending.
- **Request**: `PUT http://127.0.0.1:8000/api/v1/characters/2/reference-strokes`
```json
{
  "stroke_data": [
    [{ "x": 0.28, "y": 0.30, "time": 0 }, { "x": 0.72, "y": 0.30, "time": 100 }]
  ]
}
```
- **Response**:
```json
{
  "message": "Reference drawing saved.",
  "character_id": 25,
  "stroke_count": 1,
  "provenance_status": "unverified",
  "instructional_review_status": "pending",
  "review_invalidated": true,
  "rollback_backup": "before_admin_reference_edit_char25_20261121T000000Z_example.json"
}
```

### `POST /api/v1/characters/{character_id}/reference-review`
- **Access**: Configured administrator Bearer token.
- **Purpose**: Record a reviewer-attested decision against the exact current point and SVG geometry. Approval is accepted only when the character has an attributed source URL and reuse license metadata.
- **Request**:
```json
{
  "reviewer_name": "Reviewer Name",
  "reviewer_qualification": "Qualified Sanskrit instructor",
  "reference_standard": "Named source, edition, page, or URL",
  "writing_convention": "Named regional or instructional convention",
  "decision": "approve",
  "notes": "Checked stroke count, order, direction, and form.",
  "attests_exact_reference": true
}
```
- `decision` is `approve`, `revise`, or `hold`. Approval requires `attests_exact_reference: true`. Reviewer qualification is self-reported and must be independently trusted by the project owner. The API stores the decision, UTC timestamp, and SHA-256 fingerprint in reference metadata. A changed path invalidates the fingerprint and blocks tutorial-video release.
- **Response**:
```json
{
  "message": "Reference review recorded.",
  "character_id": 241,
  "decision": "approve",
  "instructional_review_status": "approved",
  "reviewed_reference_sha256": "<current geometry fingerprint>",
  "reviewed_at_utc": "<server UTC timestamp>"
}
```

---

## 5. Lessons & Progress

### `GET /api/v1/lessons?language_id={language_id}&level={level}`
- **Purpose**: Retrieves curriculum lessons ordered by unit and lesson order.
- **Request**: `GET http://127.0.0.1:8000/api/v1/lessons?language_id=5`
- **Response**:
```json
{
  "lessons": [
    {
      "id": 316,
      "language_id": 5,
      "language_name": "Japanese",
      "category": "word",
      "level": "beginner",
      "unit_number": 1,
      "lesson_order": 1,
      "title": "Word: Thank you",
      "content_text": "ありがとう",
      "translation_text": "Thank you",
      "pronunciation_text": "arigatou",
      "explanation": "Everyday polite expression used when thanking someone."
    }
  ]
}
```

### `GET /api/v1/lessons/{lesson_id}/reference-audio`
- **Purpose**: Streams reference audio (MP3) generated from the lesson text via gTTS.
- **Request**: `GET http://127.0.0.1:8000/api/v1/lessons/316/reference-audio`
- **Response**: HTTP 200 with `Content-Type: audio/mpeg` binary audio stream.

### `PUT /api/v1/lessons/{lesson_id}/progress`
- **Purpose**: Updates or creates a learner's progress status (`completed` or `in_progress`) and score.
- **Request**: `PUT http://127.0.0.1:8000/api/v1/lessons/316/progress`
```json
{
  "user_id": 1,
  "status": "completed",
  "score": 95.0
}
```
- **Response**:
```json
{
  "message": "Lesson progress saved."
}
```

### `GET /api/v1/lesson-progress?user_id={user_id}`
- **Purpose**: Retrieves all lesson progress rows for a specific learner.
- **Request**: `GET http://127.0.0.1:8000/api/v1/lesson-progress?user_id=1`
- **Response**:
```json
{
  "progress": [
    {
      "lesson_id": 316,
      "status": "completed",
      "score": 95.0,
      "completed_at": "2026-11-17T05:41:54",
      "updated_at": "2026-11-17T05:41:54",
      "language_id": 5,
      "language_name": "Japanese",
      "title": "Word: Thank you",
      "level": "beginner",
      "unit_number": 1,
      "category": "word"
    }
  ]
}
```

### `PUT /api/v1/lessons/{lesson_id}/tutorial-video`
- **Purpose**: Sets tutorial video status (`ready`, `processing`, `failed`) and URL.
- **Request**:
```json
{
  "status": "ready",
  "video_url": "https://example.com/videos/lesson_316.mp4"
}
```
- **Response**:
```json
{
  "message": "Tutorial video updated successfully."
}
```

---

## 6. Practice Attempts & Scoring

> [!NOTE]
> **Synthetic Trace Disclosure**: All automated scoring responses illustrated below (e.g., Attempt 71 scoring 100.0%) reflect **synthetic coordinate traces** generated directly from reference stroke vectors. Real human hand drawings will exhibit natural velocity changes, hook artifacts, and local tremors, and may score differently. Live human handwriting tests are marked `[UNVERIFIED]`.
> The drawing score is geometric prototype comparison, not trained-AI handwriting scoring. Four trained CNN models cover 41 classes (10 Hiragana, 10 Sanskrit, 12 Tamil, 9 Simplified Chinese); Katakana is registered as untrained. Local Faster-Whisper routes exist, but sample checks do not establish generalization or acoustic pronunciation accuracy.

### `POST /api/v1/practice-attempts`
- **Purpose**: Submits learner drawing coordinates. Evaluates shape similarity via bounding-box normalized Euclidean distance and stroke order with start-to-end vector cosine direction checks.
- **Request**: `POST http://127.0.0.1:8000/api/v1/practice-attempts`
```json
{
  "user_id": 1,
  "character_id": 194,
  "stroke_data": [
    [
      { "x": 0.66, "y": 0.23, "time": 0 },
      { "x": 0.27, "y": 0.82, "time": 160 }
    ]
  ]
}
```
- **Response**:
```json
{
  "message": "Practice drawing saved.",
  "attempt_id": 71,
  "user_id": 1,
  "character_id": 194,
  "stroke_count": 1,
  "scores": {
    "handwriting": 100.0,
    "stroke_order": 100.0,
    "pronunciation": null
  },
  "scoring_method": "prototype geometric comparison; not trained AI",
  "feedback": "Your overall character shape is close to the reference. Your stroke order matches the saved reference well. These are geometric prototype estimates, not scores from a trained handwriting AI model."
}
```

### `GET /api/v1/practice-attempts?user_id={user_id}`
- **Purpose**: Lists practice attempts for a learner with scores and feedback.
- **Request**: `GET http://127.0.0.1:8000/api/v1/practice-attempts?user_id=1`
- **Response**:
```json
{
  "attempts": [
    {
      "attempt_id": 71,
      "user_id": 1,
      "character_id": 194,
      "character_text": "ノ",
      "stroke_count": 1,
      "handwriting_score": 100.0,
      "stroke_order_score": 100.0,
      "pronunciation_score": null,
      "pronunciation_status": "not_submitted",
      "pronunciation_feedback": null,
      "transcribed_text": null,
      "feedback": "Your overall character shape is close to the reference...",
      "created_at": "2026-11-17T06:21:09"
    }
  ]
}
```

---

## 7. Audio & Transcription Routes

> [!IMPORTANT]
> **Audio and Pronunciation Implementation Reality:** The app records audio in the browser and saves it to the selected practice attempt. The transcription route uses local Faster-Whisper by default (or hosted OpenAI only if explicitly configured). The score is normalized transcript similarity against expected text; it does not measure phoneme-level or acoustic pronunciation. Real mic validation remains pending for all four tutor groups. Sanskrit is conditioned with Whisper's `sa` language code; its gTTS reference voice is an approximate Hindi/Indic voice.

### `PUT /api/v1/practice-attempts/{attempt_id}/pronunciation-audio`
- **Purpose**: Saves base64-encoded browser audio for a practice attempt.
- **Request**: `PUT http://127.0.0.1:8000/api/v1/practice-attempts/{attempt_id}/pronunciation-audio`
```json
{
  "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=",
  "mime_type": "audio/webm"
}
```
- **Response**:
```json
{
  "message": "Pronunciation recording saved.",
  "attempt_id": 71,
  "pronunciation_score": null,
  "assessment_note": "Speech recognition and scoring will be connected in a later step."
}
```

### `POST /api/v1/practice-attempts/{attempt_id}/pronunciation-assessment`
- **Purpose**: Evaluates supplied transcript text against the target using normalized text similarity. It does not evaluate accent or phonemes.
- **Request**: `POST http://127.0.0.1:8000/api/v1/practice-attempts/{attempt_id}/pronunciation-assessment`
```json
{
  "transcribed_text": "no"
}
```
- **Response**:
```json
{
  "message": "Pronunciation assessment saved.",
  "attempt_id": 71,
  "transcribed_text": "no",
  "pronunciation_score": 100.0,
  "scoring_method": "normalized transcript text comparison; not an acoustic AI model"
}
```

### `POST /api/v1/practice-attempts/{attempt_id}/transcribe`
- **Purpose**: Transcribes the saved recording with the configured provider (local Faster-Whisper by default).
- **Request**: `POST http://127.0.0.1:8000/api/v1/practice-attempts/{attempt_id}/transcribe`
- **Response**:
```json
{
  "message": "Speech transcription and pronunciation scoring complete.",
  "attempt_id": 71,
  "transcribed_text": "no",
  "pronunciation_score": 100.0,
  "transcription_provider": "local faster-whisper",
  "scoring_method": "speech transcription followed by normalized text similarity"
}
```

