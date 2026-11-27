# StrokeSpeak developer stroke capture

This standalone utility is not linked from React learner screens and is not included in the production Vite build.

## Run it

1. Start the backend in one PowerShell window:
   Set-Location C:\Users\CHETAN\.vscode\StrokeSpeak\backend
   .\.venv\Scripts\Activate.ps1
   uvicorn main:app --reload

2. Start Vite in a second PowerShell window:
   Set-Location C:\Users\CHETAN\.vscode\StrokeSpeak\frontend
   npm run dev

3. Open http://localhost:5173/dev-tools/stroke-reference-capture.html.
4. Select Sanskrit or Tamil and choose one of the 16 database characters. Trace the sequence from a cited teaching reference and lift the pointer between strokes.
5. Enter source title, HTTPS URL, creator/attribution, license, and captured-by fields. Export the JSON.
6. Copy the downloaded strokespeak-capture JSON into:
   C:\Users\CHETAN\.vscode\StrokeSpeak\backend\data\reference_strokes\capture-inbox

7. Run the staging pipeline from a backend PowerShell window:
   Set-Location C:\Users\CHETAN\.vscode\StrokeSpeak\backend
   .\.venv\Scripts\Activate.ps1
   python .\scripts\stage_external_stroke_candidates.py

8. Open the newest backend\data\reference_strokes\batch-review-* folder and inspect review_gallery.html.

## Safety

- The page makes GET requests only. Captures download as JSON and are never posted to the API or written to MySQL.
- Exports always remain captured_pending_review.
- The stage script accepts only the blocked Sanskrit/Tamil targets, validates database IDs and attribution, regenerates SVG from normalized points, and keeps instructor review pending.
- Japanese, Chinese, and completed Tamil அ references cannot be replaced through the inbox.
- No database import occurs; separate validation and explicit approval are still required.