# StrokeSpeak Presentation Slide Deck (PPT Content & Speaker Notes)

> **Use current data (2026-11-21):** This slide outline contains historical counts and feature descriptions. The verified snapshot is in [CURRENT_PROJECT_STATUS.md](CURRENT_PROJECT_STATUS.md): 809 core-table rows and 203 public lessons (Japanese 128, Sanskrit 29, Tamil 32, Simplified Chinese 14). There are four user rows; two legacy placeholder-hash accounts are disabled. Use a real registered account for the demonstration.

**Presentation Title**: StrokeSpeak: An AI-Powered Multilingual Handwriting and Pronunciation Learning and Assessment Platform  
**Target Duration**: 10 – 12 Minutes  
**Slide Count**: 14 Slides  

---

### Slide 1: Title Slide
- **Title**: StrokeSpeak: An AI-Powered Multilingual Handwriting and Pronunciation Learning and Assessment Platform
- **Subtitle**: Computer-Aided Language Learning (CALL) for Complex Non-Latin Orthographies
- **Student Details**: MCA Final Year Project
- **Key Focus**: Dynamic Stroke Order Validation & Multi-Script Pedagogy
- **Speaker Notes**:
  > "Respected evaluators, welcome to the final presentation for StrokeSpeak. Today, I will demonstrate our platform designed to teach non-Latin handwriting through real-time vector analysis, animated stroke guidance, and structured multi-script curricula."

---

### Slide 2: Problem Statement & Motivation
- **The Non-Latin Challenge**: Asian and Indian scripts require exact stroke order and direction, not just visual shape.
- **Flaws in Existing Apps**: Commercial apps focus on flashcards and pixel overlap, ignoring penmanship dynamics.
- **The Feedback Gap**: Self-learners lack expert native instructors to observe and correct stroke sequence errors.
- **Resource Constraints**: Traditional deep learning classifiers are opaque, heavy, and lack granular stroke diagnostic feedback.
- **Speaker Notes**:
  > "Learning non-Latin scripts like Japanese Kana or Devanagari is not just about the final shape; it is about the stroke sequence. Existing platforms fail here because they treat drawing as a static image, ignoring stroke order and direction entirely."

---

### Slide 3: Project Objectives & Scope
- **Interactive Stroke Guidance**: Dynamic vector animation showing exact order, direction, and trajectory.
- **Algorithmic Evaluation Engine**: Mathematical scoring of handwriting geometry and directional penmanship.
- **Public Script Scope**: Japanese (Hiragana + Katakana, 128 lessons), Sanskrit (Devanagari, 26), Tamil (32), and Simplified Chinese (14).
- **Integrated Feedback**: Audio reference streaming, local voice recording, and live learner progress analytics.
- **Speaker Notes**:
  > "Our objective was to build a full-stack, responsive platform with four public writing systems, transparent geometric evaluation, and structured lesson progress stored in a relational database."

---

### Slide 4: System Architecture
- **Three-Tier Architecture**: React 19 Frontend $\leftrightarrow$ FastAPI Python Backend $\leftrightarrow$ MySQL 8.0 Database.
- **Client Layer**: Responsive Tailwind UI, HTML5 DOM Canvas API, and Web Audio API.
- **Server Layer**: FastAPI (29 OpenAPI paths), Pydantic v2 validation, MySQL persistence, geometric scoring, CNN inference, and local Faster-Whisper routes.
- **Database Layer**: Fully normalized relational schema with ACID transactional guarantees (as of 2026-11-17 18:10: 112 practice attempts, 746 total rows (regenerate with backend\scripts\show_table_counts.py)).
- **Speaker Notes**:
  > "StrokeSpeak is architected in three clean tiers. The client captures DOM coordinate vectors, FastAPI validates and evaluates the geometry asynchronously, and MySQL 8.0 maintains ACID persistence for all learning records."

---

### Slide 5: Database Design & Relational Integrity
- **Six Core Relational Tables**: `users`, `languages`, `characters`, `learning_lessons`, `lesson_progress`, `practice_attempts`.
- **Integrity Constraints**: Foreign keys enforce curriculum hierarchy and user attempt linkage.
- **Learner Profiles**: Learner 1 has historical test data; Learner 2 has 17 practice attempts; Learner 3 currently has 0 attempts and 0 lesson progress.
- **Security & Privacy**: Strict deletion freeze; legacy scripts hidden from public queries via allowlists. Export contains placeholder password hashes.
- **Speaker Notes**:
  > "At the current checkpoint (2026-11-21), MySQL contains 809 rows across the six core tables and 203 public lessons across the four tutor groups. Four user rows exist; two legacy placeholder-hash accounts are disabled, and authenticated routes bind learner data to the signed-in account."

---

### Slide 6: Curriculum & Pedagogical Design
- **Hierarchical Structure**: Languages $\rightarrow$ Levels (Foundation, Beginner) $\rightarrow$ Units $\rightarrow$ Ordered Lessons.
- **Japanese Course**: 128 lessons in one combined Hiragana/Katakana tutor (Foundation 100, Beginner 25, Elementary 2, Advanced 1).
- **Sanskrit & Tamil**: Sanskrit 29 lessons; Tamil 32 lessons, with uneven level depth.
- **Simplified Chinese**: 14 lessons (9 Foundation, 5 Beginner); higher levels remain future curriculum work.
*(The database has 394 learning_lessons rows; 203 are tagged to public script rows and 191 legacy lessons are hidden.)*
- **Speaker Notes**:
  > "Curricula progress naturally from foundational glyphs to vocabulary words and short sentences. In Tamil, for instance, everyday words like 'vanakkam' and 'nanri' precede sentence construction."

---

### Slide 7: Interactive Stroke Animation (KanjiVG)
- **Vector Path Rendering**: Native SVG path rendering instead of static video files.
- **Data Source**: 92 Japanese Kana vector paths sourced from open-source KanjiVG (CC BY-SA 3.0).
- **Dynamic Controls**: Replay button with DOM key reset for seamless repetition.
- **Provenance Disclosure**: Japanese Kana guides are attributed to KanjiVG. Six Sanskrit and ten Simplified Chinese starter paths have pinned source/license data but await instructor review; five other Sanskrit and twelve Tamil paths remain unverified.
- **Speaker Notes**:
  > "Japanese Kana guides render attributed KanjiVG vectors. Some Indic and Chinese characters have draft paths with unverified provenance, so the app marks them as drafts and does not present them as authoritative."

---

### Slide 8: Drawing Canvas & Vector Capture
- **DOM Pointer Tracking**: Captures continuous $(x, y)$ coordinates and millisecond timestamps.
- **Direct Vector Representation**: Avoids image rasterization, pixel noise, and heavy OpenCV dependencies.
- **Responsive Geometry**: Standardized 700x320 canvas scaling cleanly down to 390px mobile screens.
- **Multi-Stroke Segmentation**: Automatically partitions discrete mouse/touch lifts into ordered strokes.
- **Speaker Notes**:
  > "Rather than converting drawings to bitmaps, our canvas captures clean vector coordinate streams. This preserves stroke sequence, timing, and velocity with lightweight, zero-latency processing."

---

### Slide 9: Algorithmic Handwriting Evaluator
- **Bounding-Box Normalization**: Scales user drawing to uniform $[0, 100] \times [0, 100]$ space (scale/shift invariant).
- **Point Resampling**: Equidistant arc-length interpolation enables 1-to-1 point pairing.
- **Decoupled Scoring**: Computes Shape Accuracy and Stroke Order Correctness independently.
- **Directional Cosine Check**: Computes start-to-end vector cosine; negative alignment heavily penalizes score.
- **Speaker Notes**:
  > "Our evaluator is an algorithmic vector engine. It normalizes coordinates, pairs points, and computes spatial distance and vector cosines. Reversing a stroke's direction drops the stroke order score to zero."

---

### Slide 10: Empirical Testing & Robustness
- **Synthetic Trace Testing**: Synthetic traces generated from the reference strokes, not human drawings (*HANDOFF_REPORT.md Section 20 Table 3*):
  - Model traces: 100
  - Wobble variants ($\pm 0.015$): handwriting 96.35 to 97.12 and order 88.90 to 96.45 (*Attempts 57, 60, 63, 66, 69, 72*).
  - Shifted 15% and scaled to 60%: handwriting 78.66 to 89.00 and order 84.19 to 89.55 (*Attempts 58, 61, 64, 67, 70, 73*).
  - Reverse direction penalty: Single-stroke `ノ` and two-stroke `い`, `ア` reversed drop order to 0.00 (*Attempts 74, 76, 77*). Reversed or swapped stroke order was measured on human drawings in chunk 4F (attempts 111 and 114: order 16.95 and 28.21); the older synthetic 3-stroke reversal figure of 66.64 predates the direction check and was not re-measured.

#### Human Drawing Test (Exploratory Sample):
- **Sample Overview**: The earlier tests used synthetic traces generated from the reference strokes; one person then drew with a mouse. The sample is 24 attempts by one person with a mouse on 5 characters; ids 110-116 are a deliberate careful trace of あ. Results are not an accuracy measure. Do not call any of this "accuracy".

| Attempt ID | Character (Glyph / ID) | Strokes Drawn | Ref Strokes | Handwriting Score | Stroke Order Score | Created At | Pattern / Observation |
|---:|:---:|:---:|:---:|:---:|:---:|:---|:---|
| 93 | あ (ID 2) | 4 | 3 | 64.50 | 37.16 | 2026-11-17 16:23:11 | Extra stroke drawn |
| 94 | あ (ID 2) | 3 | 3 | 87.72 | 16.60 | 2026-11-17 16:23:36 | Right stroke count; high shape, strict order drop |
| 95 | あ (ID 2) | 2 | 3 | 51.04 | 16.39 | 2026-11-17 16:24:01 | Missing stroke drawn |
| 96 | あ (ID 2) | 3 | 3 | 79.97 | 41.01 | 2026-11-17 16:24:24 | Right stroke count; moderate order match |
| 97 | あ (ID 2) | 4 | 3 | 51.15 | 16.44 | 2026-11-17 16:24:48 | Extra stroke drawn |
| 98 | あ (ID 2) | 5 | 3 | 53.04 | 52.97 | 2026-11-17 16:35:31 | Multiple extra strokes |
| 99 | い (ID 28) | 2 | 2 | 71.52 | 77.14 | 2026-11-17 16:37:27 | Right stroke count; balanced shape & order |
| 100 | う (ID 29) | 2 | 2 | 80.11 | 79.71 | 2026-11-17 16:38:25 | Right stroke count; strong match on both |
| 101 | う (ID 29) | 2 | 2 | 80.11 | 79.71 | 2026-11-17 16:39:00 | Identical score to 100 (identical stored stroke data, so the same drawing was saved twice) |
| 102 | え (ID 30) | 4 | 2 | 41.14 | 31.78 | 2026-11-17 16:39:49 | Fragmented sequence (4 vs 2 ref strokes) |
| 103 | え (ID 30) | 4 | 2 | 41.14 | 31.78 | 2026-11-17 16:40:01 | Identical score to 102 (identical stored stroke data, so the same drawing was saved twice) |
| 104 | か (ID 31) | 9 | 3 | 26.69 | 16.44 | 2026-11-17 16:54:24 | Multi-stroke scribble test |
| 105 | か (ID 31) | 3 | 3 | 87.14 | 71.45 | 2026-11-17 16:55:07 | Right stroke count; high shape & solid order |
| 106 | か (ID 31) | 3 | 3 | 86.80 | 71.23 | 2026-11-17 16:55:32 | Right stroke count; consistent high score |
| 107 | か (ID 31) | 3 | 3 | 87.13 | 55.94 | 2026-11-17 16:56:15 | Right stroke count; good shape, order partly matched |
| 108 | か (ID 31) | 3 | 3 | 79.41 | 63.90 | 2026-11-17 16:56:55 | Right stroke count; consistent shape |
| 109 | か (ID 31) | 2 | 3 | 41.89 | 26.15 | 2026-11-17 16:57:11 | Incomplete drawing (2 of 3 ref strokes) |
| 110 | あ (ID 2) | 2 | 3 | 56.82 | 47.67 | 2026-11-17 17:52:52 | Deliberate trace of あ (2 of 3 reference strokes; not analysed in 4F) |
| 111 | あ (ID 2) | 3 | 3 | 88.71 | 16.95 | 2026-11-17 17:53:34 | Deliberate trace of あ (drawn in wrong order: vertical, vertical, horizontal) |
| 112 | あ (ID 2) | 3 | 3 | 88.22 | 88.01 | 2026-11-17 17:54:03 | Deliberate trace of あ (drawn in reference order: horizontal, vertical, loop) |
| 113 | あ (ID 2) | 3 | 3 | 88.10 | 87.75 | 2026-11-17 17:54:25 | Deliberate trace of あ (drawn in reference order: horizontal, vertical, loop) |
| 114 | あ (ID 2) | 3 | 3 | 87.74 | 28.21 | 2026-11-17 17:54:47 | Deliberate trace of あ (drawn in wrong order: vertical, horizontal, loop) |
| 115 | あ (ID 2) | 3 | 3 | 88.02 | 87.78 | 2026-11-17 17:55:20 | Deliberate trace of あ (drawn in reference order: horizontal, vertical, loop) |
| 116 | あ (ID 2) | 3 | 3 | 87.86 | 88.06 | 2026-11-17 17:55:55 | Deliberate trace of あ (drawn in reference order: horizontal, vertical, loop) |

- **Key Observations**:
  - Drawings with the right stroke count scored higher on handwriting (71.52 to 88.71).
  - Chunk 4F compared the stored stroke data with the reference strokes. In attempts 111 and 114 the strokes were drawn in a different order from the reference (111: vertical, vertical, horizontal; 114: vertical, horizontal, loop). Attempt 94 is a best fit for a different order (weaker evidence). Attempt 96 has a zero-length first stroke (a dot) and two diagonal strokes; the cause of the dot is UNVERIFIED. In four traces drawn in the reference order (112, 113, 115, 116) stroke order scored 87.75 to 88.06. Attempt 110 (2 strokes) was not analysed in 4F. This is one person and a tiny sample.
  - Pairs with identical scores (ids 100/101 and 102/103) have identical stored stroke data, so the same drawing was saved twice.
  - Do not call any of this "accuracy"; human drawings by one person scored from about 16 to 89 (lowest stroke-order score 16.39, highest handwriting score 88.71); do not promise a score.
- **Speaker Notes**:
  > "We tested our evaluator with real mouse drawings from one person across 5 characters (sample is 24 attempts; ids 110-116 are a deliberate careful trace of あ). Drawings with matching stroke counts achieve higher shape scores (71.52 to 88.71), while stroke order is strict and reflects directional differences. Submitting without clearing canvas creates duplicate rows. human drawings by one person scored from about 16 to 89 (lowest stroke-order score 16.39, highest handwriting score 88.71); do not promise a score."

---

### Slide 11: Audio Reference & Pronunciation Honesty
- **Pronunciation Status**: Browser audio recording, persistence, and local Faster-Whisper transcription are implemented; speech score is normalized transcript similarity, not acoustic or phoneme-level analysis. Real microphone validation remains pending for all four groups.
- **Reference Voice**: Cloud-synthesized native audio streaming via gTTS; Sanskrit openly labeled as Hindi synthetic voice approximation.
- **Speaker Notes**:
  > "The app records and transcribes speech locally. The score compares the recognized transcript with the target text; it does not yet measure phoneme-level pronunciation. We still need genuine microphone validation for each tutor group."

---

### Slide 12: Live Demonstration Highlights
- **Target URL**: `http://localhost:5173/`; sign in or create a new account. A new account starts with no saved practice history.
- **Japanese Hiragana 'あ'**: Dynamic replay, correct drawing submission, and score verification.
- **Error Detection Demo**: Deliberately reversed stroke demonstrates directional penalty drop (0.0%).
- **Progress Tracking**: Real-time progress bar update and attempt history logging in MySQL.
- **Speaker Notes**:
  > "In our live demonstration, we sign in, trace a Japanese character, examine the geometric prototype feedback, and save progress to the authenticated learner account."

---

### Slide 13: Technical Limitations & Viva Transparency
- **Algorithmic Prototype vs. ML**: System evaluates similarity against selected reference, not open character classification.
- **Audio & Pronunciation Scope**: Local recording and Faster-Whisper transcription exist, but score is text similarity rather than phoneme-level analysis; microphone validation is pending. Four trained CNN models cover 41 classes; Katakana remains untrained, and generalization/accuracy is not established.
- **Hard Cosine Threshold**: Direction check switches sharply at $90^\circ$ ($\cos(\theta) < 0$; 80° gives 88.4%, 100° gives 0.0%).
- **Known Weaknesses**: Single-stroke characters (e.g. `ノ`) can be imitated by a plain line; Reversed or swapped stroke order was measured on human drawings in chunk 4F (attempts 111 and 114: order 16.95 and 28.21); the older synthetic 3-stroke reversal figure of 66.64 predates the direction check and was not re-measured.
- **Speaker Notes**:
  > "We maintain complete academic honesty: this is an algorithmic vector prototype, not a CNN. It evaluates drawing fidelity against the chosen reference character, ensuring complete transparency during viva defense."

---

### Slide 14: Conclusion & Future Scope
- **Key Accomplishments**: Working multilingual full-stack prototype, 203 public lessons, API/database persistence, KanjiVG Kana guides, four trained CNN models across 41 classes, and one ready tutorial video. See current status for remaining validation and limitations.
- **Future Enhancements**:
  1. Multi-dimensional Dynamic Time Warping (DTW) for complex multi-stroke alignments.
  2. Acoustic forced-alignment models (Kaldi/MFA) for phoneme-level pronunciation diagnosis.
  3. Expansion of Indic vector stroke datasets for Devanagari and Tamil.
- **Thank You**: Questions and Answers.
- **Speaker Notes**:
  > "StrokeSpeak proves that effective orthographic guidance can be achieved with transparent, lightweight vector algorithms. Thank you, and I look forward to your questions."
