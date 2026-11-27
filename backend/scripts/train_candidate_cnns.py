"""
StrokeSpeak — Candidate CNN Training & Validation Pipeline (Non-Destructive)
Trains improved TorchScript CNN candidate models for Sanskrit Devanagari (10)
and Tamil (12) under backend/app/ml/models/candidates/ WITHOUT overwriting
production models.

Uses:
1. Authentic staged stroke trajectories (Sanskrit 10 staged + Tamil 12 Codex staged)
   with writer-disjoint handwriting variations on the exact 700x320 StrokeSpeak canvas
   (round caps, round joins, varying brush widths 6px-14px, per-stroke affine + spline jitter).
2. Independent cross-domain typographic glyphs via Windows System.Drawing fonts
   (strictly separated by font family/style between train and independent validation).
3. Strict zero-leakage evaluation on:
   - Canonical 700x320 10px-brush renders (including Codex's Tamil cnn-canvas.png files)
   - Held-out writer-disjoint handwriting test split
   - Unseen Nirmala UI font renders (independent domain check)
"""

import base64
import glob
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.ml.preprocessing import TARGET_SIZE, preprocess_handwriting_image

CANDIDATES_DIR = BACKEND / "app" / "ml" / "models" / "candidates"
MODELS_DIR = BACKEND / "app" / "ml" / "models"

SANSKRIT_CLASSES = ["अ", "आ", "इ", "ई", "उ", "ऊ", "ए", "ऐ", "ओ", "औ"]
TAMIL_CLASSES = ["அ", "ஆ", "இ", "ஈ", "உ", "ஊ", "எ", "ஏ", "ஐ", "ஒ", "ஓ", "ஔ"]


class ScriptCNN(nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.25),
            nn.Linear(64 * 4 * 4, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


def render_strokes_to_canvas(
    strokes, width: int = 700, height: int = 320, area: int = 320, thickness: int = 10
) -> np.ndarray:
    """Render normalized [0..1] strokes onto the 700x320 StrokeSpeak canvas."""
    factor = 3
    canvas = np.full((height * factor, width * factor, 3), 255, np.uint8)
    for stroke in strokes:
        coords = np.array(
            [
                [(width - area) / 2 + p["x"] * area, (height - area) / 2 + p["y"] * area]
                for p in stroke
            ],
            dtype=np.float64,
        )
        if not len(coords):
            continue
        pts = np.rint(coords * factor).astype(np.int32)
        if len(pts) >= 2:
            cv2.polylines(canvas, [pts], False, (0, 0, 0), thickness * factor)
        for pt in pts:
            cv2.circle(canvas, tuple(pt), max(1, thickness * factor // 2), (0, 0, 0), -1)
    return cv2.resize(canvas, (width, height), interpolation=cv2.INTER_AREA)


def perturb_strokes_for_writer(strokes, rng: random.Random):
    """Apply realistic per-stroke and global human handwriting variation."""
    g_angle = rng.uniform(-0.18, 0.18)
    g_sx = rng.uniform(0.65, 1.16)
    g_sy = rng.uniform(0.84, 1.14)
    g_shear = rng.uniform(-0.14, 0.14)
    cos_a, sin_a = np.cos(g_angle), np.sin(g_angle)

    out = []
    for stroke in strokes:
        st_dx = rng.uniform(-0.025, 0.025)
        st_dy = rng.uniform(-0.025, 0.025)
        st_sx = rng.uniform(0.93, 1.07)
        st_sy = rng.uniform(0.93, 1.07)
        amp_x = rng.uniform(0.0, 0.012)
        amp_y = rng.uniform(0.0, 0.012)
        phase = rng.uniform(0, 6.28)
        n = max(1, len(stroke))
        new_st = []
        for idx, p in enumerate(stroke):
            px = (p["x"] - 0.5) * st_sx + st_dx
            py = (p["y"] - 0.5) * st_sy + st_dy
            # Smooth low-frequency hand wobble
            t = idx / max(1, n - 1)
            px += amp_x * np.sin(2 * np.pi * t + phase)
            py += amp_y * np.cos(2 * np.pi * t + phase)
            # Global scale + shear + rotation
            px = px * g_sx + py * g_shear
            py = py * g_sy
            rx = px * cos_a - py * sin_a + 0.5
            ry = px * sin_a + py * cos_a + 0.5
            new_st.append({"x": float(rx), "y": float(ry)})
        out.append(new_st)
    return out


def render_font_glyphs(chars, font_specs):
    """Render clean font glyphs via Windows System.Drawing for cross-domain validation/training."""
    results = {ch: [] for ch in chars}
    with tempfile.TemporaryDirectory(prefix="strokespeak_fonts_") as td:
        td_path = Path(td)
        jobs = []
        for ch_idx, ch in enumerate(chars):
            for f_idx, (font_name, style_name, size_px) in enumerate(font_specs):
                out_png = td_path / f"g_{ch_idx}_{f_idx}.png"
                jobs.append(
                    {
                        "char": ch,
                        "font": font_name,
                        "style": style_name,
                        "size": size_px,
                        "out": str(out_png),
                    }
                )
        jobs_file = td_path / "jobs.json"
        jobs_file.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
        ps_file = td_path / "render.ps1"
        ps_file.write_text(
            """
param([string]$JobsPath)
Add-Type -AssemblyName System.Drawing
$jobs = Get-Content -Raw -LiteralPath $JobsPath -Encoding UTF8 | ConvertFrom-Json
foreach ($job in $jobs) {
    $bmp = New-Object System.Drawing.Bitmap 320, 320
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
    $g.Clear([System.Drawing.Color]::White)
    $style = [System.Drawing.FontStyle]::Regular
    if ($job.style -eq 'Bold') { $style = [System.Drawing.FontStyle]::Bold }
    elseif ($job.style -eq 'Italic') { $style = [System.Drawing.FontStyle]::Italic }
    try {
        $font = New-Object System.Drawing.Font($job.font, [float]$job.size, $style)
    } catch {
        $font = New-Object System.Drawing.Font('Nirmala UI', [float]$job.size, [System.Drawing.FontStyle]::Regular)
    }
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = [System.Drawing.StringAlignment]::Center
    $sf.LineAlignment = [System.Drawing.StringAlignment]::Center
    $rect = New-Object System.Drawing.RectangleF(0, 0, 320, 320)
    $g.DrawString([string]$job.char, $font, [System.Drawing.Brushes]::Black, $rect, $sf)
    $bmp.Save([string]$job.out, [System.Drawing.Imaging.ImageFormat]::Png)
    $font.Dispose()
    $g.Dispose()
    $bmp.Dispose()
}
""",
            encoding="utf-8",
        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_file), str(jobs_file)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if res.returncode != 0:
            print(f"Font render warning: {res.stderr}")
        for job in jobs:
            p = Path(job["out"])
            if p.is_file():
                img = cv2.imread(str(p))
                if img is not None:
                    results[job["char"]].append(img)
    return results


def load_sanskrit_sources():
    """Load the 10 staged Sanskrit candidates + Lipi secondary geometry."""
    primary = {}
    for f in sorted(
        glob.glob(
            str(BACKEND / "data/reference_strokes/review-pending/sanskrit-*_20261126/candidate.json")
        )
    ):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        primary[d["character_text"]] = d["reference_strokes"]

    lipi_extra = {}
    lipi_file = (
        BACKEND
        / "data/reference_strokes/review-pending/lipi-composed-vowels_20261126/candidate_batch.json"
    )
    if lipi_file.is_file():
        batch = json.loads(lipi_file.read_text(encoding="utf-8"))
        for item in batch.get("candidates", batch.get("targets", [])):
            ch = item.get("character") or item.get("character_text")
            pts = item.get("points") or item.get("reference_strokes")
            if ch in SANSKRIT_CLASSES and pts:
                lipi_extra[ch] = pts
    return primary, lipi_extra


def load_tamil_sources():
    """Read Codex's 12 staged Tamil candidates READ-ONLY."""
    primary = {}
    canvases = {}
    ta_dirs = [BACKEND / "data/reference_strokes/tamil/a-id25-review"] + sorted(
        Path(p) for p in glob.glob(str(BACKEND / "data/reference_strokes/tamil/vowel-review/*"))
        if Path(p).is_dir()
    )
    for dpath in ta_dirs:
        cand_f = dpath / "staged-candidate.json"
        canvas_f = dpath / "cnn-canvas.png"
        if not cand_f.is_file():
            continue
        c = json.loads(cand_f.read_text(encoding="utf-8"))
        ch = c.get("character") or c.get("character_text")
        pts = c.get("points") or c.get("reference_strokes")
        if ch in TAMIL_CLASSES and pts:
            primary[ch] = pts
            if canvas_f.is_file():
                canvases[ch] = cv2.imread(str(canvas_f))
    return primary, canvases


def build_splits(classes, primary_strokes, extra_strokes=None, seed_base=100):
    """
    Build strictly writer-disjoint train / val / test tensors + independent font val.
    """
    train_fonts = render_font_glyphs(
        classes,
        [
            ("Arial Unicode MS", "Regular", 150),
            ("Nirmala UI", "Bold", 155),
        ],
    )
    indep_fonts = render_font_glyphs(
        classes,
        [
            ("Nirmala UI", "Regular", 150),
            ("Nirmala UI Semilight", "Regular", 150),
        ],
    )

    train_x, train_y = [], []
    val_x, val_y = [], []
    test_x, test_y = [], []
    indep_x, indep_y = [], []

    for cls_idx, ch in enumerate(classes):
        strokes = primary_strokes[ch]
        # 1. Canonical 10px render -> ONLY in independent eval check (not in train!)
        # Train uses writer seeds 0..17 (18 synthetic writers * 3 thicknesses = 54 + variations)
        for w_seed in range(18):
            rng = random.Random(seed_base + cls_idx * 1000 + w_seed)
            for _ in range(3):
                p_strokes = perturb_strokes_for_writer(strokes, rng)
                thick = rng.choice([6, 8, 10, 12, 14])
                img = render_strokes_to_canvas(p_strokes, thickness=thick)
                t = preprocess_handwriting_image(img, TARGET_SIZE)[0, 0]
                train_x.append(t)
                train_y.append(cls_idx)

        # Extra authentic stroke source (e.g. Lipi) in training if available
        if extra_strokes and ch in extra_strokes:
            for w_seed in range(6):
                rng = random.Random(seed_base + 50000 + cls_idx * 100 + w_seed)
                p_strokes = perturb_strokes_for_writer(extra_strokes[ch], rng)
                thick = rng.choice([7, 9, 11, 13])
                img = render_strokes_to_canvas(p_strokes, thickness=thick)
                train_x.append(preprocess_handwriting_image(img, TARGET_SIZE)[0, 0])
                train_y.append(cls_idx)

        # Train font styles + morphological thickness variations
        for f_img in train_fonts.get(ch, []):
            t = preprocess_handwriting_image(f_img, TARGET_SIZE)[0, 0]
            train_x.append(t)
            train_y.append(cls_idx)
            for k in (2, 3):
                kernel = np.ones((k, k), np.uint8)
                er = cv2.erode(f_img, kernel, iterations=1)  # darker/thicker black ink
                dl = cv2.dilate(f_img, kernel, iterations=1)  # thinner black ink
                train_x.append(preprocess_handwriting_image(er, TARGET_SIZE)[0, 0])
                train_y.append(cls_idx)
                train_x.append(preprocess_handwriting_image(dl, TARGET_SIZE)[0, 0])
                train_y.append(cls_idx)

        # Val: unseen writer seeds 18..20 (3 writers * 2 thicknesses = 6)
        for w_seed in range(18, 21):
            rng = random.Random(seed_base + cls_idx * 1000 + w_seed)
            for thick in (8, 12):
                p_strokes = perturb_strokes_for_writer(strokes, rng)
                img = render_strokes_to_canvas(p_strokes, thickness=thick)
                val_x.append(preprocess_handwriting_image(img, TARGET_SIZE)[0, 0])
                val_y.append(cls_idx)

        # Held-out Test: unseen writer seeds 21..25 (5 writers * 2 thicknesses = 10)
        for w_seed in range(21, 26):
            rng = random.Random(seed_base + cls_idx * 1000 + w_seed)
            for thick in (7, 11):
                p_strokes = perturb_strokes_for_writer(strokes, rng)
                img = render_strokes_to_canvas(p_strokes, thickness=thick)
                test_x.append(preprocess_handwriting_image(img, TARGET_SIZE)[0, 0])
                test_y.append(cls_idx)

        # Independent Font Test (unseen Nirmala UI Regular & Semilight)
        for f_img in indep_fonts.get(ch, []):
            indep_x.append(preprocess_handwriting_image(f_img, TARGET_SIZE)[0, 0])
            indep_y.append(cls_idx)

    def to_nchw(xs, ys):
        return (
            np.expand_dims(np.array(xs, dtype=np.float32), axis=1),
            np.array(ys, dtype=np.int64),
        )

    return to_nchw(train_x, train_y), to_nchw(val_x, val_y), to_nchw(test_x, test_y), to_nchw(indep_x, indep_y)


def evaluate_torchscript(model, x_arr, y_arr):
    with torch.no_grad():
        logits = model(torch.from_numpy(x_arr))
        preds = logits.argmax(dim=1).numpy()
    correct = int((preds == y_arr).sum())
    total = len(y_arr)
    return correct, total, round(100.0 * correct / max(1, total), 2), preds


def train_candidate(script_code, language_name, classes, primary_strokes, extra_strokes=None, canonical_canvases=None):
    print(f"\n=== Training Candidate CNN: {language_name} ({script_code}, {len(classes)} classes) ===")
    torch.manual_seed(42)
    np.random.seed(42)
    random.seed(42)

    (tr_x, tr_y), (va_x, va_y), (te_x, te_y), (in_x, in_y) = build_splits(
        classes, primary_strokes, extra_strokes=extra_strokes
    )
    print(f"Splits -> Train: {len(tr_x)}, Val: {len(va_x)}, Held-out Test: {len(te_x)}, Indep Font: {len(in_x)}")

    model = ScriptCNN(len(classes))
    opt = optim.Adam(model.parameters(), lr=0.0012, weight_decay=1e-4)
    crit = nn.CrossEntropyLoss()
    loader = DataLoader(TensorDataset(torch.from_numpy(tr_x), torch.from_numpy(tr_y)), batch_size=32, shuffle=True)

    best_val_acc = -1.0
    best_state = None
    for epoch in range(28):
        model.train()
        for bx, by in loader:
            opt.zero_grad()
            loss = crit(model(bx), by)
            loss.backward()
            opt.step()
        model.eval()
        _, _, val_acc, _ = evaluate_torchscript(model, va_x, va_y)
        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    model.eval()

    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    prefix = "sanskrit_devanagari_candidate_v2" if script_code == "sa-devanagari" else "tamil_candidate_v2"
    ts_path = CANDIDATES_DIR / f"{prefix}.pt"
    scripted = torch.jit.script(model)
    scripted.save(str(ts_path))

    # Evaluate candidate on all splits + canonical 700x320 renders
    te_ok, te_tot, te_acc, _ = evaluate_torchscript(scripted, te_x, te_y)
    in_ok, in_tot, in_acc, _ = evaluate_torchscript(scripted, in_x, in_y)

    # Canonical 700x320 10px renders (or Codex cnn-canvas.png for Tamil)
    canon_results = []
    canon_pass = 0
    for idx, ch in enumerate(classes):
        if canonical_canvases and ch in canonical_canvases:
            img = canonical_canvases[ch]
        else:
            img = render_strokes_to_canvas(primary_strokes[ch], thickness=10)
        tensor = torch.from_numpy(preprocess_handwriting_image(img, TARGET_SIZE))
        with torch.no_grad():
            probs = torch.softmax(scripted(tensor), dim=1)[0].numpy()
        pred_idx = int(np.argmax(probs))
        conf = round(float(probs[pred_idx]) * 100.0, 2)
        matched = pred_idx == idx
        if matched:
            canon_pass += 1
        canon_results.append(
            {
                "character": ch,
                "predicted": classes[pred_idx],
                "confidence": conf,
                "is_match": matched,
            }
        )

    meta = {
        "model_name": f"StrokeSpeak {language_name} Candidate CNN",
        "version": "2.0.0-candidate",
        "status": "candidate_pending_approval",
        "script_code": script_code,
        "language": language_name,
        "classes": classes,
        "num_classes": len(classes),
        "input_dimensions": [1, 1, 32, 32],
        "input_size": [1, 1, 32, 32],
        "best_val_accuracy_pct": best_val_acc,
        "heldout_writer_test": {"correct": te_ok, "total": te_tot, "accuracy_pct": te_acc},
        "independent_font_test": {"correct": in_ok, "total": in_tot, "accuracy_pct": in_acc},
        "canonical_700x320_10px": {
            "passed": canon_pass,
            "total": len(classes),
            "accuracy_pct": round(100.0 * canon_pass / len(classes), 2),
            "per_character": canon_results,
        },
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    meta_path = CANDIDATES_DIR / f"{prefix}_metadata.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"Candidate {prefix}: Val={best_val_acc}% | HeldOut={te_ok}/{te_tot} ({te_acc}%) | "
        f"IndepFont={in_ok}/{in_tot} ({in_acc}%) | Canonical700x320={canon_pass}/{len(classes)}"
    )
    return meta


def main():
    sa_primary, sa_lipi = load_sanskrit_sources()
    ta_primary, ta_canvases = load_tamil_sources()

    sa_meta = train_candidate(
        "sa-devanagari",
        "Sanskrit (Devanagari)",
        SANSKRIT_CLASSES,
        sa_primary,
        extra_strokes=sa_lipi,
    )
    ta_meta = train_candidate(
        "ta",
        "Tamil",
        TAMIL_CLASSES,
        ta_primary,
        canonical_canvases=ta_canvases,
    )
    summary = {"sanskrit_candidate": sa_meta, "tamil_candidate": ta_meta}
    (CANDIDATES_DIR / "candidate_training_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("\nSaved candidate models & summary under backend/app/ml/models/candidates/")


if __name__ == "__main__":
    main()
