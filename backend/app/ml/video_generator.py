"""
StrokeSpeak - Multilingual Character & Speech Tutor
AI Teacher Video Generation Module (Zero-Cost Local Pipeline)

Components:
1. SenseiKaiRenderer: Procedural 2D fallback plus a versioned 3D robotic educator portrait
   with blended mouth restoration and a smoothed audio-driven speaking envelope.
2. SmartboardRenderer: Digital classroom board with lesson header,
   character cards, frontal lip viseme, sagittal vocal tract airflow diagrams,
   and progressive vector stroke animation.
3. AudioNarrationBuilder: Generates local female Windows speech (with gTTS
   fallback), decodes PCM samples, and drives visible portrait mouth movement from audio.
4. LessonVideoGenerator: Coordinates frame rendering, H.264 video encoding,
   and AAC audio multiplexing into MP4 containers using PyAV.
"""

import hashlib
import io
import json
import math
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import av
import cv2
from gtts import gTTS
import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[2]
VIDEOS_DIR = BACKEND_DIR / "static" / "videos"
DATA_DIR = BACKEND_DIR / "data"
REALISTIC_TEACHER_PATH = BACKEND_DIR / "static" / "images" / "sensei_aoi_realistic_v1.png"
ROBOTIC_TEACHER_PATH = BACKEND_DIR / "static" / "images" / "sensei_robot_tutor_v1.png"
STUDIO_TEACHER_PATH = BACKEND_DIR / "static" / "images" / "sensei_aoi_studio_v4.png"
FRIENDLY_TEACHER_PATH = BACKEND_DIR / "static" / "images" / "sensei_aoi_friendly_v3.png"
PARTED_TEACHER_PATH = BACKEND_DIR / "static" / "images" / "sensei_aoi_friendly_v3_parted.png"
OPEN_TEACHER_PATH = BACKEND_DIR / "static" / "images" / "sensei_aoi_friendly_v3_open.png"
STATIC_TEACHER_MODE = True



def _synthesize_windows_female_voice(segments: List[Dict[str, object]]) -> Tuple[List[bytes], str]:
    """Synthesize narration with an installed female Windows voice (no API key)."""
    with tempfile.TemporaryDirectory(prefix="strokespeak-sapi-") as temp_dir:
        work = Path(temp_dir)
        data_path = work / "segments.json"
        script_path = work / "synthesize.ps1"
        data_path.write_text(json.dumps([s["text"] for s in segments], ensure_ascii=False), encoding="utf-8")
        ps_script = """
param([string]$DataPath, [string]$OutputDirectory)
Add-Type -AssemblyName System.Speech
$texts = Get-Content -Raw -LiteralPath $DataPath | ConvertFrom-Json
$synth = [System.Speech.Synthesis.SpeechSynthesizer]::new()
$voiceNames = @($synth.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name })
if ($voiceNames -contains 'Microsoft Heera') {
    $synth.SelectVoice('Microsoft Heera')
} elseif ($voiceNames -contains 'Microsoft Zira Desktop') {
    $synth.SelectVoice('Microsoft Zira Desktop')
} elseif ($voiceNames -contains 'Microsoft Zira') {
    $synth.SelectVoice('Microsoft Zira')
} else {
    throw 'No supported installed female Windows speech voice was found.'
}
$synth.Rate = -2
$synth.Volume = 95
for ($i = 0; $i -lt $texts.Count; $i++) {
    $output = Join-Path $OutputDirectory ("segment_{0:D2}.wav" -f $i)
    $synth.SetOutputToWaveFile($output)
    $synth.Speak([string]$texts[$i])
    $synth.SetOutputToNull()
}
$synth.Voice.Name | Set-Content -LiteralPath (Join-Path $OutputDirectory "selected_voice.txt") -Encoding UTF8
$synth.Dispose()
"""
        script_path.write_text(ps_script, encoding="utf-8")
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path), str(data_path), str(work)],
            capture_output=True, text=True, timeout=180, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "Windows speech synthesis failed.").strip())
        paths = [work / f"segment_{i:02d}.wav" for i in range(len(segments))]
        if not all(path.is_file() and path.stat().st_size > 44 for path in paths):
            raise RuntimeError("Windows speech synthesis did not create every narration segment.")
        voice_path = work / "selected_voice.txt"
        voice_name = voice_path.read_text(encoding="utf-8-sig").strip() if voice_path.is_file() else "Windows female voice"
        return [path.read_bytes() for path in paths], voice_name


class SenseiKaiRenderer:
    """Renders the realistic female educator, with an illustrated fallback."""

    _portrait_cache = None
    _lipsync_frames: Optional[List[np.ndarray]] = None
    _lipsync_face_box: Tuple[int, int, int, int] = (190, 545, 305, 595)
    _lipsync_mouth_mask: Optional[np.ndarray] = None
    _lipsync_hd_source: Optional[np.ndarray] = None

    @classmethod
    def prepare_lipsync_frames(
        cls,
        full_audio: np.ndarray,
        fps: float,
        total_frames: int,
    ) -> bool:
        """Precompute Wav2Lip GAN lower-face patches for the studio/friendly portrait."""
        cls._lipsync_frames = None
        cls._lipsync_mouth_mask = None
        if STUDIO_TEACHER_PATH.is_file():
            target_path = STUDIO_TEACHER_PATH
            cls._lipsync_face_box = (190, 545, 308, 598)
        elif FRIENDLY_TEACHER_PATH.is_file():
            target_path = FRIENDLY_TEACHER_PATH
            cls._lipsync_face_box = (155, 620, 425, 815)
        else:
            return False
        try:
            from app.ml.wav2lip_sync import generate_lipsync_face_frames
        except Exception as exc:
            print(f"Wav2Lip module unavailable, using fallback mouth blend: {exc}")
            return False

        source = cv2.imread(str(target_path), cv2.IMREAD_UNCHANGED)
        if source is None or source.ndim != 3 or source.shape[2] < 3:
            return False

        y1, y2, x1, x2 = cls._lipsync_face_box
        crop_h, crop_w = y2 - y1, x2 - x1
        frames = generate_lipsync_face_frames(
            portrait_bgr=source[:, :, :3],
            full_audio_44100=full_audio,
            fps=fps,
            total_frames=total_frames,
            face_box=cls._lipsync_face_box,
        )
        if not frames:
            return False

        # Cover both mouth corners completely so no static smile corner ghosts through
        mask = np.zeros((crop_h, crop_w), dtype=np.uint8)
        center = (int(round(crop_w * 0.50)), int(round(crop_h * 0.72)))
        axes = (int(round(crop_w * 0.33)), int(round(crop_h * 0.18)))
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1, cv2.LINE_AA)
        soft_crop_mask = cv2.GaussianBlur(mask, (0, 0), 14).astype(np.float32) / 255.0

        cls._lipsync_frames = frames
        cls._lipsync_mouth_mask = soft_crop_mask[:, :, None]
        cls._lipsync_hd_source = source[:, :, :3].astype(np.float32)
        print(f"Wav2Lip GAN prepared {len(frames)} lip-synced frames.")
        return True

    @classmethod
    def clear_lipsync_frames(cls) -> None:
        cls._lipsync_frames = None
        cls._lipsync_mouth_mask = None
        cls._lipsync_hd_source = None

    SKIN = (180, 215, 242)
    SKIN_SHADOW = (150, 185, 220)
    HAIR = (42, 48, 66)
    HAIR_LIGHT = (78, 98, 142)
    BLAZER = (150, 76, 58)
    BLAZER_SHADOW = (105, 48, 36)
    SHIRT = (248, 247, 252)
    SCARF = (165, 155, 70)
    GLASSES = (45, 48, 78)
    GLASSES_GLINT = (255, 255, 255)
    PENCIL_WOOD = (80, 180, 245)
    PENCIL_TIP = (40, 40, 40)
    PENCIL_ERASER = (120, 120, 220)
    GOLD = (30, 190, 245)

    @classmethod
    def render(
        cls,
        canvas: np.ndarray,
        cx: int = 200,
        cy: int = 590,
        pose: str = "welcome",
        mouth_open: float = 0.0,
        eye_blink: bool = False,
        frame_idx: int = 0,
        pointer_target: Optional[Tuple[int, int]] = None,
    ):
        # Prefer the 3D-style female tutor with a closed resting mouth.
        # Static mode keeps this portrait still across every generated lesson video.
        portrait_path = (
            STUDIO_TEACHER_PATH if STUDIO_TEACHER_PATH.is_file()
            else FRIENDLY_TEACHER_PATH if all(path.is_file() for path in (FRIENDLY_TEACHER_PATH, PARTED_TEACHER_PATH, OPEN_TEACHER_PATH))
            else ROBOTIC_TEACHER_PATH if ROBOTIC_TEACHER_PATH.is_file()
            else REALISTIC_TEACHER_PATH
        )
        if portrait_path.is_file():
            if cls._portrait_cache is None:
                source = cv2.imread(str(portrait_path), cv2.IMREAD_UNCHANGED)
                is_studio = portrait_path == STUDIO_TEACHER_PATH
                is_friendly_legacy = portrait_path == FRIENDLY_TEACHER_PATH
                parted_source = cv2.imread(str(PARTED_TEACHER_PATH), cv2.IMREAD_UNCHANGED) if is_friendly_legacy else None
                open_source = cv2.imread(str(OPEN_TEACHER_PATH), cv2.IMREAD_UNCHANGED) if is_friendly_legacy else None
                if source is not None and source.ndim == 3 and source.shape[2] == 4:
                    h, w = source.shape[:2]
                    is_friendly = is_studio or is_friendly_legacy
                    is_robot = portrait_path == ROBOTIC_TEACHER_PATH
                    if is_studio:
                        mouth_center = (int(round(w * 0.500)), int(round(h * 0.354)))
                        mouth_radius = (int(round(w * 0.095)), int(round(h * 0.068)))
                        target_h = 545
                    elif is_friendly_legacy:
                        mouth_center = (int(round(w * 0.507)), int(round(h * 0.382)))
                        mouth_radius = (int(round(w * 0.086)), int(round(h * 0.073)))
                        target_h = 535
                    elif is_robot:
                        mouth_center = (int(round(w * 0.568)), int(round(h * 0.442)))
                        mouth_radius = (int(round(w * 0.075)), int(round(h * 0.043)))
                        target_h = 485
                    else:
                        mouth_center = (575, 390)
                        mouth_radius = (82, 38)
                        target_h = 535
                    mouth_mask = np.zeros((h, w), dtype=np.uint8)
                    cv2.ellipse(mouth_mask, mouth_center, mouth_radius, 0, 0, 360, 255, -1, cv2.LINE_AA)
                    clean_rgb = cv2.inpaint(source[:, :, :3], mouth_mask, 15, cv2.INPAINT_TELEA)
                    target_w = int(w * target_h / h)
                    original = cv2.resize(source, (target_w, target_h), interpolation=cv2.INTER_AREA)
                    clean = cv2.resize(clean_rgb, (target_w, target_h), interpolation=cv2.INTER_AREA)
                    soft_mask = cv2.GaussianBlur(mouth_mask, (0, 0), 15 if is_friendly else 5)
                    soft_mask = cv2.resize(soft_mask, (target_w, target_h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
                    normalized_mouth = (mouth_center[0] / w, mouth_center[1] / h)
                    if is_friendly_legacy:
                        if (parted_source is None or open_source is None
                                or parted_source.shape != source.shape or open_source.shape != source.shape):
                            raise ValueError("Teacher speech poses must match the resting portrait dimensions.")
                        parted = cv2.resize(parted_source, (target_w, target_h), interpolation=cv2.INTER_AREA)[:, :, :3].astype(np.float32)
                        opened = cv2.resize(open_source, (target_w, target_h), interpolation=cv2.INTER_AREA)[:, :, :3].astype(np.float32)
                    else:
                        parted = opened = original[:, :, :3].astype(np.float32)
                    cls._portrait_cache = (original, clean, soft_mask, normalized_mouth, is_friendly, parted, opened)
            if cls._portrait_cache is not None:
                portrait, clean, soft_mask, mouth_fraction, is_friendly, parted, opened = cls._portrait_cache
                portrait = portrait.copy()
                target_h, target_w = portrait.shape[:2]
                original_rgb = portrait[:, :, :3].astype(np.float32)
                openness = min(1.0, max(0.0, float(mouth_open)))
                mouth_x = int(round(target_w * mouth_fraction[0]))
                mouth_y = int(round(target_h * mouth_fraction[1]))
                if is_friendly:
                    if (
                        cls._lipsync_frames is not None
                        and cls._lipsync_mouth_mask is not None
                        and cls._lipsync_hd_source is not None
                        and 0 <= frame_idx < len(cls._lipsync_frames)
                    ):
                        # Composite Wav2Lip GAN lower-face patch at HD scale before resizing
                        hd_rgb = cls._lipsync_hd_source.copy()
                        y1, y2, x1, x2 = cls._lipsync_face_box
                        lip_patch = cls._lipsync_frames[frame_idx].astype(np.float32)
                        crop_mask = cls._lipsync_mouth_mask
                        hd_rgb[y1:y2, x1:x2] = (
                            lip_patch * crop_mask + hd_rgb[y1:y2, x1:x2] * (1.0 - crop_mask)
                        )
                        portrait_rgb = cv2.resize(
                            np.clip(hd_rgb, 0, 255).astype(np.uint8),
                            (target_w, target_h),
                            interpolation=cv2.INTER_AREA,
                        )
                    else:
                        # Blend matching generated mouth poses inside a soft mask.
                        # The rest of the face remains a single stable portrait.
                        activity = min(1.0, max(0.0, (openness - 0.055) * 1.25))
                        if activity < 0.55:
                            pose_mix = activity / 0.55
                            mouth_pose = original_rgb * (1.0 - pose_mix) + parted * pose_mix
                        else:
                            pose_mix = (activity - 0.55) / 0.45
                            mouth_pose = parted * (1.0 - pose_mix) + opened * pose_mix
                        mask = soft_mask[:, :, None]
                        portrait_rgb = np.clip(mouth_pose * mask + original_rgb * (1.0 - mask), 0, 255).astype(np.uint8)

                    if eye_blink:
                        blink_overlay = portrait_rgb.copy()
                        eye_coords = (
                            ((0.436, 0.258), (0.568, 0.254))
                            if STUDIO_TEACHER_PATH.is_file()
                            else ((0.437, 0.257), (0.563, 0.247))
                        )
                        for ex_frac, ey_frac in eye_coords:
                            ex = int(round(target_w * ex_frac))
                            ey = int(round(target_h * ey_frac))
                            cv2.ellipse(blink_overlay, (ex, ey), (13, 7), 0, 0, 360, (124, 158, 205), -1, cv2.LINE_AA)
                            cv2.ellipse(blink_overlay, (ex, ey + 2), (12, 3), 0, 10, 170, (42, 30, 34), 2, cv2.LINE_AA)
                        portrait_rgb = cv2.addWeighted(blink_overlay, 0.88, portrait_rgb, 0.12, 0)
                else:
                    mask = soft_mask[:, :, None]
                    portrait_rgb = np.clip(clean.astype(np.float32) * mask + original_rgb * (1.0 - mask), 0, 255).astype(np.uint8)
                    gap_w = max(16, int(round(target_w * 0.055)))
                    if openness < 0.055:
                        cv2.ellipse(portrait_rgb, (mouth_x, mouth_y + 1), (gap_w, 3), 0, 8, 172, (89, 58, 115), 2, cv2.LINE_AA)
                    else:
                        gap_h = max(2, int(round(1 + openness * target_h * 0.020)))
                        cv2.ellipse(portrait_rgb, (mouth_x, mouth_y), (gap_w, gap_h), 0, 0, 360, (42, 22, 46), -1, cv2.LINE_AA)
                        cv2.ellipse(portrait_rgb, (mouth_x, mouth_y), (gap_w, gap_h), 0, 0, 360, (74, 43, 102), 1, cv2.LINE_AA)
                        if openness > 0.22:
                            teeth_h = max(1, int(round(gap_h * 0.28)))
                            cv2.ellipse(portrait_rgb, (mouth_x, mouth_y - max(1, gap_h // 3)), (max(5, int(gap_w * 0.68)), teeth_h), 0, 0, 360, (224, 221, 225), -1, cv2.LINE_AA)
                        cv2.ellipse(portrait_rgb, (mouth_x, mouth_y + max(2, gap_h // 2)), (max(8, int(gap_w * 0.72)), max(1, int(gap_h * 0.22))), 0, 0, 180, (110, 70, 137), 2, cv2.LINE_AA)
                portrait[:, :, :3] = portrait_rgb

                if is_friendly:
                    # Frame her face & upper shoulders inside a steady circular profile badge
                    circle_d = 336
                    radius = circle_d // 2
                    cx_p = target_w // 2
                    cy_p = int(round(target_h * 0.35))
                    half = int(round(target_w * 0.44))
                    sx0 = max(0, cx_p - half)
                    sy0 = max(0, cy_p - half)
                    sx1 = min(target_w, cx_p + half)
                    sy1 = min(target_h, cy_p + half)
                    square = cv2.resize(portrait[sy0:sy1, sx0:sx1], (circle_d, circle_d), interpolation=cv2.INTER_AREA)

                    # Soft warm-cream studio backdrop behind the cutout inside the circle
                    bg_circle = np.full((circle_d, circle_d, 3), (242, 238, 234), dtype=np.float32)
                    fg_rgb = square[:, :, :3].astype(np.float32)
                    fg_alpha = square[:, :, 3:4].astype(np.float32) / 255.0
                    composited = fg_rgb * fg_alpha + bg_circle * (1.0 - fg_alpha)

                    circ_mask = np.zeros((circle_d, circle_d), dtype=np.uint8)
                    cv2.circle(circ_mask, (radius, radius), radius - 3, 255, -1, cv2.LINE_AA)
                    circ_alpha = (circ_mask.astype(np.float32) / 255.0)[:, :, None]

                    px0, py0 = 38, 152
                    px1, py1 = px0 + circle_d, py0 + circle_d
                    # Subtle drop shadow
                    cv2.circle(canvas, (px0 + radius + 3, py0 + radius + 6), radius + 2, (210, 206, 202), -1, cv2.LINE_AA)
                    roi = canvas[py0:py1, px0:px1].astype(np.float32)
                    canvas[py0:py1, px0:px1] = np.clip(
                        composited * circ_alpha + roi * (1.0 - circ_alpha), 0, 255
                    ).astype(np.uint8)

                    # Crisp profile ring border + audio-reactive speaking pulse halo
                    pulse_expand = int(round(2 + openness * 6))
                    if openness > 0.08:
                        cv2.circle(
                            canvas,
                            (px0 + radius, py0 + radius),
                            radius + pulse_expand,
                            (129, 140, 248),
                            2,
                            cv2.LINE_AA,
                        )
                    cv2.circle(canvas, (px0 + radius, py0 + radius), radius - 2, (241, 102, 99), 4, cv2.LINE_AA)
                    cv2.circle(canvas, (px0 + radius, py0 + radius), radius + 2, (79, 70, 229), 2, cv2.LINE_AA)
                    badge_x1, badge_y1 = px0 + 68, py1 + 14
                    badge_x2, badge_y2 = px0 + circle_d - 68, py1 + 44
                    cv2.rectangle(canvas, (badge_x1, badge_y1), (badge_x2, badge_y2), (56, 38, 28), -1)
                    cv2.rectangle(canvas, (badge_x1, badge_y1), (badge_x2, badge_y2), (241, 102, 99), 2, cv2.LINE_AA)
                    cv2.putText(canvas, "AI TUTOR", (badge_x1 + 48, badge_y1 + 21), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)
                    return

                if STATIC_TEACHER_MODE:
                    breath = sway = speaking_nod = tilt = 0.0
                    portrait_scale = 1.0
                else:
                    breath = math.sin(frame_idx * 0.085) * 4.0
                    sway = math.sin(frame_idx * 0.047) * 7.0
                    speaking_nod = openness * (1.5 + 2.0 * (0.5 + 0.5 * math.sin(frame_idx * 0.19)))
                    tilt = math.sin(frame_idx * 0.037) * 1.8
                    if pose == "point":
                        tilt += 0.45
                    elif pose == "encourage":
                        sway += math.sin(frame_idx * 0.12) * 2.0
                    portrait_scale = 1.0 + 0.004 * math.sin(frame_idx * 0.035)

                pad = 18
                padded = cv2.copyMakeBorder(
                    portrait, pad, pad, pad, pad, cv2.BORDER_CONSTANT,
                    value=(0, 0, 0, 0),
                )
                anchor = (pad + target_w * 0.5, pad + target_h * 0.72)
                transform = cv2.getRotationMatrix2D(anchor, tilt, portrait_scale)
                transformed = cv2.warpAffine(
                    padded, transform, (target_w + 2 * pad, target_h + 2 * pad),
                    flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                    borderValue=(0, 0, 0, 0),
                )
                portrait = transformed[pad:pad + target_h, pad:pad + target_w]

                x0 = 10 + int(sway)
                y0 = 102 + int(breath - speaking_nod)
                x1 = min(canvas.shape[1], x0 + target_w)
                y1 = min(canvas.shape[0], y0 + target_h)
                if x0 < 0:
                    portrait = portrait[:, -x0:]
                    x0 = 0
                if y0 < 0:
                    portrait = portrait[-y0:]
                    y0 = 0
                crop = portrait[:y1 - y0, :x1 - x0]
                if crop.size:
                    alpha = crop[:, :, 3:4].astype(np.float32) / 255.0
                    foreground = crop[:, :, :3].astype(np.float32)
                    background = canvas[y0:y1, x0:x1].astype(np.float32)
                    canvas[y0:y1, x0:x1] = (foreground * alpha + background * (1.0 - alpha)).astype(np.uint8)
                return

        # Subtle breathing idle motion
        breath_offset = int(math.sin(frame_idx * 0.1) * 3)
        cy = cy + breath_offset
        hx, hy = cx, cy - 170

        # 1. Torso / Clothes
        body_poly = np.array([
            [cx - 95, cy],
            [cx - 75, hy + 90],
            [cx - 30, hy + 75],
            [cx + 30, hy + 75],
            [cx + 75, hy + 90],
            [cx + 95, cy],
        ], dtype=np.int32)
        cv2.fillPoly(canvas, [body_poly], cls.BLAZER)
        cv2.polylines(canvas, [body_poly], True, cls.BLAZER_SHADOW, 2, cv2.LINE_AA)

        # Shoulder-length bob sits behind the face and over the blazer.
        cv2.ellipse(canvas, (hx, hy + 27), (82, 112), 0, 0, 360, cls.HAIR, -1, cv2.LINE_AA)
        cv2.ellipse(canvas, (hx - 62, hy + 72), (18, 58), -8, 0, 360, cls.HAIR_LIGHT, 2, cv2.LINE_AA)
        cv2.ellipse(canvas, (hx + 62, hy + 72), (18, 58), 8, 0, 360, cls.HAIR_LIGHT, 2, cv2.LINE_AA)

        # Shirt collar (White V-neck)
        shirt_poly = np.array([
            [cx - 32, hy + 75],
            [cx + 32, hy + 75],
            [cx, hy + 130],
        ], dtype=np.int32)
        cv2.fillPoly(canvas, [shirt_poly], cls.SHIRT)

        # A soft teal scarf gives the teacher a warm, approachable classroom look.
        scarf_knot = np.array([
            [cx - 22, hy + 77], [cx, hy + 92], [cx + 22, hy + 77],
            [cx + 14, hy + 116], [cx, hy + 130], [cx - 14, hy + 116],
        ], dtype=np.int32)
        cv2.fillPoly(canvas, [scarf_knot], cls.SCARF)
        scarf_tail = np.array([
            [cx - 12, hy + 116], [cx + 12, hy + 116],
            [cx + 25, hy + 171], [cx, hy + 154], [cx - 25, hy + 171],
        ], dtype=np.int32)
        cv2.fillPoly(canvas, [scarf_tail], cls.SCARF)
        cv2.polylines(canvas, [scarf_knot, scarf_tail], True, (105, 143, 73), 2, cv2.LINE_AA)

        # Blazer lapels
        lapel_l = np.array([[cx - 75, hy + 90], [cx - 28, hy + 75], [cx - 10, hy + 135], [cx - 40, cy]], dtype=np.int32)
        lapel_r = np.array([[cx + 75, hy + 90], [cx + 28, hy + 75], [cx + 10, hy + 135], [cx + 40, cy]], dtype=np.int32)
        cv2.fillPoly(canvas, [lapel_l], (145, 70, 35))
        cv2.fillPoly(canvas, [lapel_r], (145, 70, 35))
        cv2.polylines(canvas, [lapel_l], True, cls.BLAZER_SHADOW, 2, cv2.LINE_AA)
        cv2.polylines(canvas, [lapel_r], True, cls.BLAZER_SHADOW, 2, cv2.LINE_AA)

        # Gold Teacher Crest / Badge on lapel
        cv2.circle(canvas, (cx - 48, hy + 125), 8, cls.GOLD, -1, cv2.LINE_AA)
        cv2.circle(canvas, (cx - 48, hy + 125), 8, (20, 140, 200), 1, cv2.LINE_AA)

        # 2. Neck
        neck_poly = np.array([
            [cx - 18, hy + 50],
            [cx + 18, hy + 50],
            [cx + 18, hy + 85],
            [cx - 18, hy + 85],
        ], dtype=np.int32)
        cv2.fillPoly(canvas, [neck_poly], cls.SKIN_SHADOW)

        # 3. Head / Face
        cv2.circle(canvas, (hx - 62, hy + 8), 14, cls.SKIN, -1, cv2.LINE_AA)
        cv2.circle(canvas, (hx + 62, hy + 8), 14, cls.SKIN, -1, cv2.LINE_AA)
        cv2.circle(canvas, (hx - 62, hy + 8), 7, cls.SKIN_SHADOW, -1, cv2.LINE_AA)
        cv2.circle(canvas, (hx + 62, hy + 8), 7, cls.SKIN_SHADOW, -1, cv2.LINE_AA)

        cv2.ellipse(canvas, (hx, hy), (62, 70), 0, 0, 360, cls.SKIN, -1, cv2.LINE_AA)
        chin_pts = np.array([
            [hx - 48, hy + 30],
            [hx - 32, hy + 66],
            [hx, hy + 76],
            [hx + 32, hy + 66],
            [hx + 48, hy + 30],
        ], dtype=np.int32)
        cv2.fillPoly(canvas, [chin_pts], cls.SKIN)

        # Small gold earrings add a simple polished detail.
        cv2.circle(canvas, (hx - 64, hy + 34), 5, cls.GOLD, -1, cv2.LINE_AA)
        cv2.circle(canvas, (hx + 64, hy + 34), 5, cls.GOLD, -1, cv2.LINE_AA)

        # 5. Eyes & Eyebrows
        eye_lx, eye_rx = hx - 24, hx + 24
        eye_y = hy - 4

        cv2.ellipse(canvas, (eye_lx, eye_y - 20), (14, 5), -5, 180, 360, cls.HAIR, 3, cv2.LINE_AA)
        cv2.ellipse(canvas, (eye_rx, eye_y - 20), (14, 5), 5, 180, 360, cls.HAIR, 3, cv2.LINE_AA)

        if eye_blink:
            cv2.ellipse(canvas, (eye_lx, eye_y + 2), (12, 6), 0, 0, 180, (40, 40, 40), 3, cv2.LINE_AA)
            cv2.ellipse(canvas, (eye_rx, eye_y + 2), (12, 6), 0, 0, 180, (40, 40, 40), 3, cv2.LINE_AA)
        else:
            cv2.ellipse(canvas, (eye_lx, eye_y), (13, 16), 0, 0, 360, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.ellipse(canvas, (eye_rx, eye_y), (13, 16), 0, 0, 360, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.ellipse(canvas, (eye_lx, eye_y), (13, 16), 0, 0, 360, (50, 50, 60), 2, cv2.LINE_AA)
            cv2.ellipse(canvas, (eye_rx, eye_y), (13, 16), 0, 0, 360, (50, 50, 60), 2, cv2.LINE_AA)

            look_dx = 3 if pose == 'point' else 0
            cv2.circle(canvas, (eye_lx + look_dx, eye_y + 1), 7, (70, 45, 30), -1, cv2.LINE_AA)
            cv2.circle(canvas, (eye_rx + look_dx, eye_y + 1), 7, (70, 45, 30), -1, cv2.LINE_AA)
            cv2.circle(canvas, (eye_lx + look_dx, eye_y + 1), 4, (20, 20, 25), -1, cv2.LINE_AA)
            cv2.circle(canvas, (eye_rx + look_dx, eye_y + 1), 4, (20, 20, 25), -1, cv2.LINE_AA)

            cv2.circle(canvas, (eye_lx + look_dx - 3, eye_y - 4), 3, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(canvas, (eye_rx + look_dx - 3, eye_y - 4), 3, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(canvas, (eye_lx + look_dx + 3, eye_y + 3), 1, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(canvas, (eye_rx + look_dx + 3, eye_y + 3), 1, (255, 255, 255), -1, cv2.LINE_AA)
            for eye_x in (eye_lx, eye_rx):
                cv2.line(canvas, (eye_x - 8, eye_y - 10), (eye_x - 11, eye_y - 14), cls.HAIR, 2, cv2.LINE_AA)
                cv2.line(canvas, (eye_x, eye_y - 12), (eye_x, eye_y - 17), cls.HAIR, 2, cv2.LINE_AA)
                cv2.line(canvas, (eye_x + 8, eye_y - 10), (eye_x + 11, eye_y - 14), cls.HAIR, 2, cv2.LINE_AA)

        # Glasses
        cv2.circle(canvas, (eye_lx, eye_y), 19, cls.GLASSES, 3, cv2.LINE_AA)
        cv2.circle(canvas, (eye_rx, eye_y), 19, cls.GLASSES, 3, cv2.LINE_AA)
        cv2.line(canvas, (eye_lx + 19, eye_y - 2), (eye_rx - 19, eye_y - 2), cls.GLASSES, 3, cv2.LINE_AA)
        cv2.line(canvas, (eye_lx - 19, eye_y - 2), (hx - 60, eye_y - 6), cls.GLASSES, 2, cv2.LINE_AA)
        cv2.line(canvas, (eye_rx + 19, eye_y - 2), (hx + 60, eye_y - 6), cls.GLASSES, 2, cv2.LINE_AA)
        cv2.line(canvas, (eye_lx - 10, eye_y - 12), (eye_lx - 4, eye_y - 15), cls.GLASSES_GLINT, 2, cv2.LINE_AA)
        cv2.line(canvas, (eye_rx - 10, eye_y - 12), (eye_rx - 4, eye_y - 15), cls.GLASSES_GLINT, 2, cv2.LINE_AA)

        # 6. Nose
        nose_pts = np.array([[hx - 2, hy + 12], [hx + 3, hy + 19], [hx - 3, hy + 22]], dtype=np.int32)
        cv2.polylines(canvas, [nose_pts], False, (140, 180, 220), 2, cv2.LINE_AA)

        # 7. Cheeks
        cv2.ellipse(canvas, (hx - 36, hy + 22), (10, 5), 0, 0, 360, (170, 190, 250), -1, cv2.LINE_AA)
        cv2.ellipse(canvas, (hx + 36, hy + 22), (10, 5), 0, 0, 360, (170, 190, 250), -1, cv2.LINE_AA)

        # 8. Mouth
        mouth_y = hy + 42
        if mouth_open > 0.15:
            h_open = int(6 + mouth_open * 14)
            w_open = int(14 + mouth_open * 6)
            cv2.ellipse(canvas, (hx, mouth_y), (w_open, h_open), 0, 0, 360, (50, 50, 130), -1, cv2.LINE_AA)
            cv2.ellipse(canvas, (hx, mouth_y - h_open + 5), (w_open - 3, 4), 0, 0, 180, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.ellipse(canvas, (hx, mouth_y + h_open - 4), (w_open - 5, 5), 0, 180, 360, (90, 100, 230), -1, cv2.LINE_AA)
            cv2.ellipse(canvas, (hx, mouth_y), (w_open, h_open), 0, 0, 360, (30, 30, 80), 2, cv2.LINE_AA)
        else:
            cv2.ellipse(canvas, (hx, mouth_y - 3), (15, 8), 0, 15, 165, (50, 50, 120), 3, cv2.LINE_AA)
            cv2.line(canvas, (hx - 14, mouth_y - 2), (hx - 16, mouth_y - 5), (50, 50, 120), 2, cv2.LINE_AA)
            cv2.line(canvas, (hx + 14, mouth_y - 2), (hx + 16, mouth_y - 5), (50, 50, 120), 2, cv2.LINE_AA)

        # 9. Hair Front
        bangs = np.array([
            [hx - 66, hy - 28], [hx - 60, hy - 55], [hx - 34, hy - 76],
            [hx - 5, hy - 72], [hx + 26, hy - 66], [hx + 57, hy - 42],
            [hx + 62, hy - 18], [hx + 35, hy - 30], [hx + 10, hy - 8],
            [hx - 12, hy - 29], [hx - 40, hy - 3],
        ], dtype=np.int32)
        cv2.fillPoly(canvas, [bangs], cls.HAIR)
        cv2.polylines(canvas, [bangs], True, cls.HAIR_LIGHT, 2, cv2.LINE_AA)

        # 10. Arms based on Pose
        if pose == 'welcome':
            cv2.ellipse(canvas, (cx - 85, cy - 20), (22, 50), 25, 0, 360, cls.BLAZER, -1, cv2.LINE_AA)
            cv2.circle(canvas, (cx - 105, cy - 65), 14, cls.SKIN, -1, cv2.LINE_AA)
            cv2.ellipse(canvas, (cx + 85, cy - 20), (22, 50), -25, 0, 360, cls.BLAZER, -1, cv2.LINE_AA)
            cv2.circle(canvas, (cx + 105, cy - 65), 14, cls.SKIN, -1, cv2.LINE_AA)

        elif pose == 'point':
            cv2.ellipse(canvas, (cx - 85, cy - 10), (20, 50), 10, 0, 360, cls.BLAZER, -1, cv2.LINE_AA)
            cv2.circle(canvas, (cx - 95, cy + 35), 13, cls.SKIN, -1, cv2.LINE_AA)

            arm_pts = np.array([
                [cx + 70, hy + 95],
                [cx + 125, hy + 75],
                [cx + 185, hy + 45],
                [cx + 195, hy + 65],
                [cx + 130, hy + 100],
                [cx + 75, hy + 125],
            ], dtype=np.int32)
            cv2.fillPoly(canvas, [arm_pts], cls.BLAZER)
            cv2.circle(canvas, (cx + 195, hy + 52), 14, cls.SKIN, -1, cv2.LINE_AA)

            p_start = (cx + 185, hy + 65)
            if pointer_target is not None:
                tx, ty = pointer_target
                dx = tx - p_start[0]
                dy = ty - p_start[1]
                dist = math.hypot(dx, dy)
                if dist > 0:
                    plen = min(dist - 30, 270)
                    p_end = (int(p_start[0] + dx / dist * plen), int(p_start[1] + dy / dist * plen))
                else:
                    p_end = (cx + 380, hy - 25)
            else:
                p_end = (cx + 380, hy - 25)

            cv2.line(canvas, p_start, p_end, cls.PENCIL_WOOD, 8, cv2.LINE_AA)
            cv2.line(canvas, p_start, (cx + 205, hy + 50), cls.PENCIL_ERASER, 10, cv2.LINE_AA)
            cv2.circle(canvas, p_end, 5, cls.PENCIL_TIP, -1, cv2.LINE_AA)
            sparkle_r = int(7 + math.sin(frame_idx * 0.3) * 3)
            cv2.circle(canvas, p_end, sparkle_r, (100, 220, 255), 2, cv2.LINE_AA)

        elif pose == 'explain':
            cv2.ellipse(canvas, (cx - 75, cy - 35), (20, 45), 35, 0, 360, cls.BLAZER, -1, cv2.LINE_AA)
            cv2.circle(canvas, (cx - 65, cy - 80), 14, cls.SKIN, -1, cv2.LINE_AA)
            cv2.ellipse(canvas, (cx + 80, cy - 25), (20, 48), -20, 0, 360, cls.BLAZER, -1, cv2.LINE_AA)
            cv2.circle(canvas, (cx + 90, cy - 70), 14, cls.SKIN, -1, cv2.LINE_AA)

        elif pose == 'encourage':
            cv2.ellipse(canvas, (cx - 85, cy - 20), (22, 50), 20, 0, 360, cls.BLAZER, -1, cv2.LINE_AA)
            cv2.circle(canvas, (cx - 100, cy - 60), 14, cls.SKIN, -1, cv2.LINE_AA)
            cv2.ellipse(canvas, (cx + 75, cy - 40), (22, 45), -35, 0, 360, cls.BLAZER, -1, cv2.LINE_AA)
            tx, ty = cx + 85, cy - 90
            cv2.circle(canvas, (tx, ty), 16, cls.SKIN, -1, cv2.LINE_AA)
            cv2.ellipse(canvas, (tx, ty - 12), (6, 12), 0, 0, 360, cls.SKIN, -1, cv2.LINE_AA)
            sparkle_phase = frame_idx * 0.2
            for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                rad = math.radians(angle + sparkle_phase * 10)
                sx = int(tx + math.cos(rad) * 26)
                sy = int(ty - 12 + math.sin(rad) * 26)
                cv2.circle(canvas, (sx, sy), 2, cls.GOLD, -1, cv2.LINE_AA)


class SmartboardRenderer:
    """Renders the digital classroom smartboard with real vector strokes and articulatory models."""

    @staticmethod
    def draw_character_strokes(
        canvas: np.ndarray,
        strokes_list: List[List[Dict[str, float]]],
        box_rect: Tuple[int, int, int, int],
        progress_stroke_idx: Optional[int] = None,
        progress_frac: float = 1.0,
        stroke_color: Tuple[int, int, int] = (255, 255, 255),
        thickness: int = 10,
        show_badges: bool = True,
    ):
        x1, y1, x2, y2 = box_rect
        w, h = x2 - x1, y2 - y1

        for s_idx, stroke in enumerate(strokes_list):
            if progress_stroke_idx is not None and s_idx > progress_stroke_idx:
                continue

            pts = [(int(x1 + p['x'] * w), int(y1 + p['y'] * h)) for p in stroke]
            if len(pts) < 2:
                continue

            if progress_stroke_idx is not None and s_idx == progress_stroke_idx:
                num_pts = max(2, int(len(pts) * progress_frac))
                draw_pts = pts[:num_pts]
                cur_color = (80, 220, 255) # Bright gold/cyan active drawing
                cur_thick = thickness + 2
            else:
                draw_pts = pts
                cur_color = stroke_color
                cur_thick = thickness

            for i in range(len(draw_pts) - 1):
                cv2.line(canvas, draw_pts[i], draw_pts[i + 1], cur_color, cur_thick, cv2.LINE_AA)
                cv2.circle(canvas, draw_pts[i], cur_thick // 2, cur_color, -1, cv2.LINE_AA)
            cv2.circle(canvas, draw_pts[-1], cur_thick // 2, cur_color, -1, cv2.LINE_AA)

            if progress_stroke_idx is not None and s_idx == progress_stroke_idx and len(draw_pts) > 0:
                tip = draw_pts[-1]
                cv2.circle(canvas, tip, cur_thick + 4, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.circle(canvas, tip, cur_thick // 2, (30, 200, 255), -1, cv2.LINE_AA)

            if show_badges and len(pts) > 0:
                start_pt = pts[0]
                badge_color = (79, 70, 229) if (progress_stroke_idx is not None and s_idx == progress_stroke_idx) else (30, 41, 59)
                cv2.circle(canvas, start_pt, 14, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(canvas, start_pt, 12, badge_color, -1, cv2.LINE_AA)
                cv2.putText(canvas, str(s_idx + 1), (start_pt[0] - 5, start_pt[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2, cv2.LINE_AA)


# Multi-Script Lesson Video Configurations
LESSON_VIDEO_CONFIGS: Dict[Tuple[int, int], Dict[str, object]] = {
    (61, 2): {
        "script_title": "JAPANESE HIRAGANA  *  LESSON 1",
        "char_label": "A (/a/)",
        "unit_subtitle": "Foundation Unit 1  *  3 Verified Strokes",
        "ipa_text": "/a/",
        "viseme_desc": "Open, Relaxed, Unrounded",
        "tract_desc": "Low Central Tongue / Free Airflow",
        "target_desc": "PHONETIC TARGET: IPA /a/  --  OPEN CENTRAL UNROUNDED VOWEL",
        "step_names": {
            0: "STROKE 1 OF 3: HORIZONTAL LINE (LEFT -> RIGHT)",
            1: "STROKE 2 OF 3: DOWNWARD CROSS (TOP -> BOTTOM)",
            2: "STROKE 3 OF 3: CENTRAL WIDE LOOP (CLOCKWISE)"
        },
        "complete_title": "ALL 3 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn Japanese Hiragana: Ah.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Ah, keep your lips relaxed and open, letting sound flow smoothly: Ah.", "stroke_idx": None},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw a smooth horizontal line from left to right.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: curve downwards through the middle.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: curve across and draw a wide loop to complete the character.", "stroke_idx": 2},
            {"id": "complete", "stage": "complete", "text": "Wonderful! Now practise drawing and speaking on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "ja_hiragana_2_lesson61.mp4"
    },
    (339, 216): {
        "script_title": "SANSKRIT DEVANAGARI  *  LESSON 1",
        "char_label": "A (/a/)",
        "unit_subtitle": "Svara Unit 1  *  4 Verified Strokes",
        "ipa_text": "/a/",
        "viseme_desc": "Open, Relaxed, Unrounded",
        "tract_desc": "Guttural (Kantha) / Open Airflow",
        "target_desc": "PHONETIC TARGET: IPA /a/  --  KANTHA (GUTTURAL) SHORT VOWEL",
        "step_names": {
            0: "STROKE 1 OF 4: LEFT DOUBLE CURVE",
            1: "STROKE 2 OF 4: MIDDLE CONNECTOR",
            2: "STROKE 3 OF 4: VERTICAL STEM",
            3: "STROKE 4 OF 4: TOP SHIROREKHA BAR"
        },
        "complete_title": "ALL 4 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the primary Sanskrit vowel: Ah.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Sanskrit Ah, allow the voice to resonate from the throat with relaxed lips:", "stroke_idx": None, "ref_pronunciation": {"text": "अ", "lang": "hi"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the left double curve smoothly from top to bottom.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: draw the short middle connector rightward.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: draw the vertical stem straight downward.", "stroke_idx": 2},
            {"id": "stroke4", "stage": "stroke", "text": "Stroke four: finish with the top horizontal headline bar from left to right.", "stroke_idx": 3},
            {"id": "complete", "stage": "complete", "text": "Wonderful! Now practise drawing and speaking Sanskrit Ah on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "sa_devanagari_216_lesson339_studio-v4.mp4"
    },
    (340, 217): {
        "script_title": "SANSKRIT DEVANAGARI  *  LESSON 2",
        "char_label": "AA (/a:/)",
        "unit_subtitle": "Svara Unit 1  *  5 Verified Strokes",
        "ipa_text": "/a:/",
        "viseme_desc": "Wide Open, Long Resonance",
        "tract_desc": "Guttural (Kantha) / Sustained Flow",
        "target_desc": "PHONETIC TARGET: IPA /a:/  --  KANTHA LONG VOWEL",
        "step_names": {
            0: "STROKE 1 OF 5: LEFT DOUBLE CURVE",
            1: "STROKE 2 OF 5: MIDDLE CONNECTOR",
            2: "STROKE 3 OF 5: FIRST VERTICAL STEM",
            3: "STROKE 4 OF 5: SECOND VERTICAL MATRA STEM",
            4: "STROKE 5 OF 5: TOP SHIROREKHA BAR"
        },
        "complete_title": "ALL 5 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn Sanskrit long vowel: Aa.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce long Aa, open your mouth wider and sustain the sound clearly:", "stroke_idx": None, "ref_pronunciation": {"text": "आ", "lang": "hi"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the left double curve smoothly.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: connect rightward from the waist.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: draw the first vertical stem downward.", "stroke_idx": 2},
            {"id": "stroke4", "stage": "stroke", "text": "Stroke four: draw the second parallel vertical stem for the long vowel.", "stroke_idx": 3},
            {"id": "stroke5", "stage": "stroke", "text": "Stroke five: cap both stems with the top horizontal bar.", "stroke_idx": 4},
            {"id": "complete", "stage": "complete", "text": "Great job! Now practise drawing and speaking Sanskrit Aa on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "sa_devanagari_217_lesson340_studio-v4.mp4"
    },
    (342, 219): {
        "script_title": "SANSKRIT DEVANAGARI  *  LESSON 4",
        "char_label": "II (/i:/)",
        "unit_subtitle": "Svara Unit 1  *  4 Verified Strokes",
        "ipa_text": "/i:/",
        "viseme_desc": "Spread Lips, Sustained Front Vowel",
        "tract_desc": "Talavya (Palatal) / Long High Front",
        "target_desc": "PHONETIC TARGET: IPA /i:/  --  TALAVYA LONG VOWEL",
        "step_names": {
            0: "STROKE 1 OF 4: TOP NECK & S-CURVE BODY",
            1: "STROKE 2 OF 4: LOWER DIAGONAL TAIL",
            2: "STROKE 3 OF 4: UPPER CURVED MATRA HOOK",
            3: "STROKE 4 OF 4: TOP SHIROREKHA BAR"
        },
        "complete_title": "ALL 4 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn Sanskrit long vowel: Eee.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce long Eee, spread your lips gently and sustain the palatal sound:", "stroke_idx": None, "ref_pronunciation": {"text": "ई", "lang": "hi"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the short neck and sweep through the S-curve body.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: bring the diagonal tail downward to the bottom right.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: draw the curved vowel hook rising above the headline.", "stroke_idx": 2},
            {"id": "stroke4", "stage": "stroke", "text": "Stroke four: finish with the horizontal headline bar from left to right.", "stroke_idx": 3},
            {"id": "complete", "stage": "complete", "text": "Excellent! Now practise drawing and speaking Sanskrit Eee on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "sa_devanagari_219_lesson342_studio-v4.mp4"
    },
    (357, 221): {
        "script_title": "SANSKRIT DEVANAGARI  *  LESSON 6",
        "char_label": "UU (/u:/)",
        "unit_subtitle": "Svara Unit 1  *  3 Verified Strokes",
        "ipa_text": "/u:/",
        "viseme_desc": "Rounded, Sustained Lip Protrusion",
        "tract_desc": "Oshthya (Labial) / Long High Back",
        "target_desc": "PHONETIC TARGET: IPA /u:/  --  OSHTHYA LONG VOWEL",
        "step_names": {
            0: "STROKE 1 OF 3: ROUNDED DOUBLE CURVE",
            1: "STROKE 2 OF 3: RIGHT CURVED TAIL EXTENSION",
            2: "STROKE 3 OF 3: TOP SHIROREKHA BAR"
        },
        "complete_title": "ALL 3 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn Sanskrit long vowel: Ooo.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce long Ooo, round your lips forward and sustain the vowel cleanly:", "stroke_idx": None, "ref_pronunciation": {"text": "ऊ", "lang": "hi"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the rounded double curve from top to bottom.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: sweep outward and downward from the center for the long tail.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: finish with the horizontal headline bar across the top.", "stroke_idx": 2},
            {"id": "complete", "stage": "complete", "text": "Wonderful! Now practise drawing and speaking Sanskrit Ooo on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "sa_devanagari_221_lesson357_studio-v4.mp4"
    },
    (55, 25): {
        "script_title": "TAMIL UYIREZHUTHU  *  OVERVIEW",
        "char_label": "Uyir Vowels (A - AU)",
        "unit_subtitle": "Introduction  *  12 Classical Tamil Vowels",
        "ipa_text": "/a-au/",
        "viseme_desc": "Open Central to Rounded Glides",
        "tract_desc": "Short & Long Vowel Pairs / Pure Articulation",
        "target_desc": "FOUNDATION OVERVIEW: TAMIL UYIREZHUTHU (12 VOWELS)",
        "step_names": {
            0: "START WITH A: CLOCKWISE UPPER LOOP",
            1: "SWEEP AROUND THE OUTER BOWL",
            2: "EXTEND HORIZONTAL BAR & UPWARD STEM",
            3: "FINISH WITH RIGHT VERTICAL DOWNSTROKE"
        },
        "complete_title": "TAMIL VOWEL INTRO COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to the Tamil Vowel Foundation! Tamil has twelve pure vowels called Uyirezhuthu.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "Every Tamil vowel has a clear short and long rhythm, beginning with Ah and Aaa:", "stroke_idx": None, "ref_pronunciation": {"text": "அ ஆ", "lang": "ta"}},
            {"id": "stroke1", "stage": "stroke", "text": "First, trace the starting clockwise loop of Tamil Ah smoothly.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Next, sweep down and around the curved bowl to form the rounded base.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Then extend horizontally across the center and rise into the bridge.", "stroke_idx": 2},
            {"id": "stroke4", "stage": "stroke", "text": "Finally, bring the straight right vertical stem cleanly downward.", "stroke_idx": 3},
            {"id": "complete", "stage": "complete", "text": "You are ready to explore all twelve Tamil vowels! Begin Lesson One now.", "stroke_idx": None},
        ],
        "default_filename": "ta_25_lesson55_studio-v4.mp4"
    },
    (223, 25): {
        "script_title": "TAMIL UYIREZHUTHU  *  LESSON 1",
        "char_label": "A (/a/)",
        "unit_subtitle": "Uyir Ezhuthu 1  *  4 Verified Strokes",
        "ipa_text": "/a/",
        "viseme_desc": "Open, Neutral, Unrounded",
        "tract_desc": "Central Open Vocal Tract / Clear Flow",
        "target_desc": "PHONETIC TARGET: IPA /a/  --  TAMIL SHORT INITIAL VOWEL",
        "step_names": {
            0: "STROKE 1 OF 4: CLOCKWISE UPPER LOOP",
            1: "STROKE 2 OF 4: OUTER BOWL & RETURN",
            2: "STROKE 3 OF 4: CENTER BAR & UP STEM",
            3: "STROKE 4 OF 4: RIGHT VERTICAL DOWNSTROKE"
        },
        "complete_title": "ALL 4 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the first Tamil vowel: Short Ah.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Tamil Short Ah, open your mouth naturally and keep the sound crisp:", "stroke_idx": None, "ref_pronunciation": {"text": "அ", "lang": "ta"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the small clockwise upper loop cleanly.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: sweep right and down around the wide bowl to the left.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: extend rightward along the bar and up into the bridge.", "stroke_idx": 2},
            {"id": "stroke4", "stage": "stroke", "text": "Stroke four: finish with the right vertical stem straight down.", "stroke_idx": 3},
            {"id": "complete", "stage": "complete", "text": "Excellent! Now practise drawing and speaking Tamil Ah on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "ta_25_lesson223_studio-v4.mp4"
    },
    (224, 110): {
        "script_title": "TAMIL UYIREZHUTHU  *  LESSON 2",
        "char_label": "AA (/a:/)",
        "unit_subtitle": "Uyir Ezhuthu 2  *  3 Verified Strokes",
        "ipa_text": "/a:/",
        "viseme_desc": "Wide Open, Sustained Vowel",
        "tract_desc": "Open Central Tract / Long Duration",
        "target_desc": "PHONETIC TARGET: IPA /a:/  --  TAMIL LONG VOWEL AA",
        "step_names": {
            0: "STROKE 1 OF 3: LEFT LOOP & WIDE BOWL",
            1: "STROKE 2 OF 3: CENTER BRIDGE & DOWNSTEM",
            2: "STROKE 3 OF 3: BOTTOM RIGHT CURL"
        },
        "complete_title": "ALL 3 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the long Tamil vowel: Aaa.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Tamil Aaa, open wide and hold the vowel twice as long as Ah:", "stroke_idx": None, "ref_pronunciation": {"text": "ஆ", "lang": "ta"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the inner loop and sweep smoothly around the outer curve.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: cross the middle bar and draw down the right vertical line.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: curl smoothly outward and upward beneath the stem.", "stroke_idx": 2},
            {"id": "complete", "stage": "complete", "text": "Well done! Now practise drawing and speaking Tamil Aaa on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "ta_110_lesson224_studio-v4.mp4"
    },
    (225, 111): {
        "script_title": "TAMIL UYIREZHUTHU  *  LESSON 3",
        "char_label": "I (/i/)",
        "unit_subtitle": "Uyir Ezhuthu 3  *  1 Continuous Stroke",
        "ipa_text": "/i/",
        "viseme_desc": "Spread Lips, High Front",
        "tract_desc": "High Front Tongue / Crisp Release",
        "target_desc": "PHONETIC TARGET: IPA /i/  --  TAMIL SHORT VOWEL I",
        "step_names": {
            0: "STROKE 1 OF 1: INNER LOOP, TOP ARCH & CROSSING TAIL"
        },
        "complete_title": "STROKE COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Tamil short vowel: Ee.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Tamil Ee, gently spread your lips and keep the vowel short and bright:", "stroke_idx": None, "ref_pronunciation": {"text": "இ", "lang": "ta"}},
            {"id": "stroke1", "stage": "stroke", "text": "Trace in one continuous flow: loop inward, arch high over the top, and finish across the base.", "stroke_idx": 0},
            {"id": "complete", "stage": "complete", "text": "Great job! Now practise drawing and speaking Tamil Ee on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "ta_111_lesson225_studio-v4.mp4"
    },
    (348, 241): {
        "script_title": "SIMPLIFIED CHINESE  *  LESSON 1",
        "char_label": "Yi (/i/)",
        "unit_subtitle": "Basic Numerals  *  1 Heng Stroke (Left -> Right)",
        "ipa_text": "/i/",
        "viseme_desc": "Spread Lips, High Central-Front",
        "tract_desc": "High Front Tongue Position / High Tone",
        "target_desc": "PHONETIC TARGET: First Tone yi (1)  --  HIGH LEVEL TONE (55)",
        "step_names": {
            0: "STROKE 1 OF 1: HORIZONTAL HENG (LEFT -> RIGHT)"
        },
        "complete_title": "HENG STROKE COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Chinese numeral for one.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce it, spread your lips and hold a steady high level tone, like this:", "stroke_idx": None, "ref_pronunciation": {"text": "一", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw a confident horizontal Heng stroke from left to right.", "stroke_idx": 0},
            {"id": "complete", "stage": "complete", "text": "Great job! Now practise writing and speaking Chinese one on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_241_lesson348_teacher-static-v2.mp4"
    },
    (62, 28): {
        "script_title": "JAPANESE HIRAGANA  *  LESSON 2",
        "char_label": "I (/i/)",
        "unit_subtitle": "Foundation Unit 1  *  2 Verified Strokes",
        "ipa_text": "/i/",
        "viseme_desc": "Spread Lips, Unrounded",
        "tract_desc": "High Front Tongue / Clear Airflow",
        "target_desc": "PHONETIC TARGET: IPA /i/  --  CLOSE FRONT UNROUNDED VOWEL",
        "step_names": {
            0: "STROKE 1 OF 2: LEFT CURVED DOWNSTROKE + HOOK",
            1: "STROKE 2 OF 2: RIGHT SHORTER CURVED STROKE"
        },
        "complete_title": "ALL 2 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn Japanese Hiragana: Ee.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Ee, gently spread your lips as if smiling and keep the sound crisp and steady: Ee.", "stroke_idx": None},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: sweep downward on the left and flick upward with a small hook.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: draw a shorter curved stroke on the right side from top to bottom.", "stroke_idx": 1},
            {"id": "complete", "stage": "complete", "text": "Wonderful! Now practise drawing and speaking Hiragana Ee on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "ja_hiragana_28_lesson62_teacher-static-v2.mp4"
    },
    (63, 29): {
        "script_title": "JAPANESE HIRAGANA  *  LESSON 3",
        "char_label": "U (/u/)",
        "unit_subtitle": "Foundation Unit 1  *  2 Verified Strokes",
        "ipa_text": "/u/",
        "viseme_desc": "Relaxed, Slightly Compressed Lips",
        "tract_desc": "High Back Tongue / Smooth Airflow",
        "target_desc": "PHONETIC TARGET: IPA /u/  --  CLOSE BACK UNROUNDED VOWEL",
        "step_names": {
            0: "STROKE 1 OF 2: SHORT TOP DIAGONAL TICK",
            1: "STROKE 2 OF 2: ROUNDED SWEEPING CURVE"
        },
        "complete_title": "ALL 2 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn Japanese Hiragana: Oo.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Oo, keep your lips relaxed without rounding too tightly: Oo.", "stroke_idx": None},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw a short slanted tick at the top.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: curve up and sweep smoothly down to the bottom.", "stroke_idx": 1},
            {"id": "complete", "stage": "complete", "text": "Great job! Now practise drawing and speaking Hiragana Oo on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "ja_hiragana_29_lesson63_teacher-static-v2.mp4"
    },
    (64, 30): {
        "script_title": "JAPANESE HIRAGANA  *  LESSON 4",
        "char_label": "E (/e/)",
        "unit_subtitle": "Foundation Unit 1  *  2 Verified Strokes",
        "ipa_text": "/e/",
        "viseme_desc": "Mid-Open, Unrounded Lips",
        "tract_desc": "Mid Front Tongue / Steady Airflow",
        "target_desc": "PHONETIC TARGET: IPA /e/  --  MID FRONT UNROUNDED VOWEL",
        "step_names": {
            0: "STROKE 1 OF 2: SHORT TOP DIAGONAL TICK",
            1: "STROKE 2 OF 2: ZIGZAG CURVE TO BOTTOM RIGHT"
        },
        "complete_title": "ALL 2 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn Japanese Hiragana: Eh.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Eh, open slightly wider than Ee with relaxed lips: Eh.", "stroke_idx": None},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw a short slanted tick at the top center.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: glide across, angle down left, then sweep out to the bottom right.", "stroke_idx": 1},
            {"id": "complete", "stage": "complete", "text": "Awesome! Now practise drawing and speaking Hiragana Eh on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "ja_hiragana_30_lesson64_teacher-static-v2.mp4"
    },
    (65, 3): {
        "script_title": "JAPANESE HIRAGANA  *  LESSON 5",
        "char_label": "O (/o/)",
        "unit_subtitle": "Foundation Unit 1  *  3 Verified Strokes",
        "ipa_text": "/o/",
        "viseme_desc": "Gently Rounded Lips",
        "tract_desc": "Mid Back Tongue / Open Resonance",
        "target_desc": "PHONETIC TARGET: IPA /o/  --  MID BACK ROUNDED VOWEL",
        "step_names": {
            0: "STROKE 1 OF 3: SHORT HORIZONTAL BAR",
            1: "STROKE 2 OF 3: VERTICAL STEM & WIDE LOOP",
            2: "STROKE 3 OF 3: UPPER RIGHT ACCENT DOT"
        },
        "complete_title": "ALL 3 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn Japanese Hiragana: Oh.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Oh, gently round your lips into a small circle: Oh.", "stroke_idx": None},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw a short horizontal bar from left to right.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: go straight down, loop left, and sweep around in a wide arc.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: finish with a small accent tick on the upper right.", "stroke_idx": 2},
            {"id": "complete", "stage": "complete", "text": "Fantastic! Now practise drawing and speaking Hiragana Oh on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "ja_hiragana_3_lesson65_teacher-static-v2.mp4"
    },
    (341, 218): {
        "script_title": "SANSKRIT DEVANAGARI  *  LESSON 3",
        "char_label": "I (/i/)",
        "unit_subtitle": "Svara Unit 1  *  3 Verified Strokes",
        "ipa_text": "/i/",
        "viseme_desc": "Spread Lips, Unrounded",
        "tract_desc": "Talavya (Palatal) / High Front",
        "target_desc": "PHONETIC TARGET: IPA /i/  --  TALAVYA SHORT VOWEL",
        "step_names": {
            0: "STROKE 1 OF 3: TOP NECK & S-CURVE BODY",
            1: "STROKE 2 OF 3: LOWER DIAGONAL TAIL",
            2: "STROKE 3 OF 3: TOP SHIROREKHA BAR"
        },
        "complete_title": "ALL 3 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn Sanskrit Devanagari: Short Ee.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Short Ee, raise your tongue toward the palate and keep the vowel crisp:", "stroke_idx": None, "ref_pronunciation": {"text": "इ", "lang": "hi"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: start with the short top stem and curve smoothly into an S-shape.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: form the small curve at the base and sweep the tail downward.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: finish with the horizontal headline bar across the top.", "stroke_idx": 2},
            {"id": "complete", "stage": "complete", "text": "Excellent! Now practise drawing and speaking Sanskrit Short Ee on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "sa_devanagari_218_lesson341_studio-v4.mp4"
    },
    (343, 220): {
        "script_title": "SANSKRIT DEVANAGARI  *  LESSON 5",
        "char_label": "U (/u/)",
        "unit_subtitle": "Svara Unit 1  *  2 Verified Strokes",
        "ipa_text": "/u/",
        "viseme_desc": "Rounded, Protruded Lips",
        "tract_desc": "Oshthya (Labial) / High Back",
        "target_desc": "PHONETIC TARGET: IPA /u/  --  OSHTHYA SHORT VOWEL",
        "step_names": {
            0: "STROKE 1 OF 2: ROUNDED DOUBLE CURVE",
            1: "STROKE 2 OF 2: TOP SHIROREKHA BAR"
        },
        "complete_title": "ALL 2 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn Sanskrit Devanagari: Short Oo.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Short Oo, round your lips gently forward for a crisp vowel:", "stroke_idx": None, "ref_pronunciation": {"text": "उ", "lang": "hi"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: sweep through the rounded double curve from top to bottom left.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: draw the horizontal headline bar cleanly across the top.", "stroke_idx": 1},
            {"id": "complete", "stage": "complete", "text": "Well done! Now practise drawing and speaking Sanskrit Short Oo on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "sa_devanagari_220_lesson343_studio-v4.mp4"
    },
    (227, 113): {
        "script_title": "TAMIL UYIREZHUTHU  *  LESSON 5",
        "char_label": "U (/u/)",
        "unit_subtitle": "Tamil Uyir Unit 1  *  1 Verified Continuous Stroke",
        "ipa_text": "/u/",
        "viseme_desc": "Rounded, Compact Lips",
        "tract_desc": "High Back Rounded / Smooth Airflow",
        "target_desc": "PHONETIC TARGET: IPA /u/  --  TAMIL SHORT VOWEL U",
        "step_names": {
            0: "STROKE 1 OF 1: LOOP, CURVE & HORIZONTAL BASE"
        },
        "complete_title": "STROKE COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn Tamil vowel: Short U.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce Tamil Short U, round your lips cleanly and listen to the native sound:", "stroke_idx": None, "ref_pronunciation": {"text": "உ", "lang": "ta"}},
            {"id": "stroke1", "stage": "stroke", "text": "Draw in one smooth stroke: form the top loop, curve down, and extend straight right along the base.", "stroke_idx": 0},
            {"id": "complete", "stage": "complete", "text": "Great job! Now practise drawing and speaking Tamil Short U on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "ta_113_lesson227_studio-v4.mp4"
    },
    (349, 242): {
        "script_title": "SIMPLIFIED CHINESE  *  LESSON 2",
        "char_label": "Er [er4]",
        "unit_subtitle": "Basic Numerals  *  2 Heng Strokes (Upper First)",
        "ipa_text": "[er4]",
        "viseme_desc": "Open Mid-Central to Retroflex",
        "tract_desc": "Falling Fourth Tone (51) / Clear Release",
        "target_desc": "PHONETIC TARGET: Fourth Tone er (2)  --  HIGH-TO-LOW FALLING TONE",
        "step_names": {
            0: "STROKE 1 OF 2: UPPER HORIZONTAL HENG (LEFT -> RIGHT)",
            1: "STROKE 2 OF 2: LOWER HORIZONTAL HENG (LEFT -> RIGHT)"
        },
        "complete_title": "ALL 2 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Chinese numeral for two.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce it, use a crisp fourth falling tone from high to low, like this:", "stroke_idx": None, "ref_pronunciation": {"text": "二", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the upper horizontal Heng stroke cleanly from left to right.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: draw the lower horizontal Heng stroke below it from left to right.", "stroke_idx": 1},
            {"id": "complete", "stage": "complete", "text": "Well done! Now practise writing and speaking Chinese two on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_242_lesson349_teacher-static-v2.mp4"
    },
    (350, 243): {
        "script_title": "SIMPLIFIED CHINESE  *  LESSON 3",
        "char_label": "San (/san/)",
        "unit_subtitle": "Basic Numerals  *  3 Heng Strokes (Top -> Bottom)",
        "ipa_text": "/san/",
        "viseme_desc": "Open Front to Alveolar Nasal",
        "tract_desc": "First High Level Tone (55)",
        "target_desc": "PHONETIC TARGET: First Tone san (3)  --  HIGH LEVEL TONE",
        "step_names": {
            0: "STROKE 1 OF 3: TOP HORIZONTAL HENG",
            1: "STROKE 2 OF 3: MIDDLE HORIZONTAL HENG",
            2: "STROKE 3 OF 3: LONG BASE HORIZONTAL HENG"
        },
        "complete_title": "ALL 3 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Chinese numeral for three.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce it, use a steady high first tone, like this:", "stroke_idx": None, "ref_pronunciation": {"text": "三", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the top horizontal Heng stroke from left to right.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: draw the shorter middle horizontal stroke from left to right.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: finish with the longer base horizontal stroke from left to right.", "stroke_idx": 2},
            {"id": "complete", "stage": "complete", "text": "Great work! Now practise writing and speaking Chinese three on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_243_lesson350_teacher-static-v2.mp4"
    },
    (351, 244): {
        "script_title": "SIMPLIFIED CHINESE  *  LESSON 4",
        "char_label": "Ren [ren2]",
        "unit_subtitle": "Core Pictographs  *  2 Strokes (Pie -> Na)",
        "ipa_text": "[ren2]",
        "viseme_desc": "Slightly Rounded Retroflex to Nasal",
        "tract_desc": "Second Rising Tone (35)",
        "target_desc": "PHONETIC TARGET: Second Tone ren (person)  --  RISING TONE",
        "step_names": {
            0: "STROKE 1 OF 2: LEFT-FALLING PIE STROKE",
            1: "STROKE 2 OF 2: RIGHT-FALLING NA STROKE"
        },
        "complete_title": "ALL 2 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Chinese character for person.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce it, lift your pitch in a clear second rising tone, like this:", "stroke_idx": None, "ref_pronunciation": {"text": "人", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: sweep downward and left with the Pie stroke.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: brace outward to the bottom right with the Na stroke.", "stroke_idx": 1},
            {"id": "complete", "stage": "complete", "text": "Well done! Now practise writing and speaking Chinese person on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_244_lesson351_teacher-static-v2.mp4"
    },
    (352, 245): {
        "script_title": "SIMPLIFIED CHINESE  *  LESSON 5",
        "char_label": "Da (/ta/)",
        "unit_subtitle": "Core Pictographs  *  3 Strokes (Heng -> Pie -> Na)",
        "ipa_text": "/ta/",
        "viseme_desc": "Alveolar Stop to Open Central Vowel",
        "tract_desc": "Fourth Falling Tone (51)",
        "target_desc": "PHONETIC TARGET: Fourth Tone da (big)  --  FALLING TONE",
        "step_names": {
            0: "STROKE 1 OF 3: HORIZONTAL HENG STROKE",
            1: "STROKE 2 OF 3: LEFT-FALLING PIE STROKE",
            2: "STROKE 3 OF 3: RIGHT-FALLING NA STROKE"
        },
        "complete_title": "ALL 3 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Chinese character for big.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce it, drop sharply in a crisp fourth falling tone, like this:", "stroke_idx": None, "ref_pronunciation": {"text": "大", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the horizontal Heng stroke across the upper middle.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: sweep downward from top center to bottom left.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: extend outward to the bottom right to balance the character.", "stroke_idx": 2},
            {"id": "complete", "stage": "complete", "text": "Excellent! Now practise writing and speaking Chinese big on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_245_lesson352_teacher-static-v2.mp4"
    },
    (383, 247): {
        "script_title": "SIMPLIFIED CHINESE  *  LESSON 6",
        "char_label": "Kou [kou3]",
        "unit_subtitle": "Foundation Unit 2  *  3 Strokes (Box Enclosure)",
        "ipa_text": "[kou3]",
        "viseme_desc": "Aspirated Velar to Rounded Glide",
        "tract_desc": "Third Dipping Tone (214)",
        "target_desc": "PHONETIC TARGET: Third Tone kou (mouth)  --  DIPPING TONE",
        "step_names": {
            0: "STROKE 1 OF 3: LEFT VERTICAL SHU",
            1: "STROKE 2 OF 3: TOP-RIGHT HENG-ZHE CORNER",
            2: "STROKE 3 OF 3: BOTTOM CLOSING HENG"
        },
        "complete_title": "ALL 3 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Chinese character for mouth.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce it, dip low and rise gently in the third tone, like this:", "stroke_idx": None, "ref_pronunciation": {"text": "口", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the left vertical wall downward.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: draw across the top and turn straight down the right side.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: close the bottom box cleanly from left to right.", "stroke_idx": 2},
            {"id": "complete", "stage": "complete", "text": "Great job! Now practise writing and speaking Chinese mouth on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_247_lesson383_teacher-static-v2.mp4"
    },
    (384, 248): {
        "script_title": "SIMPLIFIED CHINESE  *  LESSON 7",
        "char_label": "Ri [ri4]",
        "unit_subtitle": "Foundation Unit 2  *  4 Strokes (Sun Frame)",
        "ipa_text": "[ri4]",
        "viseme_desc": "Retroflex Approximant / Syllabic",
        "tract_desc": "Fourth Falling Tone (51)",
        "target_desc": "PHONETIC TARGET: Fourth Tone ri (sun)  --  FALLING TONE",
        "step_names": {
            0: "STROKE 1 OF 4: LEFT VERTICAL SHU",
            1: "STROKE 2 OF 4: TOP-RIGHT HENG-ZHE",
            2: "STROKE 3 OF 4: INNER HORIZONTAL HENG",
            3: "STROKE 4 OF 4: BOTTOM CLOSING HENG"
        },
        "complete_title": "ALL 4 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Chinese character for sun.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce it, use a crisp fourth falling tone, like this:", "stroke_idx": None, "ref_pronunciation": {"text": "日", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the left vertical wall downward.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: draw across the top and turn down the right side.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: add the middle horizontal bar inside the frame.", "stroke_idx": 2},
            {"id": "stroke4", "stage": "stroke", "text": "Stroke four: close the bottom line from left to right.", "stroke_idx": 3},
            {"id": "complete", "stage": "complete", "text": "Well done! Now practise writing and speaking Chinese sun on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_248_lesson384_teacher-static-v2.mp4"
    },
    (385, 249): {
        "script_title": "SIMPLIFIED CHINESE  *  LESSON 8",
        "char_label": "Yue [yue4]",
        "unit_subtitle": "Foundation Unit 2  *  4 Strokes (Moon Frame)",
        "ipa_text": "[yue4]",
        "viseme_desc": "Rounded Palatal Glide to Mid Front",
        "tract_desc": "Fourth Falling Tone (51)",
        "target_desc": "PHONETIC TARGET: Fourth Tone yue (moon)  --  FALLING TONE",
        "step_names": {
            0: "STROKE 1 OF 4: LEFT CURVED PIE",
            1: "STROKE 2 OF 4: TOP-RIGHT HENG-ZHE-GOU",
            2: "STROKE 3 OF 4: UPPER INNER HENG",
            3: "STROKE 4 OF 4: LOWER INNER HENG"
        },
        "complete_title": "ALL 4 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Chinese character for moon.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce it, round your lips and drop in a fourth falling tone, like this:", "stroke_idx": None, "ref_pronunciation": {"text": "月", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the left vertical stroke and curve gently at the base.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: draw across the top, turn down the right, and flick a small hook.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: draw the upper inner horizontal bar.", "stroke_idx": 2},
            {"id": "stroke4", "stage": "stroke", "text": "Stroke four: draw the lower inner horizontal bar.", "stroke_idx": 3},
            {"id": "complete", "stage": "complete", "text": "Awesome! Now practise writing and speaking Chinese moon on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_249_lesson385_teacher-static-v2.mp4"
    },
    (386, 252): {
        "script_title": "SIMPLIFIED CHINESE  *  LESSON 9",
        "char_label": "Shan [shan1]",
        "unit_subtitle": "Foundation Unit 2  *  3 Strokes (Mountain Peaks)",
        "ipa_text": "[shan1]",
        "viseme_desc": "Retroflex Fricative to Open Nasal",
        "tract_desc": "First High Level Tone (55)",
        "target_desc": "PHONETIC TARGET: First Tone shan (mountain)  --  HIGH LEVEL TONE",
        "step_names": {
            0: "STROKE 1 OF 3: CENTER VERTICAL PEAK",
            1: "STROKE 2 OF 3: LEFT-TO-BASE SHU-ZHE",
            2: "STROKE 3 OF 3: RIGHT VERTICAL WALL"
        },
        "complete_title": "ALL 3 STROKES COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Chinese character for mountain.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "To pronounce it, hold a steady high first tone, like this:", "stroke_idx": None, "ref_pronunciation": {"text": "山", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Stroke one: draw the tall center vertical peak straight down.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Stroke two: draw the left vertical line and turn right across the base.", "stroke_idx": 1},
            {"id": "stroke3", "stage": "stroke", "text": "Stroke three: finish with the right vertical peak downward.", "stroke_idx": 2},
            {"id": "complete", "stage": "complete", "text": "Fantastic! Now practise writing and speaking Chinese mountain on your canvas!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_252_lesson386_teacher-static-v2.mp4"
    },
    (387, 244): {
        "script_title": "SIMPLIFIED CHINESE  *  BEGINNER 1",
        "char_label": "Ni Hao [ni3 hao3]",
        "unit_subtitle": "Everyday Greetings  *  Hello (2-Character Phrase)",
        "ipa_text": "[ni3 hao3]",
        "viseme_desc": "Alveolar Nasal to Open Diphthong",
        "tract_desc": "Tone Sandhi (2-3) / Smooth Rising Glide",
        "target_desc": "PHONETIC TARGET: ni3 hao3 (Hello)  --  TONE SANDHI",
        "step_names": {
            0: "COMPONENT RADICAL: PERSON (PIE STROKE)",
            1: "COMPONENT RADICAL: PERSON (NA STROKE)"
        },
        "complete_title": "GREETING COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Chinese greeting: Ni Hao, meaning Hello.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "When two third tones meet, the first rises like a second tone. Listen closely:", "stroke_idx": None, "ref_pronunciation": {"text": "你好", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Notice the left person radical in Ni starts with a sweeping Pie stroke.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Pair it cleanly with the balancing stroke and practise speaking Ni Hao aloud.", "stroke_idx": 1},
            {"id": "complete", "stage": "complete", "text": "Great job! Now speak Ni Hao into your microphone for pronunciation practice!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_phrase_lesson387_studio-v4.mp4"
    },
    (388, 244): {
        "script_title": "SIMPLIFIED CHINESE  *  BEGINNER 2",
        "char_label": "Xie Xie [xie4 xie]",
        "unit_subtitle": "Everyday Greetings  *  Thank You",
        "ipa_text": "[xie4]",
        "viseme_desc": "Alveolo-Palatal Fricative to Glide",
        "tract_desc": "Fourth Falling Tone + Neutral Tone",
        "target_desc": "PHONETIC TARGET: xie4 xie (Thank you)  --  FALLING + NEUTRAL",
        "step_names": {
            0: "SPEECH RADICAL & BODY BALANCE",
            1: "FALLING TONE + LIGHT NEUTRAL REPEAT"
        },
        "complete_title": "THANK YOU PHRASE COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn how to say thank you in Chinese: Xie Xie.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "Drop sharply on the first syllable and keep the second light and neutral:", "stroke_idx": None, "ref_pronunciation": {"text": "谢谢", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Keep the central body balanced while pronouncing the crisp falling fourth tone.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Repeat the second syllable softly without stress.", "stroke_idx": 1},
            {"id": "complete", "stage": "complete", "text": "Well done! Now practise saying Xie Xie clearly on your lesson screen!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_phrase_lesson388_studio-v4.mp4"
    },
    (389, 249): {
        "script_title": "SIMPLIFIED CHINESE  *  BEGINNER 3",
        "char_label": "Peng You [peng2 you]",
        "unit_subtitle": "Everyday Vocabulary  *  Friend",
        "ipa_text": "[peng2]",
        "viseme_desc": "Bilabial Stop to Rounded Back Vowel",
        "tract_desc": "Second Rising Tone + Neutral Tone",
        "target_desc": "PHONETIC TARGET: peng2 you (Friend)  --  RISING + NEUTRAL",
        "step_names": {
            0: "PAIRED MOON RADICALS (LEFT COMPONENT)",
            1: "PAIRED MOON RADICALS (RIGHT BALANCE)"
        },
        "complete_title": "VOCABULARY COMPLETE!",
        "script_segments": [
            {"id": "intro", "stage": "intro", "text": "Welcome to StrokeSpeak! Today we learn the Chinese word for friend: Peng You.", "stroke_idx": None},
            {"id": "articulation", "stage": "articulation", "text": "Lift your voice in a clear second rising tone on Peng, then relax on You:", "stroke_idx": None, "ref_pronunciation": {"text": "朋友", "lang": "zh-CN"}},
            {"id": "stroke1", "stage": "stroke", "text": "Remember Peng pairs two moon components side by side.", "stroke_idx": 0},
            {"id": "stroke2", "stage": "stroke", "text": "Keep both strokes balanced and speak Peng You naturally.", "stroke_idx": 1},
            {"id": "complete", "stage": "complete", "text": "Awesome! Now practise speaking Peng You for your Beginner lesson!", "stroke_idx": None},
        ],
        "default_filename": "zh_hans_phrase_lesson389_studio-v4.mp4"
    }
}


def render_scene_frame(
    stage: str,
    stroke_idx: Optional[int],
    stroke_frac: float,
    caption: str,
    mouth_open: float,
    eye_blink: bool,
    frame_idx: int,
    strokes_data: List[List[Dict[str, float]]],
    char_label: str = "A (/a/)",
    script_title: str = "JAPANESE HIRAGANA  *  LESSON 1",
    ipa_text: str = "/a/",
    unit_subtitle: str = "Foundation Unit 1  *  3 Verified Strokes",
    viseme_desc: str = "Open, Relaxed, Unrounded",
    tract_desc: str = "Low Central Tongue / Free Airflow",
    target_desc: str = "PHONETIC TARGET: IPA /a/  --  OPEN CENTRAL UNROUNDED VOWEL",
    step_names: Optional[Dict[int, str]] = None,
    complete_title: str = "ALL STROKES COMPLETE!",
) -> np.ndarray:
    """Renders one 1280x720 video frame with teacher, smartboard, and subtitles."""
    W, H = 1280, 720
    img = np.full((H, W, 3), (242, 245, 250), dtype=np.uint8)
    cv2.rectangle(img, (0, 670), (W, H), (215, 220, 228), -1)
    cv2.line(img, (0, 670), (W, 670), (180, 190, 205), 2, cv2.LINE_AA)

    bx1, by1, bx2, by2 = 390, 40, 1240, 630
    bw, bh = bx2 - bx1, by2 - by1

    cv2.rectangle(img, (bx1 - 6, by1 - 6), (bx2 + 6, by2 + 6), (45, 35, 30), -1)
    cv2.rectangle(img, (bx1, by1), (bx2, by2), (38, 26, 20), -1)
    cv2.rectangle(img, (bx1, by1), (bx2, by2), (241, 102, 99), 3, cv2.LINE_AA)

    # Header
    cv2.rectangle(img, (bx1, by1), (bx2, by1 + 52), (56, 38, 28), -1)
    cv2.line(img, (bx1, by1 + 52), (bx2, by1 + 52), (79, 70, 229), 2, cv2.LINE_AA)
    cv2.putText(img, "STROKESPEAK ACADEMY", (bx1 + 25, by1 + 34), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (252, 180, 165), 2, cv2.LINE_AA)
    cv2.putText(img, script_title, (bx1 + 360, by1 + 34), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (226, 232, 240), 2, cv2.LINE_AA)
    cv2.rectangle(img, (bx2 - 110, by1 + 10), (bx2 - 20, by1 + 42), (241, 102, 99), -1)
    cv2.putText(img, ipa_text, (bx2 - 80, by1 + 32), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (255, 255, 255), 2, cv2.LINE_AA)

    pointer_target = None
    if stage == 'intro':
        cx, cy = bx1 + bw // 2, by1 + bh // 2 + 10
        cv2.circle(img, (cx, cy - 35), 140, (62, 42, 32), -1, cv2.LINE_AA)
        cv2.circle(img, (cx, cy - 35), 140, (241, 102, 99), 3, cv2.LINE_AA)
        if strokes_data:
            cbox = (cx - 100, cy - 135, cx + 100, cy + 65)
            SmartboardRenderer.draw_character_strokes(img, strokes_data, cbox, stroke_color=(255, 255, 255), thickness=9, show_badges=False)
        cv2.putText(img, f"Target Character: {char_label}", (cx - 165, cy + 145), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, unit_subtitle, (cx - 175, cy + 185), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (251, 191, 36), 2, cv2.LINE_AA)

    elif stage == 'articulation':
        mid_x = bx1 + bw // 2
        cv2.line(img, (mid_x, by1 + 70), (mid_x, by2 - 60), (45, 58, 78), 2, cv2.LINE_AA)

        lx = bx1 + bw // 4
        ly = by1 + 225
        cv2.putText(img, "FRONTAL LIP VISEME", (lx - 120, by1 + 88), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (129, 140, 248), 2, cv2.LINE_AA)
        cv2.putText(img, viseme_desc, (lx - 120, by1 + 115), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (148, 163, 184), 1, cv2.LINE_AA)

        cv2.circle(img, (lx, ly), 95, (62, 42, 32), -1, cv2.LINE_AA)
        cv2.circle(img, (lx, ly), 95, (71, 85, 105), 2, cv2.LINE_AA)
        cv2.line(img, (lx, ly - 45), (lx + 7, ly - 20), (148, 163, 184), 2, cv2.LINE_AA)
        cv2.line(img, (lx + 7, ly - 20), (lx - 7, ly - 20), (148, 163, 184), 2, cv2.LINE_AA)
        cv2.ellipse(img, (lx, ly + 25), (52, 35), 0, 0, 360, (75, 85, 210), -1, cv2.LINE_AA)
        cv2.ellipse(img, (lx, ly + 25), (52, 35), 0, 0, 360, (50, 60, 160), 2, cv2.LINE_AA)
        cv2.ellipse(img, (lx, ly + 25), (40, 24), 0, 0, 360, (25, 25, 75), -1, cv2.LINE_AA)
        cv2.ellipse(img, (lx, ly + 10), (28, 7), 0, 0, 180, (245, 245, 250), -1, cv2.LINE_AA)
        cv2.ellipse(img, (lx, ly + 35), (34, 11), 0, 180, 360, (110, 80, 210), -1, cv2.LINE_AA)

        rx = mid_x + bw // 4
        ry = by1 + 225
        cv2.putText(img, "SAGITTAL VOCAL TRACT", (rx - 125, by1 + 88), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (129, 140, 248), 2, cv2.LINE_AA)
        cv2.putText(img, tract_desc, (rx - 135, by1 + 115), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (148, 163, 184), 1, cv2.LINE_AA)

        cv2.rectangle(img, (rx - 135, ry - 75), (rx + 135, ry + 115), (62, 42, 32), -1)
        cv2.rectangle(img, (rx - 135, ry - 75), (rx + 135, ry + 115), (71, 85, 105), 2, cv2.LINE_AA)
        
        palate_pts = np.array([[rx - 95, ry - 30], [rx - 45, ry - 55], [rx + 25, ry - 50], [rx + 85, ry + 15], [rx + 85, ry + 95]], dtype=np.int32)
        cv2.polylines(img, [palate_pts], False, (203, 213, 225), 4, cv2.LINE_AA)
        tongue_pts = np.array([[rx - 75, ry + 15], [rx - 25, ry + 18], [rx + 20, ry + 28], [rx + 45, ry + 95], [rx - 75, ry + 95]], dtype=np.int32)
        cv2.fillPoly(img, [tongue_pts], (110, 80, 210))
        cv2.polylines(img, [tongue_pts[:4]], False, (160, 120, 255), 3, cv2.LINE_AA)
        
        pulse = (frame_idx % 20) / 20.0
        start_flow = (int(rx + 55 - 10 * pulse), int(ry + 75 - 10 * pulse))
        end_flow = (int(rx - 85 - 5 * pulse), int(ry - 15 - 5 * pulse))
        cv2.arrowedLine(img, start_flow, end_flow, (255, 230, 80), 3, cv2.LINE_AA, tipLength=0.18)

        cv2.rectangle(img, (bx1 + 50, by2 - 62), (bx2 - 50, by2 - 15), (56, 38, 28), -1)
        cv2.rectangle(img, (bx1 + 50, by2 - 62), (bx2 - 50, by2 - 15), (241, 102, 99), 2, cv2.LINE_AA)
        cv2.putText(img, target_desc, (bx1 + 65, by2 - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (251, 191, 36), 2, cv2.LINE_AA)
        pointer_target = (lx + 20, ly + 25)

    elif stage == 'stroke':
        canvas_cx = bx1 + bw // 2
        canvas_cy = by1 + bh // 2 + 18
        card_w, card_h = 390, 390
        cbox = (canvas_cx - card_w // 2, canvas_cy - card_h // 2, canvas_cx + card_w // 2, canvas_cy + card_h // 2)

        cur_steps = step_names or {}
        stroke_name = cur_steps.get(stroke_idx or 0, f"STROKE {(stroke_idx or 0) + 1} DEMONSTRATION")
        cv2.rectangle(img, (canvas_cx - 280, by1 + 65), (canvas_cx + 280, by1 + 102), (56, 38, 28), -1)
        cv2.rectangle(img, (canvas_cx - 280, by1 + 65), (canvas_cx + 280, by1 + 102), (241, 102, 99), 1, cv2.LINE_AA)
        cv2.putText(img, stroke_name, (canvas_cx - 260, by1 + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (252, 180, 165), 2, cv2.LINE_AA)

        cv2.rectangle(img, (cbox[0], cbox[1]), (cbox[2], cbox[3]), (16, 22, 34), -1)
        cv2.rectangle(img, (cbox[0], cbox[1]), (cbox[2], cbox[3]), (51, 65, 85), 2, cv2.LINE_AA)
        cv2.line(img, (canvas_cx, cbox[1] + 8), (canvas_cx, cbox[3] - 8), (35, 45, 65), 1, cv2.LINE_AA)
        cv2.line(img, (cbox[0] + 8, canvas_cy), (cbox[2] - 8, canvas_cy), (35, 45, 65), 1, cv2.LINE_AA)

        if strokes_data:
            SmartboardRenderer.draw_character_strokes(
                img, strokes_data, cbox,
                progress_stroke_idx=stroke_idx,
                progress_frac=stroke_frac,
                stroke_color=(255, 255, 255),
                thickness=9,
                show_badges=True
            )
        pointer_target = (cbox[0] + 40, canvas_cy)

    elif stage == 'complete':
        cx, cy = bx1 + bw // 2, by1 + bh // 2 + 10
        cv2.circle(img, (cx, cy - 35), 145, (30, 45, 65), -1, cv2.LINE_AA)
        cv2.circle(img, (cx, cy - 35), 145, (52, 211, 153), 4, cv2.LINE_AA)
        
        if strokes_data:
            cbox = (cx - 105, cy - 140, cx + 105, cy + 70)
            SmartboardRenderer.draw_character_strokes(img, strokes_data, cbox, stroke_color=(255, 255, 255), thickness=9, show_badges=True)

        cv2.putText(img, complete_title, (cx - 175, cy + 145), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (52, 211, 153), 2, cv2.LINE_AA)
        cv2.putText(img, "NOW PRACTISE DRAWING & SPEAKING ON CANVAS!", (cx - 245, cy + 185), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (251, 191, 36), 2, cv2.LINE_AA)

    pose_map = {
        'intro': 'welcome' if frame_idx < 45 else 'explain',
        'articulation': 'point',
        'stroke': 'point',
        'complete': 'encourage'
    }
    cur_pose = pose_map.get(stage, 'welcome')
    SenseiKaiRenderer.render(img, cx=200, cy=590, pose=cur_pose, mouth_open=mouth_open, eye_blink=eye_blink, frame_idx=frame_idx, pointer_target=pointer_target)

    if caption:
        cap_w = min(1050, max(420, len(caption) * 14 + 60))
        cx_sub = W // 2
        cv2.rectangle(img, (cx_sub - cap_w // 2, 650), (cx_sub + cap_w // 2, 702), (15, 20, 30), -1)
        cv2.rectangle(img, (cx_sub - cap_w // 2, 650), (cx_sub + cap_w // 2, 702), (241, 102, 99), 2, cv2.LINE_AA)
        (tw, th), _ = cv2.getTextSize(caption, cv2.FONT_HERSHEY_SIMPLEX, 0.62, 2)
        cv2.putText(img, caption, (cx_sub - tw // 2, 682), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)

    return img


def _load_strokes_from_db(character_id: int) -> Optional[List[List[Dict[str, float]]]]:
    """Load current reference_strokes from MySQL so videos never render stale JSON files."""
    try:
        from main import get_db_connection, _valid_strokes
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT reference_strokes FROM characters WHERE id = %s", (character_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row or not row.get("reference_strokes"):
            return None
        raw = row["reference_strokes"]
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        valid = _valid_strokes(parsed)
        return valid if valid else None
    except Exception:
        return None


def _render_lesson_video(
    lesson_id: int = 61,
    character_id: int = 2,
    output_path: Optional[str] = None,
    overwrite: bool = False,
) -> str:
    """
    Generates a full MP4 lesson tutorial video for the specified lesson and character.
    Supports Japanese Hiragana, Sanskrit Devanagari, Tamil, and Simplified Chinese.
    Internal renderer writes only to the provided temporary output path.
    """
    start_time = time.time()
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    config = LESSON_VIDEO_CONFIGS.get((lesson_id, character_id), LESSON_VIDEO_CONFIGS[(61, 2)])

    if output_path is None:
        filename = config.get("default_filename", f"lesson_{lesson_id}_char_{character_id}.mp4")
        output_path = str(VIDEOS_DIR / filename)

    # Prefer live DB reference_strokes so updated geometry is always used; fall back to JSON file if DB unavailable.
    strokes_data = _load_strokes_from_db(character_id)
    if not strokes_data:
        char_strokes_file = DATA_DIR / f"char{character_id}_strokes.json"
        if not char_strokes_file.exists():
            char_strokes_file = DATA_DIR / "char2_strokes.json"
        with open(char_strokes_file, "r", encoding="utf-8") as f:
            strokes_data = json.load(f)["stroke_data"]

    script_segments = config["script_segments"]

    resampler = av.AudioResampler(format='s16', layout='stereo', rate=44100)
    audio_chunks = []
    seg_timings = []
    current_time_sec = 0.0

    try:
        female_audio_segments, selected_voice = _synthesize_windows_female_voice(script_segments)
        print(f"Narration voice: {selected_voice}")
    except Exception as voice_error:
        print(f"Windows female voice unavailable; keeping gTTS fallback: {voice_error}")
        female_audio_segments = None

    for seg_idx, seg in enumerate(script_segments):
        if female_audio_segments is not None:
            fp = io.BytesIO(female_audio_segments[seg_idx])
            audio_format = "wav"
        else:
            fp = io.BytesIO()
            gTTS(text=seg["text"], lang="en", slow=False).write_to_fp(fp)
            fp.seek(0)
            audio_format = "mp3"

        container = av.open(fp, format=audio_format)
        in_stream = container.streams.audio[0]
        
        seg_samples = 0
        for frame in container.decode(in_stream):
            for resampled in resampler.resample(frame):
                arr = resampled.to_ndarray()
                audio_chunks.append(arr)
                seg_samples += (arr.shape[1] // 2)

        container.close()

        ref_pron = seg.get("ref_pronunciation")
        if isinstance(ref_pron, dict) and ref_pron.get("text") and ref_pron.get("lang"):
            gap_samples = int(0.18 * 44100)
            audio_chunks.append(np.zeros((1, gap_samples * 2), dtype=np.int16))
            seg_samples += gap_samples
            ref_fp = io.BytesIO()
            gTTS(text=str(ref_pron["text"]), lang=str(ref_pron["lang"]), slow=False).write_to_fp(ref_fp)
            ref_fp.seek(0)
            ref_container = av.open(ref_fp, format="mp3")
            ref_stream = ref_container.streams.audio[0]
            ref_resampler = av.AudioResampler(format='s16', layout='stereo', rate=44100)
            for frame in ref_container.decode(ref_stream):
                for resampled in ref_resampler.resample(frame):
                    arr = resampled.to_ndarray()
                    audio_chunks.append(arr)
                    seg_samples += (arr.shape[1] // 2)
            ref_container.close()
        
        seg_duration = float(seg_samples) / 44100.0
        start_sec = current_time_sec
        end_sec = start_sec + seg_duration
        seg_timings.append({
            "segment": seg,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "duration": seg_duration
        })
        current_time_sec = end_sec

    raw_interleaved = np.concatenate(audio_chunks, axis=1)
    full_audio = raw_interleaved.reshape(2, -1, order='F')
    total_audio_samples = full_audio.shape[1]
    total_duration_sec = float(total_audio_samples) / 44100.0

    fps = 25
    total_video_frames = int(math.ceil(total_duration_sec * fps))
    mouth_envelope = 0.0
    SenseiKaiRenderer.prepare_lipsync_frames(full_audio, fps, total_video_frames)

    container_out = av.open(output_path, mode='w', format='mp4')
    try:
    
        v_stream = container_out.add_stream('h264', rate=fps)
        v_stream.width = 1280
        v_stream.height = 720
        v_stream.pix_fmt = 'yuv420p'
        v_stream.options = {'crf': '16', 'preset': 'fast'}

        a_stream = container_out.add_stream('aac', rate=44100)
        a_stream.layout = 'stereo'

        def is_blinking(f_idx):
            cycle = f_idx % 100
            return 88 <= cycle <= 94

        for f_idx in range(total_video_frames):
            t_sec = float(f_idx) / fps
        
            active_seg = seg_timings[-1]
            for s in seg_timings:
                if s["start_sec"] <= t_sec < s["end_sec"]:
                    active_seg = s
                    break
        
            seg_info = active_seg["segment"]
            stage = seg_info["stage"]
            stroke_idx = seg_info["stroke_idx"]
            caption = seg_info["text"]

            if stage == 'stroke' and stroke_idx is not None:
                seg_elapsed = t_sec - active_seg["start_sec"]
                seg_dur = active_seg["duration"]
                draw_start = 0.3
                draw_end = max(0.5, seg_dur - 0.4)
                if seg_elapsed < draw_start:
                    stroke_frac = 0.05
                elif seg_elapsed > draw_end:
                    stroke_frac = 1.0
                else:
                    stroke_frac = (seg_elapsed - draw_start) / (draw_end - draw_start)
            else:
                stroke_frac = 1.0

            # Drive the portrait mouth from actual narration samples at this
            # timestamp. A short RMS window follows spoken syllables and pauses.
            audio_start = min(total_audio_samples - 1, int(t_sec * 44100))
            audio_end = min(total_audio_samples, audio_start + int(44100 / fps * 2))
            audio_window = full_audio[:, audio_start:audio_end].astype(np.float32)
            rms = float(np.sqrt(np.mean(audio_window * audio_window))) if audio_window.size else 0.0
            rms_level = rms / 32768.0
            target_open = min(1.0, max(0.0, (rms_level - 0.006) / 0.085))
            envelope_rate = 0.62 if target_open > mouth_envelope else 0.34
            mouth_envelope += (target_open - mouth_envelope) * envelope_rate
            mouth_open = mouth_envelope

            eye_blink = is_blinking(f_idx)

            bgr_frame = render_scene_frame(
                stage=stage,
                stroke_idx=stroke_idx,
                stroke_frac=stroke_frac,
                caption=caption,
                mouth_open=mouth_open,
                eye_blink=eye_blink,
                frame_idx=f_idx,
                strokes_data=strokes_data,
                char_label=config.get("char_label", "A (/a/)"),
                script_title=config.get("script_title", "STROKESPEAK LESSON"),
                ipa_text=config.get("ipa_text", "/a/"),
                unit_subtitle=config.get("unit_subtitle", "Foundation Unit"),
                viseme_desc=config.get("viseme_desc", "Open, Relaxed, Unrounded"),
                tract_desc=config.get("tract_desc", "Clear Airflow"),
                target_desc=config.get("target_desc", "PHONETIC TARGET"),
                step_names=config.get("step_names", {}),
                complete_title=config.get("complete_title", "ALL STROKES COMPLETE!"),
            )

            v_frame = av.VideoFrame.from_ndarray(bgr_frame, format='bgr24')
            v_frame.pts = f_idx
            for packet in v_stream.encode(v_frame):
                container_out.mux(packet)

        for packet in v_stream.encode():
            container_out.mux(packet)

        chunk_size = 1024
        curr_sample = 0
        while curr_sample < total_audio_samples:
            end_sample = min(curr_sample + chunk_size, total_audio_samples)
            block = np.ascontiguousarray(full_audio[:, curr_sample:end_sample])
            af = av.AudioFrame.from_ndarray(block, format='s16p', layout='stereo')
            af.rate = 44100
            af.pts = curr_sample
            for packet in a_stream.encode(af):
                container_out.mux(packet)
            curr_sample = end_sample

        for packet in a_stream.encode():
            container_out.mux(packet)

    finally:
        SenseiKaiRenderer.clear_lipsync_frames()
        container_out.close()
    
    elapsed = time.time() - start_time
    file_size_kb = os.path.getsize(output_path) / 1024.0
    print(f"Video generated at {output_path} ({file_size_kb:.1f} KB in {elapsed:.2f}s)")
    return output_path

def _validate_rendered_video(video_path: Path) -> None:
    """Decode both streams before a staged MP4 can be published."""
    container = None
    try:
        container = av.open(str(video_path), mode="r")
        if not list(container.streams.video) or not list(container.streams.audio):
            raise ValueError("Rendered MP4 must contain video and audio streams.")
        video_frames = sum(1 for _ in container.decode(video=0))
        container.seek(0)
        audio_frames = sum(1 for _ in container.decode(audio=0))
        if video_frames < 1 or audio_frames < 1:
            raise ValueError("Rendered MP4 has an empty or undecodable stream.")
    finally:
        if container is not None:
            container.close()


def publish_video_safely(staged_path: Path, output_path: Path, overwrite: bool = False) -> Path:
    """Atomically publish a staged video, failing closed on collisions."""
    staged_path, output_path = Path(staged_path), Path(output_path)
    if not staged_path.is_file() or staged_path.stat().st_size == 0:
        raise ValueError("Staged video is missing or empty.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if overwrite:
        os.replace(str(staged_path), str(output_path))
    elif os.name == "nt":
        # Windows rename is atomic and fails if destination already exists.
        os.rename(str(staged_path), str(output_path))
    else:
        # A same-volume hard link atomically refuses an existing destination.
        os.link(str(staged_path), str(output_path))
        staged_path.unlink()
    return output_path


MANIFEST_PATH = DATA_DIR / "video_reference_manifest.json"


def _compute_current_reference_fingerprint(character_id: int) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (reference_sha256, script_code, character_text) from MySQL for character_id."""
    try:
        from main import get_db_connection, _valid_strokes
        from app.reference_paths import reference_path_fingerprint
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT c.character_text, l.script_code, c.reference_strokes, c.reference_strokes_svg "
            "FROM characters c JOIN languages l ON l.id = c.language_id WHERE c.id = %s",
            (character_id,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return None, None, None
        ref = json.loads(row["reference_strokes"]) if isinstance(row["reference_strokes"], str) else (row["reference_strokes"] or [])
        svg = json.loads(row["reference_strokes_svg"]) if isinstance(row["reference_strokes_svg"], str) else (row["reference_strokes_svg"] or {})
        fp = reference_path_fingerprint(_valid_strokes(ref), svg)
        return fp, row["script_code"], row["character_text"]
    except Exception:
        return None, None, None


def record_video_reference_manifest(
    lesson_id: int,
    character_id: int,
    video_path: Path,
    status: str = "published",
    note: Optional[str] = None,
) -> Dict[str, object]:
    """Record the exact reference-geometry fingerprint used when generating a lesson video."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    manifest: Dict[str, object] = {}
    if MANIFEST_PATH.is_file():
        try:
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            manifest = {}

    ref_fp, script_code, char_text = _compute_current_reference_fingerprint(character_id)
    strokes_file = DATA_DIR / f"char{character_id}_strokes.json"
    strokes_json_sha256 = (
        hashlib.sha256(strokes_file.read_bytes()).hexdigest() if strokes_file.is_file() else None
    )
    entry: Dict[str, object] = {
        "lesson_id": lesson_id,
        "character_id": character_id,
        "script_code": script_code,
        "character_text": char_text,
        "video_filename": Path(video_path).name,
        "reference_sha256": ref_fp,
        "strokes_json_sha256": strokes_json_sha256,
        "status": status,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if note:
        entry["note"] = note
    manifest[str(lesson_id)] = entry
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return entry


def detect_video_reference_drift() -> List[Dict[str, object]]:
    """Compare recorded video fingerprints against current MySQL reference geometry."""
    if not MANIFEST_PATH.is_file():
        return []
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    report: List[Dict[str, object]] = []
    for key, entry in manifest.items():
        cid = entry.get("character_id")
        current_fp, _, _ = _compute_current_reference_fingerprint(int(cid)) if cid else (None, None, None)
        recorded_fp = entry.get("reference_sha256")
        report.append({
            "lesson_id": entry.get("lesson_id", key),
            "character_id": cid,
            "character_text": entry.get("character_text"),
            "status": entry.get("status"),
            "recorded_reference_sha256": recorded_fp,
            "current_reference_sha256": current_fp,
            "drifted": bool(recorded_fp and current_fp and recorded_fp != current_fp),
        })
    return report


def generate_lesson_video(
    lesson_id: int = 61,
    character_id: int = 2,
    output_path: Optional[str] = None,
    overwrite: bool = False,
) -> str:
    """Render to a temporary sibling, validate, and publish atomically."""
    config = LESSON_VIDEO_CONFIGS.get((lesson_id, character_id), LESSON_VIDEO_CONFIGS[(61, 2)])
    if output_path is None:
        filename = config.get("default_filename", f"lesson_{lesson_id}_char_{character_id}.mp4")
        output_path = str(VIDEOS_DIR / filename)
    destination = Path(output_path)
    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Video already exists and was not replaced: {destination}. "
            "Pass overwrite=True to explicitly authorize replacement."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, staged_name = tempfile.mkstemp(
        prefix=f".{destination.stem}.", suffix=".tmp.mp4", dir=str(destination.parent)
    )
    os.close(descriptor)
    staged = Path(staged_name)
    try:
        _render_lesson_video(
            lesson_id=lesson_id, character_id=character_id,
            output_path=str(staged), overwrite=True,
        )
        _validate_rendered_video(staged)
        publish_video_safely(staged, destination, overwrite=overwrite)
        record_video_reference_manifest(lesson_id=lesson_id, character_id=character_id, video_path=destination, status="published")
        return str(destination)
    finally:
        try:
            staged.unlink(missing_ok=True)
        except OSError:
            pass

