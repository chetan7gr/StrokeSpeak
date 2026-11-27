"""Script-aware local tutorial video rendering from verified database strokes."""

import io
import math
import os
import tempfile
import time
from pathlib import Path

import av
import cv2
from gtts import gTTS
import numpy as np

from app.ml.video_generator import (
    SenseiKaiRenderer, SmartboardRenderer, _synthesize_windows_female_voice,
)

BACKEND_DIR = Path(__file__).resolve().parents[2]
VIDEOS_DIR = BACKEND_DIR / "static" / "videos"

PUBLIC_SCRIPTS = {
    "ja-hiragana": ("JAPANESE HIRAGANA", "ja"),
    "sa-devanagari": ("SANSKRIT DEVANAGARI", "hi"),
    "ta": ("TAMIL", "ta"),
    "zh-hans": ("SIMPLIFIED CHINESE", "zh-CN"),
}


def _render_frame(stage, stroke_index, stroke_fraction, caption, frame_index,
                  strokes, script_title, target_label, pronunciation_label, mouth_open, source_label):
    width, height = 1280, 720
    image = np.full((height, width, 3), (242, 245, 250), dtype=np.uint8)
    cv2.rectangle(image, (0, 670), (width, height), (215, 220, 228), -1)
    cv2.line(image, (0, 670), (width, 670), (180, 190, 205), 2, cv2.LINE_AA)

    board = (390, 40, 1240, 630)
    bx1, by1, bx2, by2 = board
    center_x = (bx1 + bx2) // 2
    center_y = (by1 + by2) // 2 + 18
    cv2.rectangle(image, (bx1 - 6, by1 - 6), (bx2 + 6, by2 + 6), (30, 35, 45), -1)
    cv2.rectangle(image, (bx1, by1), (bx2, by2), (20, 26, 38), -1)
    cv2.rectangle(image, (bx1, by1), (bx2, by2), (99, 102, 241), 3, cv2.LINE_AA)
    cv2.rectangle(image, (bx1, by1), (bx2, by1 + 52), (28, 38, 56), -1)
    cv2.putText(image, "STROKESPEAK ACADEMY", (bx1 + 24, by1 + 34),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (165, 180, 252), 2, cv2.LINE_AA)
    cv2.putText(image, script_title, (bx1 + 360, by1 + 34),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (226, 232, 240), 2, cv2.LINE_AA)
    cv2.rectangle(image, (bx2 - 130, by1 + 10), (bx2 - 18, by1 + 42), (99, 102, 241), -1)
    cv2.putText(image, pronunciation_label[:14], (bx2 - 120, by1 + 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)

    pointer_target = None
    stroke_count = len(strokes)
    if stage == "intro":
        cv2.putText(image, "TODAY'S CHARACTER", (center_x - 170, by1 + 145),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (165, 180, 252), 2, cv2.LINE_AA)
        box = (center_x - 125, center_y - 105, center_x + 125, center_y + 145)
        SmartboardRenderer.draw_character_strokes(image, strokes, box,
            stroke_color=(255, 255, 255), thickness=12, show_badges=False)
        cv2.putText(image, target_label[:35], (center_x - 170, by2 - 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.78, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(image, f"{stroke_count} REFERENCE DATASET STROKES", (center_x - 190, by2 - 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (251, 191, 36), 2, cv2.LINE_AA)
        if source_label:
            cv2.putText(image, source_label[:54], (bx1 + 20, by2 - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.43, (210, 220, 235), 1, cv2.LINE_AA)

    elif stage == "sound":
        cv2.putText(image, "LISTEN TO THE TARGET SOUND", (center_x - 230, by1 + 128),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, (165, 180, 252), 2, cv2.LINE_AA)
        cv2.putText(image, target_label[:35], (center_x - 180, by1 + 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.74, (226, 232, 240), 2, cv2.LINE_AA)
        cv2.putText(image, "Listen, then repeat the sound.", (center_x - 190, by2 - 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        for bar in range(19):
            amplitude = 10 + int(35 * abs(math.sin(frame_index * 0.11 + bar * 0.55)))
            x = center_x - 245 + bar * 27
            cv2.line(image, (x, center_y - amplitude), (x, center_y + amplitude),
                     (99, 102, 241), 8, cv2.LINE_AA)

    elif stage == "stroke":
        box_size = 390
        box = (center_x - box_size // 2, center_y - box_size // 2,
               center_x + box_size // 2, center_y + box_size // 2)
        cv2.rectangle(image, (center_x - 260, by1 + 66), (center_x + 260, by1 + 104), (28, 38, 56), -1)
        cv2.putText(image, f"STROKE {stroke_index + 1} OF {stroke_count}: FOLLOW THE HIGHLIGHTED PATH",
                    (center_x - 245, by1 + 91), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
                    (165, 180, 252), 2, cv2.LINE_AA)
        cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (16, 22, 34), -1)
        cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (51, 65, 85), 2, cv2.LINE_AA)
        cv2.line(image, (center_x, box[1] + 8), (center_x, box[3] - 8), (35, 45, 65), 1, cv2.LINE_AA)
        cv2.line(image, (box[0] + 8, center_y), (box[2] - 8, center_y), (35, 45, 65), 1, cv2.LINE_AA)
        SmartboardRenderer.draw_character_strokes(image, strokes, box,
            progress_stroke_idx=stroke_index, progress_frac=stroke_fraction,
            stroke_color=(255, 255, 255), thickness=10, show_badges=True)
        pointer_target = (box[0] + 38, center_y)

    else:
        cv2.putText(image, "REFERENCE STROKE ORDER COMPLETE", (center_x - 260, by1 + 145),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.82, (52, 211, 153), 2, cv2.LINE_AA)
        box = (center_x - 125, center_y - 105, center_x + 125, center_y + 145)
        SmartboardRenderer.draw_character_strokes(image, strokes, box,
            stroke_color=(255, 255, 255), thickness=12, show_badges=True)
        cv2.putText(image, f"NOW PRACTISE: {target_label[:25]}", (center_x - 210, by2 - 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (251, 191, 36), 2, cv2.LINE_AA)

    pose = {"intro": "welcome", "sound": "point", "stroke": "point", "complete": "encourage"}.get(stage, "welcome")
    SenseiKaiRenderer.render(image, cx=200, cy=590, pose=pose,
        mouth_open=mouth_open,
        eye_blink=(frame_index % 100) in range(88, 95),
        frame_idx=frame_index, pointer_target=pointer_target)

    if caption:
        caption_width = min(1080, max(420, len(caption) * 13 + 60))
        mid = width // 2
        cv2.rectangle(image, (mid - caption_width // 2, 650),
                      (mid + caption_width // 2, 704), (15, 20, 30), -1)
        cv2.rectangle(image, (mid - caption_width // 2, 650),
                      (mid + caption_width // 2, 704), (99, 102, 241), 2, cv2.LINE_AA)
        (text_width, _), _ = cv2.getTextSize(caption, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 2)
        cv2.putText(image, caption, (mid - text_width // 2, 684),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)
    return image


def generate_script_demo_video(lesson, output_path=None):
    """Render a non-overwriting demo using the lesson's saved character strokes."""
    script_code = lesson["script_code"]
    if script_code not in PUBLIC_SCRIPTS:
        raise ValueError(f"Script is outside the approved public scope: {script_code}")
    strokes = lesson["stroke_data"]
    if isinstance(strokes, str):
        import json
        strokes = json.loads(strokes)
    if not isinstance(strokes, list) or not strokes:
        raise ValueError("This character has no reference strokes.")
    for stroke in strokes:
        if not isinstance(stroke, list) or len(stroke) < 2:
            raise ValueError("Each reference stroke must have at least two points.")
        for point in stroke:
            x, y = float(point["x"]), float(point["y"])
            if not (0 <= x <= 1 and 0 <= y <= 1):
                raise ValueError("Reference coordinates must be normalized from 0 to 1.")

    title, native_tts_lang = PUBLIC_SCRIPTS[script_code]
    reference_metadata = lesson.get("reference_metadata") or {}
    if isinstance(reference_metadata, str):
        import json
        reference_metadata = json.loads(reference_metadata)
    source_label = str(reference_metadata.get("video_credit") or "")
    pronunciation = str(lesson.get("pronunciation_text") or lesson["character_text"])
    ascii_pronunciation = (pronunciation.encode("ascii", "ignore").decode("ascii") or "sound")
    target_label = f"{title.title()}: {ascii_pronunciation}"
    safe_lesson_title = f"{title} TUTORIAL"
    segments = [
        {"stage": "intro", "caption": f"LEARN {target_label.upper()}"[:82],
         "speech": f"Welcome to StrokeSpeak. Today we learn {title.title()}. This character is read as {ascii_pronunciation}.",
         "lang": "en"},
        {"stage": "sound", "caption": f"LISTEN AND REPEAT: {ascii_pronunciation.upper()}",
         "speech": str(lesson["character_text"]), "lang": native_tts_lang},
    ]
    for idx in range(len(strokes)):
        number = idx + 1
        segments.append({
            "stage": "stroke", "stroke_index": idx,
            "caption": f"STROKE {number} OF {len(strokes)}: FOLLOW THE HIGHLIGHTED PATH",
            "speech": f"Stroke {number} of {len(strokes)}. Follow the highlighted path.",
            "lang": "en",
        })
    segments.append({
        "stage": "complete", "caption": "NOW PRACTISE THE CHARACTER",
        "speech": f"All {len(strokes)} reference strokes are complete. Now practise drawing and speaking.",
        "lang": "en",
    })

    audio_chunks, timelines, current_time = [], [], 0.0
    english_segments = [segment for segment in segments if segment["lang"] == "en"]
    try:
        english_audio, selected_voice = _synthesize_windows_female_voice(english_segments)
        print(f"Tutorial narration voice: {selected_voice}")
    except Exception as voice_error:
        print(f"Windows female voice unavailable; using gTTS for English narration: {voice_error}")
        english_audio = None
    english_audio_index = 0

    for segment in segments:
        if segment["lang"] == "en" and english_audio is not None:
            audio_file = io.BytesIO(english_audio[english_audio_index])
            audio_format = "wav"
            english_audio_index += 1
        else:
            audio_file = io.BytesIO()
            gTTS(text=segment["speech"], lang=segment["lang"], slow=False).write_to_fp(audio_file)
            audio_file.seek(0)
            audio_format = "mp3"
        decoded = []
        with av.open(audio_file, format=audio_format) as audio_container:
            stream = audio_container.streams.audio[0]
            resampler = av.AudioResampler(format="s16", layout="stereo", rate=44100)
            for audio_frame in audio_container.decode(stream):
                for frame in resampler.resample(audio_frame):
                    decoded.append(frame.to_ndarray())
        if not decoded:
            raise RuntimeError(f"Audio narration was empty for {segment['stage']} segment.")
        interleaved = np.concatenate(decoded, axis=1)
        samples = interleaved.reshape(2, -1, order="F")
        duration = samples.shape[1] / 44100.0
        audio_chunks.append(samples)
        timelines.append({**segment, "start": current_time, "end": current_time + duration, "duration": duration})
        current_time += duration

    full_audio = np.concatenate(audio_chunks, axis=1)
    total_samples = full_audio.shape[1]
    output_dir = VIDEOS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        output_path = output_dir / f"strokespeak_demo_{script_code}_lesson{lesson['lesson_id']}.mp4"
    else:
        output_path = Path(output_path)
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing video: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix="strokespeak_video_", suffix=".tmp.mp4", dir=str(output_path.parent))
    os.close(handle)
    started = time.time()
    container = None
    try:
        container = av.open(temporary_name, mode="w", format="mp4")
        video_stream = container.add_stream("h264", rate=30)
        video_stream.width, video_stream.height = 1280, 720
        video_stream.pix_fmt = "yuv420p"
        video_stream.options = {"crf": "22", "preset": "veryfast"}
        audio_stream = container.add_stream("aac", rate=44100)
        audio_stream.layout = "stereo"

        total_frames = int(math.ceil(current_time * 30))
        SenseiKaiRenderer.prepare_lipsync_frames(full_audio, 30, total_frames)
        for frame_index in range(total_frames):
            t = frame_index / 30
            current = timelines[-1]
            for item in timelines:
                if item["start"] <= t < item["end"]:
                    current = item
                    break
            stage = current["stage"]
            stroke_index = current.get("stroke_index")
            fraction = 1.0
            if stage == "stroke":
                elapsed = t - current["start"]
                fraction = max(0.03, min(1.0, elapsed / max(0.5, current["duration"] - 0.25)))
            audio_start = min(total_samples - 1, int(t * 44100))
            audio_end = min(total_samples, audio_start + int(44100 / 30 * 2))
            audio_window = full_audio[:, audio_start:audio_end].astype(np.float32)
            rms = float(np.sqrt(np.mean(audio_window * audio_window))) if audio_window.size else 0.0
            mouth_open = min(1.0, max(0.0, (rms / 32768.0 - 0.018) / 0.20))
            image = _render_frame(
                stage, stroke_index, fraction, current["caption"], frame_index,
                strokes, safe_lesson_title, target_label, f"/{ascii_pronunciation}/", mouth_open, source_label,
            )
            video_frame = av.VideoFrame.from_ndarray(image, format="bgr24")
            video_frame.pts = frame_index
            for packet in video_stream.encode(video_frame):
                container.mux(packet)
        for packet in video_stream.encode():
            container.mux(packet)

        position = 0
        while position < total_samples:
            block = np.ascontiguousarray(full_audio[:, position:min(position + 1024, total_samples)])
            audio_frame = av.AudioFrame.from_ndarray(block, format="s16p", layout="stereo")
            audio_frame.rate = 44100
            audio_frame.pts = position
            for packet in audio_stream.encode(audio_frame):
                container.mux(packet)
            position += block.shape[1]
        for packet in audio_stream.encode():
            container.mux(packet)
        container.close()
        container = None
        if output_path.exists():
            raise FileExistsError(f"Refusing to overwrite existing video: {output_path}")
        os.rename(temporary_name, output_path)
        return {"path": str(output_path), "duration_seconds": round(current_time, 2),
                "size_bytes": output_path.stat().st_size, "render_seconds": round(time.time() - started, 2)}
    finally:
        SenseiKaiRenderer.clear_lipsync_frames()
        if container is not None:
            container.close()
        if os.path.exists(temporary_name):
            os.remove(temporary_name)