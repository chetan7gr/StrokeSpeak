# StrokeSpeak Screenshot Capture Checklist

> **Current-state update (2026-11-21):** Sign in at `http://localhost:5173/`. Create a new account if a clean profile is needed. Do not use historical `?learner_id=` links. See [CURRENT_PROJECT_STATUS.md](CURRENT_PROJECT_STATUS.md) for counts and implementation limitations.

This checklist specifies the exact set of 13 screenshots required for the Final Project Report and the Presentation Slides (PPT). Use the specified file names and follow the capture setup to maintain visual consistency across submissions.

> [!IMPORTANT]
> **Learner Profile Guidance**: Use an authenticated account. A new account is a clean profile; existing accounts may contain historical attempts or progress.

---

## Screenshot Inventory Summary

| # | Item Name | Suggested File Name | Viewport / Source | Capture Mode | Purpose |
|:---|:---|:---|:---|:---|:---|
| 1 | **Dashboard Overview** | `screenshots/01_dashboard_overview.png` | Desktop (1280x800) | Automated / Chrome | Main interface, active learner header, syllabus metrics |
| 2 | **Language Selection** | `screenshots/02_language_selector.png` | Desktop (1280x800) | Automated / Chrome | Multilingual tab bar showing 4 active languages |
| 3 | **Lesson Stroke Replay** | `screenshots/03_stroke_replay_japanese.png` | Desktop (1280x800) | Automated / Chrome | Learning Studio with animated KanjiVG stroke order |
| 4 | **Interactive Canvas** | `screenshots/04_canvas_drawing_active.png` | Desktop (1280x800) | Automated / Chrome | In-progress stroke drawing on vector HTML5 canvas |
| 5 | **Score & Feedback Card** | `screenshots/05_score_feedback_correct.png` | Desktop (1280x800) | Automated / Chrome | Score card showing shape and order evaluation |
| 6 | **Wrong-Drawing Penalty** | `screenshots/06_score_feedback_penalty.png` | Desktop (1280x800) | Automated / Chrome | Score card demonstrating directional order penalty |
| 7 | **Progress & Summary** | `screenshots/07_progress_summary_view.png` | Desktop (1280x800) | Automated / Chrome | Lesson completion marks and recent attempt analytics |
| 8 | **Draft Reference Notice** | `screenshots/08_draft_reference_warning.png` | Desktop (1280x800) | Automated / Chrome | Sanskrit/Tamil draft provenance warning & approximate Sanskrit voice label |
| 9 | **Chinese Curriculum** | `screenshots/09_chinese_curriculum.png` | Desktop (1280x800) | Automated / Chrome | Foundation and Beginner lessons; draft stroke-guide warning |
| 10 | **Mobile 390px View** | `screenshots/10_mobile_responsive_390px.png` | Mobile (390x844) | Automated / Chrome | DevTools device emulation showing 0 horizontal overflow |
| 11 | **Swagger /docs Page** | `screenshots/11_fastapi_swagger_docs.png` | Browser (1280x800) | Automated / Chrome | FastAPI interactive Swagger UI (27 OpenAPI paths at current checkpoint) |
| 12 | **MySQL Row Counts** | `screenshots/12_mysql_table_counts.png` | MySQL Workbench / CLI | **Manual Capture** | Current read-only table-count output (809 rows across six core tables; verified 2026-11-21) |
| 13 | **API Health Check** | `screenshots/13_backend_health_check.png` | Browser / JSON | Automated / Chrome | JSON response: `status: healthy`, `database: connected` |

---

## Detailed Capture Instructions & Captions

### 1. Dashboard Overview
- **File Name**: `screenshots/01_dashboard_overview.png`
- **URL**: `http://localhost:5173/`
- **Setup**: Sign in with the account selected for the screenshot. Ensure the header shows the signed-in learner and course level navigation.
- **Report Caption**: *Figure 4.1: StrokeSpeak Main Dashboard showing active learner identification, overall syllabus progress, and modular level cards.*
- **Slide Reference**: Slide 4 (System Architecture) & Slide 6 (Curriculum Design).

### 2. Language Selection Bar
- **File Name**: `screenshots/02_language_selector.png`
- **URL**: `http://localhost:5173/`
- **Setup**: Focus capture on the upper sub-navigation showing the four active tabs: Japanese, Sanskrit (Devanagari), Tamil, and Simplified Chinese.
- **Report Caption**: *Figure 4.2: Multilingual Language Selector isolating the four public writing systems while filtering legacy database records.*
- **Slide Reference**: Slide 3 (Project Objectives & Scope).

### 3. Lesson with Stroke Replay
- **File Name**: `screenshots/03_stroke_replay_japanese.png`
- **URL**: `http://localhost:5173/` -> Japanese -> Lesson 61 (`あ`)
- **Setup**: Trigger the animated stroke replay; capture mid-animation showing numbered directional vector arrows on the SVG canvas.
- **Report Caption**: *Figure 4.3: Interactive Stroke Replay Guide dynamically rendering KanjiVG vector paths for Hiragana vowel 'あ'.*
- **Slide Reference**: Slide 7 (Interactive Stroke Animation).

### 4. Interactive Canvas Drawing
- **File Name**: `screenshots/04_canvas_drawing_active.png`
- **URL**: `http://localhost:5173/` -> Learning Studio (Lesson 61)
- **Setup**: Draw character `あ` on the canvas; capture with pen cursor visible and Clear / Submit buttons enabled.
- **Report Caption**: *Figure 4.4: HTML5 Drawing Canvas capturing discrete stroke coordinates and millisecond timestamp vectors.*
- **Slide Reference**: Slide 8 (Drawing Canvas & Coordinate Tracking).

### 5. High Score and Algorithmic Feedback Card
- **File Name**: `screenshots/05_score_feedback_correct.png`
- **URL**: `http://localhost:5173/` -> Submit correct `あ` attempt
- **Setup**: Capture the score modal/card showing separate Handwriting Shape Score (observed post-change synthetic wobble range 96.35% – 97.12% HW and 88.90% – 96.45% order, HANDOFF_REPORT.md Section 20 Table 3; reference model 100.0%), Stroke Order Score (100.0%), and the note on Speaking Practice.
- **Report Caption**: *Figure 4.5: Practice Evaluation Card displaying decoupled handwriting shape score and stroke-order vector scores.*
- **Slide Reference**: Slide 9 (Algorithmic Handwriting Evaluator).

### 6. Deliberately Wrong Drawing Score Card
- **File Name**: `screenshots/06_score_feedback_penalty.png`
- **URL**: `http://localhost:5173/` -> Submit reversed stroke or incorrect geometry
- **Setup**: Draw stroke in reverse direction; capture the resulting drop in Stroke Order Score (observed 0.00 on reversed stroke for single-stroke ノ Att 74, two-stroke い Att 76, ア Att 77, HANDOFF_REPORT.md Section 20 Table 3) demonstrating directional cosine penalty.
- **Report Caption**: *Figure 4.6: Algorithmic Evaluation Penalty showing stroke order score reduction when start-to-end vector cosine is negative.*
- **Slide Reference**: Slide 10 (Empirical Testing & Robustness).

### 7. Learning Progress and Summary Analytics
- **File Name**: `screenshots/07_progress_summary_view.png`
- **URL**: `http://localhost:5173/` -> Completed lesson view / Dashboard recent activity
- **Setup**: Capture recent activity table showing attempt history with individual stroke order and shape percentages.
- **Report Caption**: *Figure 4.7: Learner Analytics view summarizing historical practice attempts and lesson completion timestamps.*
- **Slide Reference**: Slide 4 & Slide 12.

### 8. Sanskrit / Tamil Fallback Notice
- **File Name**: `screenshots/08_fallback_sanskrit_tamil.png`
- **URL**: `http://localhost:5173/` -> Sanskrit Tab -> Lesson 339 (`अ`)
- **Setup**: Capture a Tamil guide with its draft-provenance warning or a Sanskrit/Chinese guide with the pending-instructor-review warning. If showing Sanskrit reference audio, keep its Hindi/Indic approximation label visible.
- **Report Caption**: *Figure 4.8: Transparent Fallback Handling showing unverified stroke notification and synthetic voice approximation disclaimer.*
- **Slide Reference**: Slide 11 & Slide 13.

### 9. Simplified Chinese Curriculum
- **File Name**: `screenshots/09_chinese_prototype_badge.png`
- **URL**: `http://localhost:5173/` -> Simplified Chinese Tab
- **Setup**: Capture current Foundation and Beginner lesson cards; when a reference guide is available, include its draft provenance warning.
- **Report Caption**: *Figure 4.9: Simplified Chinese Foundation Prototype displaying explicit academic scope disclaimer.*
- **Slide Reference**: Slide 6 & Slide 13.

### 10. Mobile Responsive 390px View
- **File Name**: `screenshots/10_mobile_responsive_390px.png`
- **URL**: `http://localhost:5173/` (Device: iPhone 12 / 390x844 in Chrome DevTools)
- **Setup**: Set viewport dimension to 390px width. Capture Studio screen showing vertically stacked canvas and controls without horizontal scroll.
- **Report Caption**: *Figure 4.10: Mobile Responsive View at 390px width demonstrating fluid flexbox layout and touch-accessible canvas.*
- **Slide Reference**: Slide 8 & Slide 12.

### 11. FastAPI Interactive Swagger Docs
- **File Name**: `screenshots/11_fastapi_swagger_docs.png`
- **URL**: `http://127.0.0.1:8000/docs`
- **Setup**: Capture Swagger UI showing `/api/v1/health`, `/api/v1/languages`, `/api/v1/lessons`, and `/api/v1/practice-attempts`.
- **Report Caption**: *Figure 4.11: FastAPI Interactive OpenAPI Documentation exposing RESTful endpoints with strict Pydantic v2 schemas.*
- **Slide Reference**: Slide 4 (System Architecture).

> [!WARNING]
> **Swagger `/docs` Safety Rule**:
> When using Swagger UI (`http://127.0.0.1:8000/docs`), **only press "Execute" on `GET` requests** (e.g. `GET /api/v1/health`, `GET /api/v1/languages`, `GET /api/v1/lessons`). **Never press "Execute" on the transcribe or pronunciation-audio routes** (`POST /api/v1/practice-attempts/{attempt_id}/transcribe`, `PUT /api/v1/practice-attempts/{attempt_id}/pronunciation-audio`) as these routes involve unverified external calls and database mutations.

### 12. MySQL Table Counts & Schema Verification (MANUAL CAPTURE)
- **File Name**: `screenshots/12_mysql_table_counts.png`
- **Source**: MySQL Command Line or MySQL Workbench
- **Command**:
  ```sql
  SELECT 'characters' AS tbl, count(*) FROM characters UNION ALL
  SELECT 'languages', count(*) FROM languages UNION ALL
  SELECT 'learning_lessons', count(*) FROM learning_lessons UNION ALL
  SELECT 'lesson_progress', count(*) FROM lesson_progress UNION ALL
  SELECT 'practice_attempts', count(*) FROM practice_attempts UNION ALL
  SELECT 'users', count(*) FROM users;
  ```
- **SECURITY WARNING**: Capture by hand from local MySQL CLI or Workbench. **Ensure that any typed password, connection string, or user credential is completely cleared or hidden from the screen before capturing.**
- **Report Caption**: *Figure 4.12: Relational Database Record Verification in MySQL 8.0 (as of 2026-11-17 17:47: 105 practice attempts, 739 total rows across 6 tables (regenerate with backend\scripts\show_table_counts.py); baseline capture 720 rows).*
- **Slide Reference**: Slide 5 (Database Architecture).

### 13. API Health Check Endpoint
- **File Name**: `screenshots/13_backend_health_check.png`
- **URL**: `http://127.0.0.1:8000/api/v1/health`
- **Setup**: Browser window rendering formatted JSON response: `{"status":"healthy","service":"StrokeSpeak API","database":"connected"}`.
- **Report Caption**: *Figure 4.13: API Health Check probe confirming live database connectivity and Uvicorn server operation.*
- **Slide Reference**: Slide 4 (System Architecture).
