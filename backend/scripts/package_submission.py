"""Safe StrokeSpeak submission packaging script (dry-run inventory by default; pass --create-zip when ready)."""
import argparse
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCLUDE_DIRS = {
    ".venv", "venv", "node_modules", "__pycache__", ".git", ".pytest_cache",
    "dist", "scratch", "db_backups", "backups", ".vscode",
}
EXCLUDE_FILES = {".env", ".DS_Store", "Thumbs.db"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".log", ".tmp"}


def collect_submission_files() -> list[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith("."))
        for fn in sorted(filenames):
            if fn in EXCLUDE_FILES or fn.endswith(tuple(EXCLUDE_EXTS)) or fn.startswith(".env.") and fn != ".env.example":
                continue
            p = Path(dirpath) / fn
            files.append(p)
    return files


def main():
    parser = argparse.ArgumentParser(description="Prepare clean StrokeSpeak submission inventory or ZIP.")
    parser.add_argument("--create-zip", action="store_true", help="Explicitly create StrokeSpeak_Submission.zip")
    parser.add_argument("--output", default=str(ROOT / "StrokeSpeak_Submission.zip"))
    args = parser.parse_args()

    files = collect_submission_files()
    total_mb = sum(p.stat().st_size for p in files) / (1024 * 1024)
    print(f"Clean submission inventory: {len(files)} files ({total_mb:.2f} MB)")
    print("Excluded: .env, .venv, node_modules, dist, scratch, db_backups, backups, logs, caches.")

    if not args.create_zip:
        print("Dry-run only (pass --create-zip after Codex integration is reconciled).")
        return

    out_path = Path(args.output)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(p, arcname=str(p.relative_to(ROOT)))
    print(f"Created submission ZIP: {out_path} ({out_path.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
