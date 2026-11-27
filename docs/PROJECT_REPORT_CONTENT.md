# StrokeSpeak Project Report Content (Draft Chapters)

> **Current-state update (2026-11-21):** This draft contains earlier implementation descriptions. Use [CURRENT_PROJECT_STATUS.md](CURRENT_PROJECT_STATUS.md) as authoritative and reconcile every historical section before submission. The latest read-only snapshot is 809 core-table rows and 203 public lessons; the users table contains four rows, including two disabled legacy placeholder-hash accounts.

This document provides formal, thesis-ready draft chapters for the MCA Final Year Project Report on **StrokeSpeak: An AI-Powered Multilingual Handwriting and Pronunciation Learning and Assessment Platform**.

---

# Chapter 1: Introduction

## 1.1 Background & Motivation
Computer-Aided Language Learning (CALL) systems have advanced significantly over the past decade, yet the vast majority of commercial and academic applications prioritize Latin-based orthographies and vocabulary memorization (e.g., flashcard systems and multiple-choice quizzes). Non-Latin writing systems—such as Japanese Kana (Hiragana and Katakana), Sanskrit Devanagari, Tamil abugida, and Chinese Hanzi—present distinct orthographic hurdles for novice learners. In these scripts, character validity is strictly governed not only by static visual geometry but also by dynamic stroke order, stroke trajectory, and directional penmanship.

Improper stroke sequence and direction hinder calligraphic legibility, impede muscle memory development, and make handwriting recognition difficult. Furthermore, learners studying non-Latin scripts frequently lack synchronous access to expert native instructors who can observe their physical penmanship and provide immediate correction.

## 1.2 Problem Statement
Existing digital language learning applications suffer from three critical deficiencies:
1. **Lack of Dynamic Stroke Validation**: Most platforms assess handwriting via basic pixel overlap or static image classification, completely ignoring stroke order and stroke direction.
2. **Heavyweight & Opaque Machine Learning Architectures**: Deep convolutional neural network (CNN) classifiers require massive labeled datasets and high-end hardware, while behaving as "black boxes" that cannot provide granular feedback on which individual stroke was drawn in reverse or out of order.
3. **Fragmented Multi-Script Support**: Platforms rarely provide a unified architectural schema capable of handling phonetic syllabaries (Kana), alphasyllabic scripts with complex conjuncts (Devanagari and Tamil), and ideographic logographs (Chinese Hanzi).

## 1.3 Project Scope
StrokeSpeak addresses these challenges by delivering an interactive, full-stack pedagogical environment. The system's public scope spans four distinct writing systems:
- **Japanese**: 128 lessons in one tutor covering Hiragana and Katakana across Foundation (100), Beginner (25), Elementary (2), and Advanced (1).
- **Sanskrit (Devanagari)**: 29 lessons across Foundation and Beginner; its 14 foundational vowels now follow the full traditional order.
- **Tamil**: 32 lessons across Foundation, Beginner, Elementary, and Advanced.
- **Simplified Chinese**: 14 lessons across Foundation and Beginner.
*(The database has 394 learning lessons; 203 are tagged to public script rows and 191 legacy lessons are hidden.)*

---

# Chapter 2: Project Objectives

The core objectives of the StrokeSpeak platform are:
1. **Interactive Orthographic Guidance**: To synthesize animated vector stroke sequences that visually guide the learner through proper stroke order, trajectory, and count.
2. **Algorithmic Penmanship Evaluation**: To develop an algorithmic evaluation engine capable of independently scoring handwriting shape fidelity and directional stroke order without black-box ML opacity.
3. **Multi-Script Relational Data Architecture**: To design a normalized relational database schema in MySQL 8.0 that models languages, scripts, phonetic romanizations, characters, curriculum units, learner progress, and attempt histories.
4. **Synchronous Multi-Modal Feedback**: To provide concurrent visual and auditory feedback, integrating client-side speech practice and reference audio streaming.
5. **Cross-Platform Responsive Access**: To construct a modern, responsive web application compliant across both standard desktop screens and mobile device viewports (down to 390px).

---

# Chapter 3: Technology Stack & Architectural Rationale

StrokeSpeak adopts a three-tier decoupled client-server architecture:

```
[ Client Layer ]              [ Application Layer ]            [ Persistence Layer ]
React 19 + Tailwind CSS <---> FastAPI + Uvicorn (REST API) <---> MySQL 8.0 Database
(DOM Canvas & Web Audio)      (Pydantic v2 & Vector Math)      (ACID Transactions)
```

## 3.1 Client Layer: React 19 & Tailwind CSS
- **React 19**: Selected for its declarative component model, efficient virtual DOM diffing, and support for reactive state synchronization across the Learning Studio, Drawing Canvas, and Analytics Dashboard.
- **Tailwind CSS**: Employs utility-first styling to ensure fluid, zero-overflow responsive design across desktop viewports (1280px) and mobile devices (390px).
- **HTML5 Canvas API**: Intercepts native DOM pointer events (`pointerdown`, `pointermove`, `pointerup`) to record high-resolution coordinate vectors without raster latency.
- **Web Audio API**: Manages client-side microphone capture and local audio playback via `MediaRecorder` without uploading uncompressed audio blobs to the cloud.

## 3.2 Application Layer: FastAPI & Uvicorn
- **FastAPI (0.143.2)**: An asynchronous Python web framework providing high throughput, native ASGI concurrency via Uvicorn (0.54.0), and automated OpenAPI/Swagger documentation generation.
- **Pydantic v2**: Enforces strict compile-time and runtime data validation on all JSON request/response payloads.
- **Pure-Vector Algorithmic Engine**: Vector processing is executed using native Python mathematical operations, eliminating bloated machine learning runtimes.

## 3.3 Persistence Layer: MySQL 8.0
- **MySQL 8.0**: Chosen for its robust ACID transactional compliance, relational foreign-key integrity constraints, and optimized B-tree indexing for low-latency queries across learners, curriculum lessons, and attempt logs.

---

# Chapter 4: Database Design

The StrokeSpeak database consists of six core relational tables:

```
+---------------+       +--------------------+       +--------------------+
|   languages   |<------|     characters     |<------|  learning_lessons  |
+---------------+       +--------------------+       +--------------------+
        ^                                                       ^
        |                                                       |
+---------------+       +--------------------+       +--------------------+
|     users     |------>|  practice_attempts |       |  lesson_progress   |
+---------------+       +--------------------+       +--------------------+
```

## 4.1 Schema Definitions
1. **`users`**:
   - `id` (INT, PK, Auto-Increment)
   - `name` (VARCHAR(100), Not Null)
   - `email` (VARCHAR(255), Unique, Not Null)
   - `password_hash` (VARCHAR(255), Not Null; placeholder hash in demo/testing)
   - `created_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP)
2. **`languages`**:
   - `id` (INT, PK, Auto-Increment)
   - `name` (VARCHAR(50), Unique)
   - `script_code` (VARCHAR(20), Unique; e.g. `ja-hiragana`, `sa-devanagari`, `ta`, `zh-hans`)
3. **`characters`**:
   - `id` (INT, PK, Auto-Increment)
   - `language_id` (INT, FK -> `languages.id`)
   - `character_text` (VARCHAR(10))
   - `stroke_count` (INT)
   - `reference_strokes` (JSON / TEXT: Vector coordinates and KanjiVG SVG definitions)
4. **`learning_lessons`**:
   - `id` (INT, PK, Auto-Increment)
   - `language_id` (INT, FK -> `languages.id`)
   - `character_id` (INT, FK -> `characters.id`, Nullable for word-only lessons)
   - `level` (VARCHAR(20); 'Foundation', 'Beginner', 'Elementary', 'Advanced')
   - `unit_number` (INT)
   - `lesson_order` (INT)
   - `title` (VARCHAR(100))
   - `pronunciation` (VARCHAR(100))
   - `meaning` (VARCHAR(255))
5. **`lesson_progress`**:
   - `id` (INT, PK, Auto-Increment)
   - `user_id` (INT, FK -> `users.id`)
   - `lesson_id` (INT, FK -> `learning_lessons.id`)
   - `status` (VARCHAR(20); 'completed', 'in_progress')
   - `score` (FLOAT)
   - `completed_at` (TIMESTAMP)
6. **`practice_attempts`**:
   - `id` (INT, PK, Auto-Increment)
   - `user_id` (INT, FK -> `users.id`)
   - `character_id` (INT, FK -> `characters.id`)
   - `handwriting_score` (FLOAT)
   - `stroke_order_score` (FLOAT)
   - `feedback` (TEXT)
   - `created_at` (TIMESTAMP)

**Current database snapshot (2026-11-21):** users 4, languages 12, characters 250, learning lessons 394, lesson progress 17, practice attempts 132; 809 total rows. Public lesson total is 203; 191 legacy lessons remain hidden. Per-learner counts and validation status are in [CURRENT_PROJECT_STATUS.md](CURRENT_PROJECT_STATUS.md).

> [!NOTE]
> **Privacy and Data Security**: Database exports, `.env` files, access tokens, and password hashes must not be published. The learner frontend uses signed 8-hour Bearer tokens, and personal attempt/progress/quiz routes enforce token ownership. Shared course/reference changes require an account ID in `STROKESPEAK_ADMIN_USER_IDS`. This is still a local project implementation; HTTPS, token refresh/revocation, rate limits, account recovery, and live account-flow validation remain before production use.

---

# Chapter 5: API Architecture & Endpoints

The API is documented in [API_OVERVIEW.md](API_OVERVIEW.md) and interactive via `/docs`. The live OpenAPI document currently exposes 29 paths, including admin-only quiz preview and non-persistent quiz grading. Major route groups include:
- **System**: `GET /api/v1/health` (Service state and DB ping).
- **Languages**: `GET /api/v1/languages` (Public script list; legacy scripts excluded).
- **Curriculum**: `GET /api/v1/lessons?language_id={id}` (Hierarchical level/unit/order queries).
- **Characters**: `GET /api/v1/characters/{id}` and `GET /api/v1/characters/{id}/reference-strokes`.
- **Progress Tracking**: `GET /api/v1/lesson-progress?user_id={id}` and `POST /api/v1/lesson-progress`.
- **Practice Evaluation**: `POST /api/v1/practice-attempts` (Receives stroke arrays, executes geometric evaluation, logs score).

---

# Chapter 6: Implementation of System Modules

## 6.1 Interactive Stroke Order Guide
The stroke guide loads normalized point paths and optional source SVG paths from `characters.reference_strokes` and `characters.reference_strokes_svg`. Japanese Kana uses 92 KanjiVG-attributed paths. Six Sanskrit vowel paths from Lipi and ten Chinese starter paths from `hanzi-writer-data` have recorded licenses but await qualified instructor review. Five other Sanskrit and twelve Tamil paths are unverified. Changed canvas drafts are backed up and marked unverified. An admin-only review form stores the cited standard, reviewer attestation, and a fingerprint of the exact geometry; tutorial-video release requires a matching approved fingerprint.

## 6.2 Responsive Vector Drawing Canvas
Rather than saving bitmap images, the drawing canvas records an array of stroke objects:
```json
[
  {
    "stroke_number": 1,
    "points": [{"x": 120.5, "y": 85.0, "time": 1700000000}, ...]
  }
]
```
This data structure captures temporal stroke sequence and velocity without the computational overhead of image binarization.

## 6.3 Algorithmic Assessment Engine
Handwriting evaluation is performed mathematically in four stages:
1. **Bounding Box Normalization**: Both reference and learner strokes are shifted and scaled to a uniform $[0, 100] \times [0, 100]$ coordinate space:
   $$x' = \frac{x - x_{\min}}{x_{\max} - x_{\min}} \times 100, \quad y' = \frac{y - y_{\min}}{y_{\max} - y_{\min}} \times 100$$
2. **Point Resampling**: Strokes are resampled into $N$ equidistant points along their cumulative arc length.
3. **Spatial Distance Scoring**: The average Euclidean distance $\bar{d}$ between positionally paired points $(p_i, q_i)$ is computed:
   $$\text{Score}_{\text{shape}} = \max\left(0, 100 - \frac{\bar{d}}{\alpha}\right)$$
4. **Directional Vector Cosine Verification**: For each stroke, the start-to-end displacement vector $\vec{v} = p_{\text{end}} - p_{\text{start}}$ is evaluated against the reference vector $\vec{u}$:
   $$\cos(\theta) = \frac{\vec{v} \cdot \vec{u}}{\|\vec{v}\| \|\vec{u}\|}$$
   If $\cos(\theta) < 0$ (drawing in reverse direction $> 90^\circ$), the stroke order component drops to zero.

---

# Chapter 7: Testing & Empirical Results

> [!NOTE]
> **Synthetic Trace & Human Drawing Disclosure**: Automated scoring benchmarks below were generated using **synthetic coordinate traces** derived mathematically from reference stroke vectors (HANDOFF_REPORT.md Sections 8, 9, 10, 20). Freehand drawings made with a mouse by a human hand were recorded in exploratory attempts 93–116 (detailed in Section 7.1 below). This is a small exploratory sample from one person on 5 characters, not an accuracy measure (do not call any of this "accuracy"). Genuinely physical and environment-dependent viva conditions remain marked `[UNVERIFIED]`.

Empirical regression testing recorded in `backend/HANDOFF_REPORT.md` demonstrates the evaluator's performance across controlled geometric transformations (synthetic traces generated from the reference strokes, not human drawings):
- **Baseline Model Alignment**: Submitting perfect reference strokes yields 100 on shape and stroke order (*HANDOFF_REPORT.md Section 20 Table 3, Attempts 56, 59, 62, 65, 68, 71*).
- **Wobble Variants ($\pm 0.015$)**: Random synthetic coordinate jitter yields handwriting 96.35 to 97.12 and order 88.90 to 96.45 (attempts 57, 60, 63, 66, 69, 72) across test Kana (`あ, い, ア, イ, ウ, ノ`) (*HANDOFF_REPORT.md Section 20 Table 3*).
- **Shifted 15% and Scaled to 60%**: handwriting 78.66 to 89.00 and order 84.19 to 89.55 (attempts 58, 61, 64, 67, 70, 73) (*HANDOFF_REPORT.md Section 20 Table 3*).
- **Directional Reversal**: Drawing single-stroke `ノ` in reverse direction causes the stroke-order score to drop to $0.00$ (*HANDOFF_REPORT.md Section 20, Attempt 74*). Drawing two-stroke characters `い` and `ア` with both strokes reversed likewise drops stroke order to $0.00$ (*HANDOFF_REPORT.md Section 20, Attempts 76 & 77*).
- **Multi-Stroke Reversed Sequence**: Reversed or swapped stroke order was measured on human drawings in chunk 4F (attempts 111 and 114: order 16.95 and 28.21); the older synthetic 3-stroke reversal figure of 66.64 predates the direction check and was not re-measured.
- **Historical Angle Cliff Experiment (pre-2026-11-21 scorer)**: The earlier evaluator gave the single-stroke ノ trace an 88.4% order score at 80° variation and 0.0% at 100°. That sharp cutoff was replaced in HANDOFF_REPORT.md Section 57 by arc-length resampled local-tangent comparison with gradual direction weighting. These measurements describe only the earlier implementation; saved historical scores were not recalculated.
- **Cross-Viewport Testing**: Headless Chrome CDP verified `scrollWidth <= innerWidth` across both 1280px Desktop (1265px <= 1280px) and 390px Mobile viewports (*HANDOFF_REPORT.md Section 24.4*).

## 7.1 Human Drawing Test (Exploratory Sample)

> [!NOTE]
> **Exploratory Sample Disclosure**: Earlier tests in this project used synthetic traces generated from reference strokes (adding wobble or shifting); one person then drew these attempts with a mouse. The sample is 24 attempts by one person with a mouse on 5 characters; ids 110-116 are a deliberate careful trace of あ. Results are not an accuracy measure. Do not call any of this "accuracy".

### Recorded Human Mouse Drawing Attempts (IDs 93–116 on Learner 1):

| Attempt ID | Character (Glyph / ID) | Strokes Drawn | Ref Strokes | Handwriting Score | Stroke Order Score | Created At | Pattern / Evaluator Observation |
|---:|:---:|:---:|:---:|:---:|:---:|:---|:---|
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

### Key Analytical Findings:
- Earlier tests in this project used synthetic traces generated from reference strokes (adding wobble or shifting); one person then drew these attempts with a mouse.
- The sample is 24 attempts by one person with a mouse on 5 characters; ids 110-116 are a deliberate careful trace of あ. This is not an accuracy measure.
- Drawings that matched the reference stroke count scored higher on handwriting shape (71.52 to 88.71).
- Chunk 4F compared the stored stroke data with the reference strokes. In attempts 111 and 114 the strokes were drawn in a different order from the reference (111: vertical, vertical, horizontal; 114: vertical, horizontal, loop). Attempt 94 is a best fit for a different order (weaker evidence). Attempt 96 has a zero-length first stroke (a dot) and two diagonal strokes; the cause of the dot is UNVERIFIED. In four traces drawn in the reference order (112, 113, 115, 116) stroke order scored 87.75 to 88.06. Attempt 110 (2 strokes) was not analysed in 4F. This is one person and a tiny sample.
- Pairs of attempts with identical scores (such as 100 and 101, 102 and 103) have identical stored stroke data, so the same drawing was saved twice.
- Do not call any of this "accuracy"; human drawings by one person scored from about 16 to 89 (lowest stroke-order score 16.39, highest handwriting score 88.71); do not promise a score.

---

# Chapter 8: Limitations & Future Scope

As detailed in [docs/LIMITATIONS_AND_FUTURE_SCOPE.md](file:///c:/Users/CHETAN/.vscode/StrokeSpeak/docs/LIMITATIONS_AND_FUTURE_SCOPE.md):
- **Algorithmic Prototype (Not ML)**: The handwriting evaluator is an algorithmic geometric prototype, not a machine learning or CNN classifier. It measures geometric alignment against the chosen reference character; it cannot identify what arbitrary character was drawn.
- **Known Algorithmic Weaknesses**: A plain line can still imitate a simple single-stroke character. Direction mismatch now changes the score gradually instead of using a hard 90-degree cutoff, but the method remains a geometric heuristic. Stroke order is aligned one-to-one by index, so inserted or swapped moving strokes can be penalized harshly. Human observations in attempts 111 and 114 are exploratory, not accuracy measurements. Historical scores were not recalculated after the November 21 scoring change.
- **Audio & Pronunciation Scope**:
  The app records and stores browser audio, then can transcribe it with local Faster-Whisper. The displayed score is normalized transcript similarity, not acoustic or phoneme-level pronunciation assessment. End-to-end microphone validation remains pending for all four tutor groups. Four trained CNN models cover 41 classes (10 Hiragana, 10 Sanskrit, 12 Tamil, and 9 Simplified Chinese); Japanese Katakana has no trained CNN model yet. Sample checks are not accuracy evidence.
- **Reference Stroke Scope**: Japanese Kana paths are attributed to KanjiVG. Six Sanskrit and ten Simplified Chinese starter paths have pinned source/license metadata, but qualified review is pending. Five other Sanskrit and twelve Tamil paths are unverified and must not be presented as authoritative or redistributed. Some characters still have no reference path.
- **Future Scope**: Future work includes stronger multi-stroke insertion/deletion alignment, more robust handling of degenerate strokes, phoneme-level forced alignment, additional reviewed Indic stroke vectors, and genuine learner validation across the full public character set.

---

# Chapter 9: Conclusion

StrokeSpeak successfully demonstrates an end-to-end, multi-script CALL system for non-Latin orthographies. By coupling transparent geometric vector evaluation with relational data persistence and modern responsive web technologies, the platform provides learners with immediate, actionable feedback on their handwriting and penmanship technique.

---

## Data Sources and Attribution

Stroke vector reference data for Japanese Hiragana and Katakana is adapted from the **KanjiVG** project ([https://kanjivg.tagaini.net/](https://kanjivg.tagaini.net/)), authored by Ulrich Apel and contributors. KanjiVG data is distributed under the **Creative Commons Attribution-Share Alike 3.0 Unported (CC BY-SA 3.0)** license. All derivative vector paths maintained in the StrokeSpeak database retain original stroke sequence metadata and attribution.
