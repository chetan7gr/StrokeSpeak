"""Bulk multilingual video generation with explicit overwrite opt-in."""
import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

import av

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))
from app.ml.video_generator import (
    VIDEOS_DIR, _validate_rendered_video, generate_lesson_video, publish_video_safely,
)


def verify_video(path: Path) -> None:
    assert path.exists(), f"Video file not found: {path}"
    size_kb = path.stat().st_size / 1024.0
    container = av.open(str(path))
    try:
        videos, audios = list(container.streams.video), list(container.streams.audio)
        assert videos, f"No video stream in {path}"
        assert audios, f"No audio stream in {path}"
        video, audio = videos[0], audios[0]
        duration = float(container.duration or 0) / av.time_base if container.duration else 0
        print(f"  [PASS] {path.name}")
        print(f"         Resolution: {video.width}x{video.height}, FPS: {video.average_rate}")
        print(f"         Codec: {video.codec_context.name}, Audio: {audio.codec_context.name} ({audio.rate} Hz)")
        print(f"         Duration: {duration:.2f}s, Size: {size_kb:.1f} KB")
    finally:
        container.close()


def planned_outputs(videos_dir: Path = VIDEOS_DIR) -> list[Path]:
    return [
        videos_dir / "sa_devanagari_216_lesson339.mp4",
        videos_dir / "ta_25_lesson55.mp4",
        videos_dir / "ta_25_lesson223.mp4",
        videos_dir / "zh_hans_241_lesson348.mp4",
    ]


def preflight_outputs(outputs: list[Path], overwrite: bool) -> None:
    existing = [path for path in outputs if path.exists()]
    if existing and not overwrite:
        names = "\n".join(f"  - {path}" for path in existing)
        raise FileExistsError(
            "Batch stopped before generation; target files already exist:\n"
            f"{names}\nPass --overwrite to explicitly authorize replacement."
        )


def copy_video_safely(source: Path, destination: Path, overwrite: bool = False) -> Path:
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, staged_name = tempfile.mkstemp(
        prefix=f".{destination.stem}.", suffix=".tmp.mp4", dir=str(destination.parent)
    )
    os.close(descriptor)
    staged = Path(staged_name)
    try:
        shutil.copyfile(source, staged)
        _validate_rendered_video(staged)
        publish_video_safely(staged, destination, overwrite=overwrite)
        return destination
    finally:
        try:
            staged.unlink(missing_ok=True)
        except OSError:
            pass


def main(overwrite: bool = False) -> None:
    outputs = planned_outputs()
    preflight_outputs(outputs, overwrite)
    print("=" * 60, "\nGenerating StrokeSpeak multilingual teacher videos")
    if overwrite:
        print("Explicit overwrite authorization: enabled")
    sa_path, ta_path, ta_path_223, zh_path = outputs

    print(f"\n1. Sanskrit Devanagari: {sa_path.name}")
    generate_lesson_video(lesson_id=339, character_id=216, output_path=str(sa_path), overwrite=overwrite)
    verify_video(sa_path)

    print(f"\n2. Tamil: {ta_path.name}")
    generate_lesson_video(lesson_id=55, character_id=25, output_path=str(ta_path), overwrite=overwrite)
    verify_video(ta_path)
    print(f"Publishing Tamil lesson 223: {ta_path_223.name}")
    copy_video_safely(ta_path, ta_path_223, overwrite=overwrite)
    verify_video(ta_path_223)

    print(f"\n3. Simplified Chinese: {zh_path.name}")
    generate_lesson_video(lesson_id=348, character_id=241, output_path=str(zh_path), overwrite=overwrite)
    verify_video(zh_path)
    print("\nMultilingual lesson videos generated and verified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate StrokeSpeak multilingual lesson videos.")
    parser.add_argument("--overwrite", action="store_true", help="explicitly authorize replacing existing target MP4 files")
    main(overwrite=parser.parse_args().overwrite)
