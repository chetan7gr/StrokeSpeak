# StrokeSpeak Run & Startup Instructions

> **Current-state correction (2026-11-21):** See [CURRENT_PROJECT_STATUS.md](CURRENT_PROJECT_STATUS.md) for authoritative counts and limitations. After starting MySQL, backend, and frontend, create an account or sign in on the StrokeSpeak page. The app now uses an 8-hour signed session; do not add `?learner_id=` to select accounts. Speech uses local Faster-Whisper and transcript similarity, not phoneme-level pronunciation scoring.

Step-by-step instructions for launching and verifying the StrokeSpeak full-stack platform.

---

## 1. Startup Order

Always start the **backend first**, verify the health check, and then start the **frontend**.

```
[ MySQL 8.0 ] ---> [ FastAPI Backend (Port 8000) ] ---> [ Vite React Frontend (Port 5173) ]
```

---

## 2. Environment & Interpreter Configuration

> [!NOTE]
> The backend interpreter is located at:
> `C:\Users\CHETAN\.vscode\StrokeSpeak\backend\.venv\Scripts\python.exe`
> The virtual environment configuration (`pyvenv.cfg`) references the base Python 3.12 installation at `C:\Users\CHETAN\AppData\Local\Programs\Python\Python312` (confirmed existing on disk). Key dependencies (`fastapi` 0.143.2, `uvicorn` 0.54.0, `mysql.connector` 26.7.0) are verified in this environment.

---

## 3. Backend Startup (Port 8000)

### Primary Command
Open a terminal in the `backend/` directory:
```powershell
# Tested on Windows PowerShell:
Set-Location "C:\Users\CHETAN\.vscode\StrokeSpeak\backend"
& "C:\Users\CHETAN\.vscode\StrokeSpeak\backend\.venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8000
```

### Verification (Health Probe)
Once Uvicorn logs `Application startup complete`, probe the health endpoint:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method Get
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "StrokeSpeak API",
  "database": "connected"
}
```

### Interactive API Documentation (Swagger UI)
- URL: `http://127.0.0.1:8000/docs`
- **Safety Rule**: In Swagger (/docs) press Execute only on GET routes. Never press Execute on transcribe, pronunciation-audio or pronunciation-assessment, or on any POST/PUT/DELETE route; they can create rows or call an external service.

---

## 4. Frontend Startup (Port 5173)

Open a separate terminal in the `frontend/` directory.

### Verified package.json Scripts
The `frontend/package.json` defines four scripts:
- `npm run dev`: Starts the local Vite development server on port 5173.
- `npm run build`: Bundles the React application into `frontend/dist/`.
- `npm run lint`: Runs Oxlint.
- `npm run preview`: Previews the production build locally.

### Development Server Launch (Mandatory Execution Mode)
```powershell
# Tested on Windows PowerShell:
Set-Location "C:\Users\CHETAN\.vscode\StrokeSpeak\frontend"
npm run dev
```

The terminal will report:
```
  VITE v8.3.5  ready in ... ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

> [!IMPORTANT]
> **Proxy & CORS Architecture Note**:
> 1. **Run the frontend with `npm run dev`**: It automatically proxies all `/api` calls to `http://127.0.0.1:8000` via `frontend/vite.config.js`.
> 2. **The built `dist` folder does not work without a proxy**: Opening `frontend/dist/index.html` directly or serving it with a basic static web server will fail because relative `/api` paths will not resolve.
> 3. **Backend CORS Architecture**: The backend has no CORS middleware by design in this version. All browser communication relies on the Vite development proxy to ensure same-origin requests (`http://localhost:5173/api/...` forwarded to `127.0.0.1:8000`).
> 4. **Test Server Cleanup**: Stop the port 8001 test server if it is running before launching (`Get-NetTCPConnection -LocalPort 8001 | Stop-Process -Id {$_.OwningProcess} -Force`).

### Building for Production
```powershell
# Tested on Windows PowerShell:
Set-Location "C:\Users\CHETAN\.vscode\StrokeSpeak\frontend"
npm run build
```

---

## 5. Live Demonstration and Learner Accounts

Four user rows currently exist. Two legacy placeholder-hash accounts cannot authenticate. Register a real account in the app or sign in with an account you control; a new account provides a clean learner profile. The app no longer selects accounts through a URL parameter or typed learner ID. Confirm registration and sign-in after starting both local servers before presenting.

---

## 6. Commands Marked as UNTESTED

The following administrative or optional commands have not been executed in this maintenance cycle:

- `[UNTESTED] python -m pytest tests/` — automated unit test suite.
- `[UNTESTED] npm run preview` — vite preview server for production bundle.
- `[UNTESTED] python backend/scripts/seed_database.py` — full fresh database re-seeding.
- *Note: `npm run test` is not defined in `frontend/package.json` and does not exist.*

---

## 7. Cold-Start Procedure (Clean Boot from Scratch) [UNTESTED]

> [!WARNING]
> This cold-start procedure is marked **[UNTESTED]** because a full server restart has not been executed during this evaluation session to ensure zero service disruption. **Do not run this procedure during an active presentation or evaluation.**

If restarting the platform from a completely shut-down computer:

### Step 1: Ensure MySQL 8.0 Service is Running & Port 8001 Stopped
Verify MySQL is active on standard port 3306 before starting the application servers, and stop the port 8001 test server if it is running:
```powershell
Get-Service -Name MySQL*
# Stop port 8001 test server if active:
Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### Step 2: Start the Backend Server First
Open a fresh PowerShell terminal:
```powershell
Set-Location "C:\Users\CHETAN\.vscode\StrokeSpeak\backend"
& "C:\Users\CHETAN\.vscode\StrokeSpeak\backend\.venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8000
```
Wait until the terminal displays: `Application startup complete.`

### Step 3: Probe the Backend Health Endpoint
Open a second terminal and confirm database connectivity:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method Get
```
Expected output:
```json
{"status": "healthy", "service": "StrokeSpeak API", "database": "connected"}
```

### Step 4: Start the Frontend Vite Development Server
In the second terminal, navigate to the frontend directory and launch Vite:
```powershell
Set-Location "C:\Users\CHETAN\.vscode\StrokeSpeak\frontend"
npm run dev
```
Wait until Vite reports: `VITE v8.3.5 ready in ... ms` and displays `http://localhost:5173/`.

### Step 5: Open the Sign-In Page
Open Google Chrome or Microsoft Edge and navigate to:
```
http://localhost:5173/
```
Create a new learner account or sign in. The frontend stores the signed session token and uses the account attached to it for lesson progress, attempts, and quizzes.

## 8. Optional Admin-Only Script Demo Release

The demo generator refuses to release Sanskrit, Tamil, or Simplified Chinese videos while their reference paths are unverified or awaiting qualified instructional review. It also requires a genuine learner drawing validation for the target lesson. Never pass `--validated-lesson-id` until both conditions have actually been met.

After review and learner validation, configure the intended administrator account ID in `backend/.env` as `STROKESPEAK_ADMIN_USER_IDS`, restart FastAPI, and sign in to the frontend with that account. Copy the current `strokespeak_access_token` value from the browser's Local Storage. Run the generator in the backend terminal and paste the token at its hidden prompt; the script checks `/api/v1/auth/me` before rendering and sends the same Bearer token to the protected registration route. Do not save or commit the token.

Example, only after the documented release gates are satisfied:

```powershell
Set-Location "C:\Users\CHETAN\.vscode\StrokeSpeak\backend"
$lessonId = 339 # Replace only with the lesson ID that passed both release gates.
.\.venv\Scripts\python.exe .\scripts\generate_script_demo_videos.py --apply --validated-lesson-id $lessonId
```

