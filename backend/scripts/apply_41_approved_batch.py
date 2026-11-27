"""
StrokeSpeak — Safe Backup & Apply Script for Staged Sanskrit (10) & Tamil (12) References + Candidate CNNs
1. Backs up all 41 live MySQL character rows before any write.
2. Backs up production Sanskrit & Tamil v1 CNN models/metadata before promotion.
3. Imports the 10 staged Sanskrit candidates and 12 Codex Tamil candidates into MySQL.
4. Promotes sanskrit_devanagari_candidate_v2 and tamil_candidate_v2 to production v1 paths.
"""

import glob
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from main import get_db_connection

BACKUP_DIR = BACKEND / "data" / "reference_strokes" / "backups"
MODELS_DIR = BACKEND / "app" / "ml" / "models"
CAND_MODELS_DIR = MODELS_DIR / "candidates"
MODEL_BACKUP_DIR = MODELS_DIR / "backups" / "pre_v2_20261126"
BATCH_FILE = (
    BACKEND
    / "data"
    / "reference_strokes"
    / "batch-review-41-consolidated"
    / "sanskrit_import_batch.json"
)

TARGET_IDS = [
    2, 28, 29, 30, 3, 31, 32, 33, 34, 35,
    216, 217, 218, 219, 220, 221, 223, 224, 225, 226,
    25, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120,
    241, 242, 243, 244, 245, 247, 248, 249, 252,
]


def backup_mysql_41():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / "before_41_apply_20261126.json"
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    placeholders = ",".join(["%s"] * len(TARGET_IDS))
    cur.execute(
        f"SELECT id, language_id, character_text, meaning, pronunciation_text, reference_strokes, reference_strokes_svg FROM characters WHERE id IN ({placeholders}) ORDER BY id",
        tuple(TARGET_IDS),
    )
    rows = cur.fetchall()
    conn.close()
    backup_path.write_text(
        json.dumps(
            {
                "backed_up_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "row_count": len(rows),
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Backed up {len(rows)} MySQL character rows -> {backup_path}")
    return backup_path


def apply_reference_updates():
    updates = []

    # 1. 10 Sanskrit staged candidates
    sa_batch = json.loads(BATCH_FILE.read_text(encoding="utf-8"))
    for rec in sa_batch["records"]:
        updates.append(
            (
                rec["character_id"],
                rec["character_text"],
                rec["reference_strokes"],
                rec["reference_strokes_svg"],
            )
        )

    # 2. 12 Tamil Codex staged candidates
    ta_dirs = [BACKEND / "data/reference_strokes/tamil/a-id25-review"] + sorted(
        Path(p)
        for p in glob.glob(str(BACKEND / "data/reference_strokes/tamil/vowel-review/*"))
        if Path(p).is_dir()
    )
    for dpath in ta_dirs:
        cand_f = dpath / "staged-candidate.json"
        if not cand_f.is_file():
            continue
        c = json.loads(cand_f.read_text(encoding="utf-8"))
        cid = int(c["character_id"])
        ch = c.get("character") or c.get("character_text")
        pts = c.get("points") or c.get("reference_strokes")
        svg = c.get("svg") or c.get("reference_strokes_svg")
        if svg and "watermark_align_to_reference" not in svg:
            svg["watermark_align_to_reference"] = True
        updates.append((cid, ch, pts, svg))

    conn = get_db_connection()
    cur = conn.cursor()
    updated = 0
    try:
        for cid, ch, pts, svg in updates:
            cur.execute(
                "UPDATE characters SET reference_strokes = %s, reference_strokes_svg = %s WHERE id = %s",
                (
                    json.dumps(pts, ensure_ascii=False),
                    json.dumps(svg, ensure_ascii=False),
                    cid,
                ),
            )
            updated += cur.rowcount
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
    print(f"Updated {updated} character rows in MySQL (10 Sanskrit + 12 Tamil).")


def promote_candidate_models():
    import numpy as np
    import torch

    MODEL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for prod_prefix, cand_prefix in (
        ("sanskrit_devanagari", "sanskrit_devanagari_candidate_v2"),
        ("tamil", "tamil_candidate_v2"),
    ):
        for suffix in ("_v1.pt", "_metadata.json", "_weights.npz", "_weights.pt"):
            prod_file = MODELS_DIR / f"{prod_prefix}{suffix}"
            if prod_file.is_file():
                backup_file = MODEL_BACKUP_DIR / prod_file.name
                if not backup_file.exists():
                    shutil.copy2(prod_file, backup_file)

        cand_pt = CAND_MODELS_DIR / f"{cand_prefix}.pt"
        cand_meta = CAND_MODELS_DIR / f"{cand_prefix}_metadata.json"
        if cand_pt.is_file():
            dest_pt = MODELS_DIR / f"{prod_prefix}_v1.pt"
            shutil.copy2(cand_pt, dest_pt)
            # Keep NumPy NPZ fallback and state_dict synchronized with promoted TorchScript model
            loaded = torch.jit.load(str(dest_pt), map_location="cpu")
            sd = loaded.state_dict()
            torch.save(sd, MODELS_DIR / f"{prod_prefix}_weights.pt")
            np.savez(
                MODELS_DIR / f"{prod_prefix}_weights.npz",
                **{k: v.cpu().numpy() for k, v in sd.items()},
            )
        if cand_meta.is_file():
            meta = json.loads(cand_meta.read_text(encoding="utf-8"))
            meta["status"] = "production_promoted"
            meta["model_file"] = f"{prod_prefix}_v1.pt"
            meta["weights_file"] = f"{prod_prefix}_weights.pt"
            meta["input_dimensions"] = [1, 1, 32, 32]
            meta["promoted_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            (MODELS_DIR / f"{prod_prefix}_metadata.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        print(f"Promoted {cand_prefix} -> {prod_prefix}_v1.pt (backup in {MODEL_BACKUP_DIR})")


def main():
    backup_mysql_41()
    apply_reference_updates()
    promote_candidate_models()


if __name__ == "__main__":
    main()
