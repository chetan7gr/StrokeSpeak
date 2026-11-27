# StrokeSpeak Cold-Start Checklist & Runbook

> **Status: UNTESTED** (This checklist is a prepared runbook for clean manual startup. Label: UNTESTED until executed by hand.)

This document provides the step-by-step procedure to cold-start the StrokeSpeak platform from a completely stopped state. Follow these numbered steps strictly in order.

---

## 1. Stop Any Lingering Processes (Clean Slate)
* **Goal**: Ensure ports `8000`, `5173`, and `8001` are completely free before starting. **Stop the port 8001 test server if it is running** (a secondary backend instance may have been left running on port 8001 from earlier test runs).
* **Commands** (PowerShell):
  ```powershell
  # Check if ports 8000, 5173, or 8001 are listening
  Get-NetTCPConnection -LocalPort 8000, 5173, 8001 -ErrorAction SilentlyContinue | Select-Object LocalPort, OwningProcess, State

  # If any process is listening (including on port 8001), terminate by PID:
  Stop-Process -Id <PID> -Force
  ```
  *(Alternative Windows Command Prompt)*:
  ```cmd
  netstat -ano | findstr :8000
  netstat -ano | findstr :5173
  netstat -ano | findstr :8001
  taskkill /PID <PID> /F
  ```
* **Expected Result**: No processes listening on ports 8000, 5173, or 8001.
* **Troubleshooting**: If termination fails or access is denied, open Windows Task Manager and end any lingering `python.exe` or `node.exe` processes.

---

## 2. Terminal 1: Start Backend Server
* **Goal**: Launch FastAPI backend on port 8000 using the dedicated virtual environment.
* **Commands** (from project root `C:\Users\CHETAN\.vscode\StrokeSpeak`):
  ```cmd
  cd backend
  .\.venv\Scripts\python.exe -m uvicorn main:app --port 8000
  ```
  *(Note: `--reload` is deliberately omitted for stable demo execution to prevent unexpected auto-reloads.)*
* **Expected Result**:
  ```text
  INFO:     Started server process [...]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
  ```
* **Troubleshooting**:
  * **Application Control Policy Block**: Direct execution of `.\.venv\Scripts\uvicorn.exe` will fail with an Application Control policy block on Windows. Always use `.\.venv\Scripts\python.exe -m uvicorn`.
  * **Port 8000 in use (`WinError 10048`)**: A previous uvicorn instance is still active. Return to Step 1 and kill the process on port 8000.
  * **MySQL Connection Refused on Startup**: Ensure the MySQL Windows service is running. Run `Get-Service -Name MySQL*` in PowerShell or open `services.msc` and verify `MySQL80` status is "Running".

---

## 3. Verify Backend Health & Database Connectivity
* **Goal**: Verify that the backend is alive and connected to MySQL before launching the frontend.
* **Command**:
  ```powershell
  curl http://127.0.0.1:8000/api/v1/health
  ```
  *(Or open `http://127.0.0.1:8000/api/v1/health` in any browser.)*
* **Expected Result**:
  ```json
  {"status":"healthy","database":"connected"}
  ```
  HTTP Status: `200 OK`.
* **Troubleshooting**:
  * **HTTP 503 / `database: "disconnected"`**: Backend is running, but MySQL is unreachable. Check that MySQL service is running in `services.msc` and verify variables in `backend\.env` (`DB_HOST=localhost`, `DB_PORT=3306`, `DB_NAME=strokespeak`, `DB_USER=root`, `DB_PASSWORD`).
  * **Connection Refused / Failed to Connect**: Backend process in Terminal 1 did not start or crashed on launch. Inspect error traceback in Terminal 1.

---

## 4. Terminal 2: Start Frontend Development Server
* **Goal**: Launch Vite development server with API proxy configured.
* **Commands** (from project root `C:\Users\CHETAN\.vscode\StrokeSpeak` in a second terminal):
  ```cmd
  cd frontend
  npm run dev
  ```
  *(Important Architecture Note: Always run the frontend with `npm run dev` because Vite's development server proxies `/api` calls directly to `http://127.0.0.1:8000`. The production-built `frontend\dist` folder does not work without a reverse proxy; opening `frontend\dist\index.html` directly in a browser will fail to reach the API. Furthermore, the backend has no CORS middleware by design in this version, so it relies on the Vite development proxy for local browser access.)*
* **Expected Result**:
  ```text
  VITE v...  ready in ... ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
  ```
* **Troubleshooting**:
  * **Port 5173 in use**: Vite will ask to switch to port 5174. If that occurs, kill the process on 5173 or press `Ctrl+C`, run `npx kill-port 5173`, and rerun `npm run dev`.
  * **Missing modules**: If `node_modules` is damaged, run `npm install` (requires administrative permissions outside sandbox).

---

## 5. Open Web Application
* **Goal**: Load the application in a desktop browser.
* **Action**: Open Google Chrome or Microsoft Edge and navigate to:
  ```text
  http://localhost:5173
  ```
* **Expected Result**: The StrokeSpeak portal loads immediately displaying the landing screen with the language selector and character tier cards.
* **Troubleshooting**:
  * **Blank white screen**: Open Developer Tools (`F12`), check the **Console** tab. If you see `ERR_CONNECTION_REFUSED` on `/api/v1/...`, the Vite proxy cannot reach `http://127.0.0.1:8000`. Verify Terminal 1 is still running.
  * **Proxy Error in Terminal 2** (`[vite] http proxy error: ... ECONNREFUSED`): Backend server on port 8000 is not running. Start backend as shown in Step 2.

---

## 6. Verify Lesson List Loading Across All 4 Languages
* **Goal**: Confirm database lesson rows load properly for all supported languages.
* **Action**: In the web UI, click each language option in sequence:
  1. **Japanese**: Verify lessons load. Expected: 127 total lessons (99 Foundation, 25 Beginner, 2 Elementary, 1 Advanced). Katakana lessons are already included inside these 127 lessons and are not counted twice.
  2. **Sanskrit**: Verify lessons load. Expected: 9 lessons (5 Foundation, 4 Beginner).
  3. **Tamil**: Verify lessons load. Expected: 23 lessons (18 Foundation, 5 Beginner).
  4. **Chinese**: Verify lessons load. Expected: 5 prototype lessons (5 Foundation).
  *(Total lessons in MySQL database across all languages: 356 rows in `learning_lessons`.)*
* **Expected Result**: Each language displays its lesson cards with character glyphs, romaji/transliteration, and stroke count badges without infinite loading spinners or errors.
* **Troubleshooting**: If lessons fail to load, verify backend Terminal 1 logs; verify database has not been dropped or tables emptied (total seeded rows should be 356 in `learning_lessons`).

---

## 7. Verify Reference Audio Playback (Requires Internet)
* **Goal**: Confirm gTTS audio synthesis endpoint functions.
* **Action**: In any Japanese lesson (e.g. Lesson 1: "あ"), click the speaker / audio icon to play reference pronunciation.
* **Expected Result**: Audio generates and plays clearly through system speakers.
* **Troubleshooting**:
  * **Audio fails or HTTP 500 in backend**: gTTS requires active internet access to reach Google Text-to-Speech endpoints. If internet is disconnected, audio playback will fail. Mention during presentation: *"Reference audio streaming relies on Google TTS and requires active internet access."*

---

## 8. Sign In to a Learner Account
* **Goal**: Use a real account session; do not select another account by URL or numeric ID.
* **Action**: Open `http://localhost:5173/` and sign in, or create a new account for a clean learner profile.
* **Expected Result**: The header shows the signed-in learner name. Attempts, quiz history and lesson progress belong to that account.
* **Admin maintenance**: New accounts are learners. To enable shared course/reference maintenance for a deliberate administrator, add that account ID to `STROKESPEAK_ADMIN_USER_IDS` in `backend/.env` and restart the backend. Keep the file private.

---

## Quick Launcher Batch Files

For convenience, two small launcher scripts are provided in the repository root:
* `start_backend.bat`: Launches Terminal 1 backend process.
* `start_frontend.bat`: Launches Terminal 2 frontend development server.

*(Do NOT run them automatically; launch manually when initiating a cold start.)*
