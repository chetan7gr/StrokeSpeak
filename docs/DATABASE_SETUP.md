# StrokeSpeak Database Setup & Migration Guide

> **Live-state reference:** This guide's seed order and sample counts describe a historical build. Current live counts (verified 2026-11-21) are in [CURRENT_PROJECT_STATUS.md](CURRENT_PROJECT_STATUS.md). The runbook below is still marked untested on an empty machine; do not replay its chronological seed sequence over the populated database.

> [!WARNING]
> **Status: UNTESTED on a Fresh Machine**  
> This setup runbook is documented based on the historical build logs in `backend/HANDOFF_REPORT.md`. It has **not** been re-executed from scratch on a clean machine during this evaluation session to ensure zero downtime or disruption to the live running database. **Do not run these scripts against the currently active production database.**

This guide explains how to initialize and seed a fresh MySQL database for the StrokeSpeak platform from an empty machine.

---

## 1. Prerequisites

1. **MySQL Server 8.0+**: Installed and running on `localhost:3306`.
2. **Python 3.12**: Virtual environment configured in `backend/.venv` with required packages (`mysql-connector-python`, `fastapi`, `python-dotenv`).

---

## 2. Database Creation & User Privileges

Open the MySQL command line client or MySQL Workbench as `root`:

```sql
-- 1. Create the database with UTF-8 Unicode support
CREATE DATABASE IF NOT EXISTS strokespeak 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 2. Create a dedicated application user (replace placeholder credentials)
CREATE USER IF NOT EXISTS 'strokespeak_user'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD_HERE';

-- 3. Grant privileges on the strokespeak database
GRANT ALL PRIVILEGES ON strokespeak.* TO 'strokespeak_user'@'localhost';
FLUSH PRIVILEGES;
```

*(Alternatively, run `python backend/create_database.py` which prompts interactively for MySQL root credentials to create the database).*

---

## 3. Environment Configuration (`backend/.env`)

Copy the template from `backend/.env.example` to `backend/.env` (in the `backend/` directory):

```bash
cd backend
copy .env.example .env
```

Open `backend/.env` and supply your local database credentials:

```ini
DB_HOST=localhost
DB_PORT=3306
DB_NAME=strokespeak
DB_USER=strokespeak_user
DB_PASSWORD=YOUR_PASSWORD_HERE
STROKESPEAK_TRANSCRIPTION_PROVIDER=openai
OPENAI_API_KEY=leave-empty
```
*(Keep `OPENAI_API_KEY=leave-empty` or empty if not using cloud speech recognition; the live app uses local browser audio).*

---

## 4. Relational Schema Creation (Tables)

From the `backend/` directory, execute `create_tables.py` using the dedicated virtual environment Python:

```cmd
cd backend
.\.venv\Scripts\python.exe create_tables.py
```

This creates the six core relational tables:
1. `users`: Stores learner profiles (`id`, `name`, `email`, `password_hash`, `created_at`).
2. `languages`: Stores language scripts (`id`, `name`, `script_code`).
3. `characters`: Stores glyph metadata, stroke counts, and vector coordinate JSON.
4. `learning_lessons`: Stores curriculum lessons, units, and level attributes (no separate `levels` table; levels are stored in `learning_lessons`).
5. `lesson_progress`: Tracks completion status and scores per learner.
6. `practice_attempts`: Logs individual canvas drawing submissions and evaluations.

---

## 5. Seed Scripts Execution Order (Chronological Handoff Sequence)

To reconstruct the exact database state recorded in `backend/HANDOFF_REPORT.md`, execute the seed and migration scripts in the exact order they were applied during development:

```cmd
cd backend

:: Step 1: Base seed (Starter language, initial test user, initial lessons)
.\.venv\Scripts\python.exe seed_data.py

:: Step 2: Correct Hiragana meaning labels and gojuon ordering
.\.venv\Scripts\python.exe scripts\fix_japanese_labels.py

:: Step 3: Seed 46 Katakana characters (Character IDs 170-215)
.\.venv\Scripts\python.exe scripts\seed_katakana.py

:: Step 4: Seed Sanskrit language row and starter characters (Character IDs 216-235)
.\.venv\Scripts\python.exe scripts\seed_sanskrit.py

:: Step 5: Seed added Tamil characters (Character IDs 236-240)
.\.venv\Scripts\python.exe scripts\seed_tamil_extra.py

:: Step 6: Seed Simplified Chinese language and 12 characters (Character IDs 241-252)
.\.venv\Scripts\python.exe scripts\seed_chinese.py

:: Step 7: Seed Katakana first vowel lesson (Lesson ID 315)
.\.venv\Scripts\python.exe scripts\seed_katakana_lesson.py

:: Step 8: Seed KanjiVG SVG paths and normalized vector coordinates for Kana
.\.venv\Scripts\python.exe scripts\seed_reference_strokes.py

:: Step 9: Seed Japanese Beginner curriculum (Lessons 316-338)
.\.venv\Scripts\python.exe scripts\seed_japanese_beginner.py

:: Step 10: Seed Multilingual Featured curriculum (Sanskrit 339-347, Chinese 348-352, Tamil 353-356)
.\.venv\Scripts\python.exe scripts\seed_featured_curriculum.py

:: Step 11: Seed Spare Demo Learner (User ID 3)
.\.venv\Scripts\python.exe scripts\add_spare_learner.py
```

---

## 6. Verification of Final Row Counts

Run the table count verification script:

```cmd
cd backend
.\.venv\Scripts\python.exe scripts\show_table_counts.py
```

**Current live counts (verified 2026-11-21)**:
- `users`: **4**
- `languages`: **12** (4 active public: `ja-hiragana`, `sa-devanagari`, `ta`, `zh-hans`; plus legacy rows)
- `characters`: **250** (including all 92 Kana, Sanskrit, Tamil, Chinese, and test character 169)
- `learning_lessons`: **394** (203 public-script rows, 191 hidden legacy rows)
- `lesson_progress`: **17**
- `practice_attempts`: **132**
- Quiz tables: **10 quizzes**, **48 questions**, **0 learner submissions**

---

## 7. Fast Restore Alternative: Full Database Export JSON

Instead of running individual seed scripts, a historical database snapshot is stored at:
`backend/db_backups/full_export_2026-11-17.json`

*(Note: The JSON export contains placeholder password hashes and should only be imported using an authorized database restore utility in a trusted environment).*
