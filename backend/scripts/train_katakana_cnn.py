"""Train a local Katakana CNN only from a verified, writer-labeled dataset."""
import argparse
import copy
import csv
import json
import random
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
DATA_DIR = BACKEND_DIR / "data" / "katakana_dataset"
ANNOTATIONS_PATH = DATA_DIR / "annotations.csv"
MANIFEST_PATH = DATA_DIR / "dataset_manifest.json"
PREFLIGHT_PATH = BACKEND_DIR / "scripts" / "preflight_katakana_dataset.py"
OUTPUT_DIR = DATA_DIR / "artifacts"
MODEL_NAME = "japanese_katakana_v1.pt"
METADATA_NAME = "japanese_katakana_metadata.json"
CLASSES = tuple("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン")


def augment(image, rng):
    h, w = image.shape
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), rng.uniform(-8, 8), rng.uniform(0.94, 1.06))
    matrix[0, 2] += rng.uniform(-1.5, 1.5)
    matrix[1, 2] += rng.uniform(-1.5, 1.5)
    result = cv2.warpAffine(image, matrix, (w, h), borderValue=0)
    choice = rng.random()
    if choice < 0.15:
        result = cv2.dilate(result, np.ones((2, 2), np.uint8), iterations=1)
    elif choice < 0.25:
        result = cv2.erode(result, np.ones((2, 2), np.uint8), iterations=1)
    return result


class KanaImageDataset:
    def __init__(self, items, preprocess, augment_enabled, seed):
        self.items = items
        self.preprocess = preprocess
        self.augment_enabled = augment_enabled
        self.rng = random.Random(seed)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        import torch
        path, label = self.items[index]
        image = self.preprocess(str(path), 32)[0, 0].astype(np.float32, copy=True)
        if self.augment_enabled:
            image = augment(image, self.rng)
        return torch.from_numpy(image[None, :, :]), torch.tensor(label, dtype=torch.long)


def read_dataset():
    process = subprocess.run(
        [sys.executable, str(PREFLIGHT_PATH)],
        cwd=str(BACKEND_DIR.parent), text=True, capture_output=True, check=False,
    )
    if process.stdout:
        print(process.stdout, end="")
    if process.stderr:
        print(process.stderr, file=sys.stderr, end="")
    if process.returncode != 0:
        raise SystemExit("Katakana training stopped: dataset preflight did not pass.")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = []
    with ANNOTATIONS_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append({
                "path": (DATA_DIR / row["filename"].strip()).resolve(),
                "character": row["character"].strip(),
                "writer_id": row["writer_id"].strip(),
            })
    return manifest, rows


def split_by_writer(rows, seed, train_limit, val_limit, test_limit):
    rng = random.Random(seed)
    writers = sorted({row["writer_id"] for row in rows})
    rng.shuffle(writers)
    train_end = max(1, int(len(writers) * 0.70))
    val_end = max(train_end + 1, int(len(writers) * 0.85))
    train_writers = set(writers[:train_end])
    val_writers = set(writers[train_end:val_end])
    test_writers = set(writers[val_end:])
    if not train_writers or not val_writers or not test_writers:
        raise ValueError("Not enough distinct writers for a 70/15/15 writer-disjoint split.")
    if train_writers & val_writers or train_writers & test_writers or val_writers & test_writers:
        raise AssertionError("Writer leakage detected in split assignment.")

    grouped = {"train": defaultdict(list), "validation": defaultdict(list), "test": defaultdict(list)}
    for row in rows:
        split = "train" if row["writer_id"] in train_writers else "validation" if row["writer_id"] in val_writers else "test"
        grouped[split][row["character"]].append(row)

    limits = {"train": train_limit, "validation": val_limit, "test": test_limit}
    output = {}
    for split, chars in grouped.items():
        items = []
        for label, character in enumerate(CLASSES):
            candidates = chars[character]
            rng.shuffle(candidates)
            if not candidates:
                raise ValueError(f"Writer split leaves {character} without {split} samples.")
            chosen = candidates[:limits[split]]
            if len(chosen) < 5:
                raise ValueError(f"Only {len(chosen)} {split} samples for {character}; need at least 5.")
            items.extend((row["path"], label) for row in chosen)
        rng.shuffle(items)
        output[split] = items
    return output, {"train_writers": len(train_writers), "validation_writers": len(val_writers), "test_writers": len(test_writers)}


def create_model(torch):
    import torch.nn as nn

    class KatakanaCNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(1, 16, 3, padding=1), nn.BatchNorm2d(16), nn.ReLU(inplace=True), nn.MaxPool2d(2),
                nn.Conv2d(16, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(inplace=True), nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(inplace=True), nn.MaxPool2d(2),
            )
            self.classifier = nn.Sequential(
                nn.Dropout(0.25), nn.Linear(64 * 4 * 4, 128), nn.ReLU(inplace=True),
                nn.Dropout(0.15), nn.Linear(128, len(CLASSES)),
            )

        def forward(self, x):
            return self.classifier(self.features(x).flatten(1))

    return KatakanaCNN()


def main():
    parser = argparse.ArgumentParser(description="Train a Katakana CNN from a locally installed AIST ETL6 dataset.")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-per-class", type=int, default=300)
    parser.add_argument("--validation-per-class", type=int, default=100)
    parser.add_argument("--test-per-class", type=int, default=100)
    args = parser.parse_args()
    if min(args.epochs, args.batch_size, args.train_per_class, args.validation_per_class, args.test_per_class) < 1:
        raise SystemExit("Training options must be positive integers.")

    if (OUTPUT_DIR / MODEL_NAME).exists() or (OUTPUT_DIR / METADATA_NAME).exists():
        raise SystemExit(f"Refusing to overwrite Katakana artifacts in {OUTPUT_DIR}.")

    import torch
    from torch.utils.data import DataLoader
    from app.ml.preprocessing import preprocess_handwriting_image

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)
    started = time.time()
    manifest, rows = read_dataset()
    splits, writer_counts = split_by_writer(
        rows, args.seed, args.train_per_class, args.validation_per_class, args.test_per_class,
    )
    print("Writer-disjoint samples:", {key: len(value) for key, value in splits.items()})
    print("Writer split counts:", writer_counts)

    datasets = {
        "train": KanaImageDataset(splits["train"], preprocess_handwriting_image, True, args.seed),
        "validation": KanaImageDataset(splits["validation"], preprocess_handwriting_image, False, args.seed),
        "test": KanaImageDataset(splits["test"], preprocess_handwriting_image, False, args.seed),
    }
    loaders = {
        name: DataLoader(ds, batch_size=args.batch_size, shuffle=(name == "train"), num_workers=0)
        for name, ds in datasets.items()
    }
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = create_model(torch).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
    criterion = torch.nn.CrossEntropyLoss()
    best_state, best_val = None, -1.0
    history = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss_sum = 0.0
        train_correct = train_total = 0
        for images, labels in loaders["train"]:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            train_loss_sum += float(loss.item()) * len(labels)
            train_correct += int((logits.argmax(1) == labels).sum().item())
            train_total += len(labels)

        model.eval()
        val_correct = val_total = 0
        with torch.no_grad():
            for images, labels in loaders["validation"]:
                logits = model(images.to(device))
                labels = labels.to(device)
                val_correct += int((logits.argmax(1) == labels).sum().item())
                val_total += len(labels)
        val_accuracy = val_correct / max(1, val_total)
        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss_sum / max(1, train_total), 5),
            "train_accuracy": round(train_correct / max(1, train_total), 5),
            "validation_accuracy": round(val_accuracy, 5),
        })
        if val_accuracy > best_val:
            best_val = val_accuracy
            best_state = copy.deepcopy(model.state_dict())
        print(f"Epoch {epoch}/{args.epochs}: train={train_correct}/{train_total}, validation={val_correct}/{val_total} ({val_accuracy:.1%})")

    if best_state is None:
        raise RuntimeError("No best model state was produced.")
    model.load_state_dict(best_state)
    model.eval()
    confusion = np.zeros((len(CLASSES), len(CLASSES)), dtype=np.int64)
    correct = total = 0
    with torch.no_grad():
        for images, labels in loaders["test"]:
            logits = model(images.to(device))
            labels_np = labels.numpy()
            predicted = logits.argmax(1).cpu().numpy()
            for truth, guess in zip(labels_np, predicted):
                confusion[int(truth), int(guess)] += 1
            correct += int((predicted == labels_np).sum())
            total += len(labels_np)
    test_accuracy = correct / max(1, total)
    print(f"Writer-disjoint ETL6 test accuracy: {correct}/{total} ({test_accuracy:.1%})")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = OUTPUT_DIR / MODEL_NAME
    meta_path = OUTPUT_DIR / METADATA_NAME
    temp_model = OUTPUT_DIR / (MODEL_NAME + ".tmp")
    dummy = torch.zeros(1, 1, 32, 32, dtype=torch.float32, device=device)
    torch.jit.trace(model.cpu(), dummy.cpu()).save(str(temp_model))
    temp_model.replace(model_path)
    metadata = {
        "model_name": "StrokeSpeak Japanese Katakana CNN",
        "version": "1.0.0",
        "script_code": "ja-katakana",
        "language": "Japanese Katakana",
        "model_file": MODEL_NAME,
        "classes": list(CLASSES),
        "num_classes": len(CLASSES),
        "architecture": "3-stage Conv-BN-ReLU-MaxPool CNN with 128-unit classifier",
        "input_dimensions": [1, 1, 32, 32],
        "preprocessing": "app.ml.preprocessing.preprocess_handwriting_image; 32x32 grayscale",
        "dataset": {
            "name": manifest["dataset_name"],
            "source_url": manifest["source_url"],
            "license_name": manifest["license_name"],
            "citation": manifest["citation"],
            "source_archive_sha256": manifest["source_archive_sha256"],
            "raw_dataset_included": False,
        },
        "writer_split": writer_counts,
        "sample_counts": {key: len(value) for key, value in splits.items()},
        "test_accuracy": round(test_accuracy, 6),
        "test_confusion_matrix": confusion.tolist(),
        "training_history": history,
        "training_seconds": round(time.time() - started, 2),
        "evaluation_scope": "Held-out ETL6 writers only; not a benchmark of contemporary tablet handwriting or StrokeSpeak learners.",
        "promotion_status": "local draft; manual review required before registry activation or redistribution",
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Local model draft:", model_path)
    print("Metadata:", meta_path)
    print("The model was not added to the public registry. Human review is required before activation.")


if __name__ == "__main__":
    main()
