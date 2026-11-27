# StrokeSpeak — Intelligent Multilingual Character & Speech Tutor

**MCA Final-Year Minor Project**

StrokeSpeak is a full-stack multilingual writing and pronunciation tutor supporting **Japanese (Hiragana & Katakana)**, **Sanskrit (Devanagari)**, **Tamil**, and **Simplified Chinese**. It combines interactive stroke-order animation, canvas handwriting evaluation, CNN character recognition, local speech transcription, AI teacher tutorial videos (*Sensei Kai*), and gated section quizzes.

---

## Core Features

- **4-Language Learning Studio:** Guided lessons across **Japanese** (`ja-hiragana`, `ja-katakana`), **Sanskrit** (`sa-devanagari`), **Tamil** (`ta`), and **Simplified Chinese** (`zh-hans`).
- **Interactive Stroke-Order Animation:** Step-by-step reference stroke playback and guided tracing canvas (`700 × 320`).
- **Handwriting Assessment & CNN Recognition:** Evaluates geometric shape similarity (`>= 60%`), stroke-order similarity (`>= 55%` when `stroke_reference_verified=True`), and CNN character recognition (`is_match=True`). Mismatched CNN predictions (`status=mismatch_rejected`) cannot pass on geometric overlap alone.
- **Speech Pronunciation Practice:** Local `faster-whisper` (`base`, CPU `int8`) transcription with silence/short-audio rejection (`HTTP 422`) and normalized Levenshtein transcript matching (`>= 50%` required).
- **Sensei Kai AI Teacher Videos:** Character and stroke tutorial MP4s served via `/api/v1/lessons/{id}/video`.
- **Progress Tracking & Gated Quizzes:** Lesson completion (`PUT /api/v1/lessons/{id}/progress`) enforces passing handwriting and pronunciation attempts on `character` lessons (`HTTP 409` otherwise), and `STROKESPEAK_DEVELOPER_BYPASS=false` enforces sequential section quiz prerequisites.

---

## Architecture

- **Frontend:** React 19 + Vite 8 + Tailwind CSS 4 (`frontend/`)
- **Backend:** FastAPI + Uvicorn (`backend/main.py`, `backend/app/quiz_api.py`)
- **Database:** MySQL 8.x (`strokespeak` schema via `backend/app/db/database.py`)
- **Handwriting AI:** 4 trained 3-stage `ScriptCNN` models (`32×32` OpenCV preprocessing) with automatic exact NumPy `*_weights.npz` CPU fallback when PyTorch `torch_python.dll` is blocked by Windows Smart App Control (`WinError 4551`)
- **Speech AI:** Local `faster-whisper` (`base`, CPU `int8`) with optional OpenAI fallback when explicitly configured in `backend/.env`

---

## Prerequisites

- **Python 3.12** (`backend/.venv`)
- **Node.js 20+ & npm** (`frontend/`)
- **MySQL 8.x** running locally on port `3306`

---

## Local Setup & Installation

### 1. Database & Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\pip install -r requirements-ai.txt
Copy-Item .env.example .env
```

Edit `backend/.env` with your local MySQL credentials and a unique 32+ character `STROKESPEAK_AUTH_SECRET` (never commit `.env`):

```powershell
# Generate a local signing secret:
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Create the MySQL database and tables (see `docs/DATABASE_SETUP.md` for full seeding order):

```powershell
.\.venv\Scripts\python.exe create_database.py
.\.venv\Scripts\python.exe create_tables.py
.\.venv\Scripts\python.exe seed_data.py
```

### 2. Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
```

Leave `VITE_API_BASE_URL` empty in `frontend/.env` during local development so Vite's `/api` proxy in `frontend/vite.config.js` forwards requests to `http://127.0.0.1:8000`.

---

## Running the Application

Start FastAPI backend (`http://127.0.0.1:8000`):

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Start Vite frontend (`http://127.0.0.1:5173`):

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

---

## Verification Commands

- **CNN 4-Script Smoke Check:** `backend\.venv\Scripts\python.exe backend\scripts\verify_all_four_models.py`
- **Frontend Production Build:** `npm --prefix frontend run build`

---

## Large External Assets & Source Licensing

- **Wav2Lip Weights Excluded (`>100 MB`):** `backend/ml_models/wav2lip/Wav2lip/wav2lip_gan.pth` (`415.61 MB`) exceeds GitHub's 100 MB file limit and is excluded via `.gitignore`. Pre-rendered tutorial MP4s in `backend/static/videos/` still play normally; if regenerating lip-synced videos locally, place `wav2lip_gan.pth` back in `backend/ml_models/wav2lip/Wav2lip/`.
- **Third-Party Stroke & Character Sources:**
  - **Simplified Chinese:** `hanzi-writer-data` (MIT License)
  - **Japanese:** `fude-kana-data` / KanjiVG-derived stroke data
  - **Devanagari / Tamil:** `lipi-devanagari`, Wikimedia Commons, and open-source reference sets
  - **Sanskrit Guru Non-Redistribution:** Staged candidate files referencing *Sanskrit Guru* (`© 2026 Sri Hayavadhana Info-Tech`, where only dictionary data is `CC BY-NC-SA 4.0` and SVG trajectories have no open redistribution license) are excluded from this public repository via `.gitignore`.

---

## Known Limitations & Scope

- **CNN Handwriting Domain Gap:** The 4 `ScriptCNN` models are trained on `32×32` synthetic/font-style and dataset samples; natural freehand variations (especially thick or non-standard strokes) can occasionally misclassify compared to human handwriting.
- **Speech Evaluation Scope:** Pronunciation grading uses normalized Levenshtein transcript similarity on `faster-whisper` output rather than acoustic phoneme-level scoring.

---

## Future Vercel Frontend Deployment

- Set the Vercel project **Root Directory** to `frontend`.
- Build command: `npm run build` | Output directory: `dist` (SPA routing configured in `frontend/vercel.json`).
- Set environment variable `VITE_API_BASE_URL` to your hosted FastAPI backend URL (and ensure backend CORS allows the Vercel origin).

---

## Git Workflow (Ongoing Development)

- `main`: Stable, faculty-ready branch.
- `dev` / feature branches: Used for ongoing updates from Antigravity, Codex, or local development before merging into `main`.
