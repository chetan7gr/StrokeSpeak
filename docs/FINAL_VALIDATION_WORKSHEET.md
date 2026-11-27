# StrokeSpeak Final Integration Validation Worksheet



**Checkpoint:** 2026-11-22  

**Purpose:** Separate software checks from evidence that requires real learners or qualified language reviewers. Blank rows are intentionally blank; do not fill them with generated traces, typed words, prerecorded clips, or model-generated values.



## Verified automated and technical checks



| Area | Recorded result | What this demonstrates | What it does not demonstrate |

| --- | --- | --- | --- |

| Quiz progression API regression | 39/39 passed (reported regression run) | Tested locked access, lesson prerequisites, failed retry, passing score, correct unlock, attempt history, authorization, and non-persistent administrator preview using isolated test data | A learner completing the flow in the browser |

| Authentication, drawing, and speech API regression | 16/16 passed (reported regression run) | API routes and expected software behavior passed that regression set | Genuine handwriting quality or real microphone quality |

| Video overwrite safety | 8/8 passed (rerun 2026-11-22) | Existing files are protected by default; staged output is validated before publish; failed render/copy leaves working output intact | Linguistic correctness of a video |

| CNN model and sample-image endpoints | 4 model groups loaded; 7/7 sample-image inference calls returned their expected labels | Model registry and inference routes respond for the supplied sample images | Real-user handwriting accuracy or generalization; samples are technical fixtures, not human drawings |
| Video streaming API | All five current lesson URLs returned HTTP 200/video/mp4 and served teacher-static-v2 files. Earlier moving previews, closed-mouth v1 clips, and the old v4 alias remain available. | Current five lesson routes serve their static-teacher files | Full browser playback or instructional correctness |
| Mapped MP4 decoding | 5/5 lesson files decoded (read-only audit) | Each mapped file has decodable video and audio streams | Correct language, stroke convention, voice, diagrams, captions, or pronunciation |

| Frontend production build | Fresh Vite production build passed on 2026-11-22, output directed to system temp | Current frontend source compiled into production assets | Future changes still need a fresh build |

| Browser learner walkthrough | Not completed | No browser flow result is claimed | Login-to-quiz progression in a real UI session |



The earlier Japanese lesson-61 URL ending in female-lipsync-v4 returned HTTP 200/video/mp4 with filename ja_hiragana_2_lesson61_female-lipsync-v5.mp4. This remains a backward-compatible direct route. The baseline audit covered Japanese 61 (あ, v5), Sanskrit 339 (अ), Tamil 55 and 223 (அ, duplicate media), and Simplified Chinese 348 (一). After the user first requested responsive lips in every video and then asked to stop body movement without stopping the lips, all five public lesson records now map to teacher-static-v2 versions. Previous moving videos, the closed-mouth v1 clips, and original media remain intact.

All five current lesson videos use the same 3D-style female tutor with a fixed body position and narration-driven closed, parted, and open mouth poses. Their new filenames end in teacher-static-v2. The tutor's body stays still while lesson-board and stroke demonstrations continue to animate. All five lesson URLs and video routes returned HTTP 200/video/mp4, and every new MP4 decoded audio and video. Microsoft Zira Desktop English narration remains; it is not target-language pronunciation audio.



## Video audit: technical findings and review status



All five currently mapped teacher-static-v2 files use H.264 1280×720 video at 30 fps and AAC stereo audio at 44.1 kHz. Video/audio stream duration differences are 1–21 ms. Pixel comparisons show the teacher's non-mouth region remains fixed apart from encoding variation, while the mouth region changes during narration. Mouth poses follow audio level, not individual phonemes; this does not establish target-language pronunciation accuracy.



There are no separate subtitle streams. English captions are burned into the picture and match the configured English narration scripts. The MP4 metadata does not identify the voice. The latest five renders logged Microsoft Zira Desktop, an English Windows voice; it is not a native pronunciation reference for Japanese, Sanskrit, Tamil, or Mandarin. Do not describe these videos as target-language pronunciation models.



Articulation-stage panels reuse the same generic frontal-mouth and sagittal-tongue drawings for different sounds. They do not represent sound-specific mouth positions. The Chinese /i/ example is a clear mismatch: its configured instruction calls for spread lips/high front articulation while the reused drawing shows a generic open oval.



| Group / lesson | Video content and timing | Linguistic / instructional audit | Release decision |

| --- | --- | --- | --- |

| Japanese, 61 (あ), baseline v5 file | 30.267 s video / 30.262 s audio; historical v4 route still aliases to v5 | The configured three-stroke labels broadly align with the Japanese guide. English narration; handoff reports Zira Desktop. Generic articulation drawings; not a Japanese spoken reference. | Prior Japanese tutorial approval exists, but do not present its English narration as Japanese pronunciation training. Re-review the v5 voice and generic articulation claims. |

| Japanese, 61 (あ), current teacher-static-v2 | 30.267 s video / 30.262 s audio; both streams decoded; lesson API returned HTTP 200/video/mp4; sampled frames show fixed body position with changing speaking mouth poses | Microsoft Zira Desktop English narration; audio-level mouth poses, not Japanese phoneme matching. | Active mapping; native-language and instructional review remain outstanding. |
| Sanskrit, 339 (अ), current teacher-static-v2 | 29.733 s video / 29.712 s audio; both streams decoded; lesson API returned HTTP 200/video/mp4; sampled frames show fixed body position with changing speaking mouth poses | Microsoft Zira Desktop English narration; audio-level mouth poses, not Sanskrit phoneme matching. Configured second-stroke caption says “vertical stem & shirorekha bar,” but its vector is a short rising rightward segment. | Hold pending stroke-path and narration review. |

| Tamil, 55 (அ), current teacher-static-v2 | 32.767 s video / 32.766 s audio; both streams decoded; lesson API returned HTTP 200/video/mp4; sampled frames show fixed body position with changing speaking mouth poses | Microsoft Zira Desktop English narration; audio-level mouth poses, not Tamil phoneme matching. Three vectors match the generator’s own description, but the source path is unverified. | Hold pending qualified Tamil reference review. |

| Tamil, 223 (அ), current teacher-static-v2 | 32.767 s video / 32.766 s audio; both streams decoded; lesson API returned HTTP 200/video/mp4; sampled frames show fixed body position with changing speaking mouth poses | Microsoft Zira Desktop English narration; audio-level mouth poses, not Tamil phoneme matching. This is a separate fresh render of lesson 223. | Hold pending qualified Tamil reference review. |

| Simplified Chinese, 348 (一), current teacher-static-v2 | 25.933 s video / 25.928 s audio; both streams decoded; lesson API returned HTTP 200/video/mp4; sampled frames show fixed body position with changing speaking mouth poses | Microsoft Zira Desktop English narration; audio-level mouth poses, not Mandarin phoneme matching. One left-to-right stroke is consistent with configured Heng; generic articulation diagrams remain unspecific. | Hold pending qualified language/reference review. |



This audit is not a linguistic certification. A readable/decodable MP4 and close stream durations are technical checks, not proof of correct teaching content. The bulk generator also bypasses the per-reference approval workflow; do not use it for release until each applicable reference is approved.



## Genuine handwriting validation — 41 CNN classes



Use the React Canvas and a real person’s own mouse, stylus, or touch drawing. For each character, create a new attempt through the normal learner UI, then copy the attempt ID and values shown by the application/API. Do not seed, synthesize, replay, or transform reference strokes as learner data.



**Existing baseline:** The project reports 1/41 formal target-character validations. The summary available for this checkpoint does not identify which target character and attempt make up that one case. Trace it to a genuine attempt before marking any row complete; do not silently count it against an arbitrary character.



For a future row, “workflow pass” means a genuine drawing was saved and the expected prediction/confidence and shape/order scores were returned. Separately note whether the predicted class equals the drawn target. A workflow pass is not a model-accuracy claim.



| Script group | Target | Attempt ID | CNN prediction / confidence | Shape score | Stroke-order score | Workflow pass/fail | Prediction equals target? / notes |

| --- | --- | --- | --- | --- | --- | --- | --- |

| Japanese Hiragana | あ |  |  |  |  |  |  |

| Japanese Hiragana | い |  |  |  |  |  |  |

| Japanese Hiragana | う |  |  |  |  |  |  |

| Japanese Hiragana | え |  |  |  |  |  |  |

| Japanese Hiragana | お |  |  |  |  |  |  |

| Japanese Hiragana | か |  |  |  |  |  |  |

| Japanese Hiragana | き |  |  |  |  |  |  |

| Japanese Hiragana | く |  |  |  |  |  |  |

| Japanese Hiragana | け |  |  |  |  |  |  |

| Japanese Hiragana | こ |  |  |  |  |  |  |

| Sanskrit Devanagari | अ |  |  |  |  |  |  |

| Sanskrit Devanagari | आ |  |  |  |  |  |  |

| Sanskrit Devanagari | इ |  |  |  |  |  |  |

| Sanskrit Devanagari | ई |  |  |  |  |  |  |

| Sanskrit Devanagari | उ |  |  |  |  |  |  |

| Sanskrit Devanagari | ऊ |  |  |  |  |  |  |

| Sanskrit Devanagari | ए |  |  |  |  |  |  |

| Sanskrit Devanagari | ऐ |  |  |  |  |  |  |

| Sanskrit Devanagari | ओ |  |  |  |  |  |  |

| Sanskrit Devanagari | औ |  |  |  |  |  |  |

| Tamil | அ |  |  |  |  |  |  |

| Tamil | ஆ |  |  |  |  |  |  |

| Tamil | இ |  |  |  |  |  |  |

| Tamil | ஈ |  |  |  |  |  |  |

| Tamil | உ |  |  |  |  |  |  |

| Tamil | ஊ |  |  |  |  |  |  |

| Tamil | எ |  |  |  |  |  |  |

| Tamil | ஏ |  |  |  |  |  |  |

| Tamil | ஐ |  |  |  |  |  |  |

| Tamil | ஒ |  |  |  |  |  |  |

| Tamil | ஓ |  |  |  |  |  |  |

| Tamil | ஔ |  |  |  |  |  |  |

| Simplified Chinese | 一 |  |  |  |  |  |  |

| Simplified Chinese | 二 |  |  |  |  |  |  |

| Simplified Chinese | 三 |  |  |  |  |  |  |

| Simplified Chinese | 人 |  |  |  |  |  |  |

| Simplified Chinese | 大 |  |  |  |  |  |  |

| Simplified Chinese | 口 |  |  |  |  |  |  |

| Simplified Chinese | 日 |  |  |  |  |  |  |

| Simplified Chinese | 月 |  |  |  |  |  |  |

| Simplified Chinese | 山 |  |  |  |  |  |  |



### Human drawing procedure



1. Sign in with a dedicated demo learner account; do not use another learner’s account.

2. Select the script and exact target character from the table.

3. Draw the character yourself in the React Canvas. Avoid pasted images, synthetic paths, automated mouse macros, or reference-trace replay.

4. Submit once. Record the attempt ID, CNN top prediction and confidence, shape score, and stroke-order score exactly as shown. If a value is missing, write “not returned”; do not infer it.

5. Mark workflow pass/fail using the definition above. Separately record target-match yes/no and any visible/API error.

6. Repeat for each target. Keep screenshots or sanitized response excerpts only if they do not reveal credentials or private learner data.



The 41 targets are the four trained model groups only. Japanese Katakana is public for geometric practice but is not one of the 41 trained CNN classes.



## Genuine browser microphone validation — four tutor groups



No actual microphone session was completed for this checkpoint. Current baseline is 0/4. Use a real person speaking into the browser microphone, with the browser permission prompt granted by that person. Do not use typed text, synthesized speech, or a bundled recording. Record exact outputs; transcript similarity is text similarity, not acoustic or phoneme-level pronunciation quality.



| Tutor group | Capture success / format | Expected character + transliteration | Transcript returned | Transcript similarity | Error / limitation / notes |

| --- | --- | --- | --- | --- | --- |

| Japanese Hiragana |  |  |  |  |  |

| Sanskrit Devanagari |  |  |  |  |  |

| Tamil |  |  |  |  |  |

| Simplified Chinese |  |  |  |  |  |



For each group: choose a lesson with a known target, record a real utterance through the in-app microphone, submit it through the normal speech route, and capture the returned transcript and similarity value. Note browser permission failures, device/format errors, language-code behavior, missing model errors, transcription errors, and Sanskrit reference-audio limitations. Do not equate a high similarity value with correct phonetics, accent, tone, aspiration, or formant quality.



## Browser learner walkthrough



Status: **not completed**. The isolated private-browser attempt was stopped because browser-control safety could not verify the current URL. No account, attempt, quiz submission, progress, or microphone permission was changed in that attempt.



When a human tester performs this check, use a dedicated demo account and record pass/fail, screenshots without private details, and any returned IDs for each step:



- [ ] Register/sign in with the dedicated demo account.

- [ ] Select each of the four public tutor groups; confirm hidden languages are absent.

- [ ] Open a lesson and play its correctly mapped tutorial video.

- [ ] Draw a real character and confirm attempt persistence, prediction, shape, and stroke-order feedback.

- [ ] Record a real pronunciation; confirm capture, transcription, and transcript similarity are shown with accurate wording.

- [ ] Complete prerequisite lessons and verify the quiz is unlocked only afterward.

- [ ] Submit a quiz; verify backend score, feedback, attempt history, and correct next-section unlock.

- [ ] Fail a quiz and verify retry is allowed while progress remains locked.

- [ ] Review learner progress and confirm data belongs only to the signed-in test account.



Do not manually delete learner data to clean up. Use disposable test accounts or an isolated transaction/fixture for automated tests.



## Packaging gate



**Do not create the final submission ZIP yet.** The current v10 archive is a checkpoint. Rebuild only after the remaining video/reference review and genuine human validation are either resolved or clearly documented and accepted, Antigravity-owned integration changes are reviewed, a fresh production build and backend/API suite pass, and the browser learner walkthrough is recorded. Exclude .env files, credentials, virtual environments, caches, and user recordings from any eventual archive.

