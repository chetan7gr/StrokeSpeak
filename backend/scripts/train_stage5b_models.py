"""
StrokeSpeak — Stage 5B-B2: Multilingual CNN Training & Export Pipeline
Trains, validates, evaluates, and exports separate TorchScript CNN models for:
1. Sanskrit Devanagari (10 vowel classes)
2. Tamil (12 vowel classes)
3. Simplified Chinese (9 foundational character classes)

Preserves the existing Japanese Hiragana model without retraining or modification.
Strictly abides by:
- Train partition ONLY is augmented (14 base * 10 = 140 training images per class).
- Validation (3) and Test (3) partitions are NEVER augmented.
- Evaluates on held-out test split and computes:
  - Accuracy
  - Correct / Total count
  - Full Confusion Matrix
  - Macro-Precision, Macro-Recall, Macro-F1
- Exports versioned TorchScript model (.pt), weights (.pt, .npz), and metadata (.json).
- Clearly designates metrics as Synthetic-Data Benchmark Results (Tier 1).
"""

import os
import sys
import json
import random
import time
import cv2
import numpy as np

# Ensure backend package can be imported
sys.path.insert(0, os.path.abspath("backend"))
from app.ml.preprocessing import preprocess_handwriting_image, TARGET_SIZE

DATA_BASE_DIR = os.path.abspath("backend/data")
MODELS_DIR = os.path.abspath("backend/app/ml/models")

# ============================================================================
# Configurations for the 3 target scripts
# ============================================================================

CONFIGS = {
    "sa-devanagari": {
        "model_name": "StrokeSpeak Sanskrit Devanagari CNN",
        "version": "1.0.0",
        "script_code": "sa-devanagari",
        "language": "Sanskrit (Devanagari)",
        "dataset_dir": os.path.join(DATA_BASE_DIR, "sanskrit_dataset"),
        "model_prefix": "sanskrit_devanagari",
        "classes": [
            ("अ", "vowel_A"),
            ("आ", "vowel_AA"),
            ("इ", "vowel_I"),
            ("ई", "vowel_II"),
            ("उ", "vowel_U"),
            ("ऊ", "vowel_UU"),
            ("ए", "vowel_E"),
            ("ऐ", "vowel_AI"),
            ("ओ", "vowel_O"),
            ("औ", "vowel_AU"),
        ],
        "epochs": 25,
        "batch_size": 32,
        "learning_rate": 0.001,
        "seed": 42,
    },
    "ta": {
        "model_name": "StrokeSpeak Tamil CNN",
        "version": "1.0.0",
        "script_code": "ta",
        "language": "Tamil",
        "dataset_dir": os.path.join(DATA_BASE_DIR, "tamil_dataset"),
        "model_prefix": "tamil",
        "classes": [
            ("அ", "vowel_A"),
            ("ஆ", "vowel_AA"),
            ("இ", "vowel_I"),
            ("ஈ", "vowel_II"),
            ("உ", "vowel_U"),
            ("ஊ", "vowel_UU"),
            ("எ", "vowel_E"),
            ("ஏ", "vowel_EE"),
            ("ஐ", "vowel_AI"),
            ("ஒ", "vowel_O"),
            ("ஓ", "vowel_OO"),
            ("ஔ", "vowel_AU"),
        ],
        "epochs": 25,
        "batch_size": 32,
        "learning_rate": 0.001,
        "seed": 42,
    },
    "zh-hans": {
        "model_name": "StrokeSpeak Simplified Chinese CNN",
        "version": "1.0.0",
        "script_code": "zh-hans",
        "language": "Simplified Chinese",
        "dataset_dir": os.path.join(DATA_BASE_DIR, "chinese_dataset"),
        "model_prefix": "chinese",
        "classes": [
            ("一", "char_YI"),
            ("二", "char_ER"),
            ("三", "char_SAN"),
            ("人", "char_REN"),
            ("大", "char_DA"),
            ("口", "char_KOU"),
            ("日", "char_RI"),
            ("月", "char_YUE"),
            ("山", "char_SHAN"),
        ],
        "epochs": 25,
        "batch_size": 32,
        "learning_rate": 0.001,
        "seed": 42,
    },
}


# ============================================================================
# Augmentation function (Training data ONLY)
# ============================================================================

def augment_image(img_2d):
    """
    Apply slight affine rotation, translation, scaling, and morphological jitter.
    Applied ONLY to the training set to prevent data leakage into val or test.
    """
    h, w = img_2d.shape
    angle = random.uniform(-10, 10)
    tx = random.uniform(-2, 2)
    ty = random.uniform(-2, 2)
    scale = random.uniform(0.92, 1.08)

    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
    M[0, 2] += tx
    M[1, 2] += ty
    aug = cv2.warpAffine(img_2d, M, (w, h), borderValue=0)

    choice = random.random()
    if choice < 0.25:
        kernel = np.ones((2, 2), np.uint8)
        aug = cv2.dilate(aug, kernel, iterations=1)
    elif choice < 0.40:
        kernel = np.ones((2, 2), np.uint8)
        aug = cv2.erode(aug, kernel, iterations=1)

    return aug


# ============================================================================
# Dataset Loading & Partitioning
# ============================================================================

def load_script_dataset(config):
    """
    Load dataset for a script with strict partition boundaries:
    - 14 base images (70%) -> 1 base + 9 augmented = 140 training images per class
    - 3 base images (15%) -> unaugmented validation set
    - 3 base images (15%) -> unaugmented held-out test set
    """
    data_dir = config["dataset_dir"]
    classes = config["classes"]
    
    train_x, train_y = [], []
    val_x, val_y = [], []
    test_x, test_y = [], []
    
    per_class_summary = {}

    for idx, (char_symbol, folder_name) in enumerate(classes):
        class_dir = os.path.join(data_dir, folder_name)
        if not os.path.isdir(class_dir):
            raise FileNotFoundError(f"Class directory not found: {class_dir}")

        img_files = sorted([f for f in os.listdir(class_dir) if f.endswith(('.jpg', '.png'))])
        if len(img_files) != 20:
            raise ValueError(f"Expected 20 base images for {folder_name}, found {len(img_files)}")

        # Strict split
        train_files = img_files[:14]
        val_files = img_files[14:17]
        test_files = img_files[17:20]

        # Verify zero leakage
        assert not (set(train_files) & set(val_files)), f"Train/Val leakage in {folder_name}"
        assert not (set(train_files) & set(test_files)), f"Train/Test leakage in {folder_name}"
        assert not (set(val_files) & set(test_files)), f"Val/Test leakage in {folder_name}"

        # 1. Training images (with 9 augmentations per base sample -> 140 total per class)
        for f in train_files:
            fpath = os.path.join(class_dir, f)
            tensor = preprocess_handwriting_image(fpath, TARGET_SIZE)
            img_2d = tensor[0, 0]
            train_x.append(img_2d)
            train_y.append(idx)

            for _ in range(9):
                aug_2d = augment_image(img_2d)
                train_x.append(aug_2d)
                train_y.append(idx)

        # 2. Validation images (raw preprocessed, NO augmentation)
        for f in val_files:
            fpath = os.path.join(class_dir, f)
            tensor = preprocess_handwriting_image(fpath, TARGET_SIZE)
            val_x.append(tensor[0, 0])
            val_y.append(idx)

        # 3. Held-out test images (raw preprocessed, NO augmentation)
        for f in test_files:
            fpath = os.path.join(class_dir, f)
            tensor = preprocess_handwriting_image(fpath, TARGET_SIZE)
            test_x.append(tensor[0, 0])
            test_y.append(idx)

        per_class_summary[char_symbol] = {
            "folder": folder_name,
            "base_total": len(img_files),
            "train_base": len(train_files),
            "train_augmented": len(train_files) * 10,
            "val_unaugmented": len(val_files),
            "test_unaugmented": len(test_files),
        }

    # Format arrays to NCHW float32
    train_x = np.expand_dims(np.array(train_x, dtype=np.float32), axis=1)
    train_y = np.array(train_y, dtype=np.int64)
    val_x = np.expand_dims(np.array(val_x, dtype=np.float32), axis=1)
    val_y = np.array(val_y, dtype=np.int64)
    test_x = np.expand_dims(np.array(test_x, dtype=np.float32), axis=1)
    test_y = np.array(test_y, dtype=np.int64)

    return (train_x, train_y), (val_x, val_y), (test_x, test_y), per_class_summary


# ============================================================================
# PyTorch Model Architecture (Identical to KanaCNN)
# ============================================================================

def create_model_class():
    import torch.nn as nn

    class ScriptCNN(nn.Module):
        def __init__(self, num_classes):
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(1, 16, kernel_size=3, padding=1),
                nn.BatchNorm2d(16),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2),  # -> 16x16

                nn.Conv2d(16, 32, kernel_size=3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2),  # -> 8x8

                nn.Conv2d(32, 64, kernel_size=3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2),  # -> 4x4
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
            x = self.classifier(x)
            return x

    return ScriptCNN


# ============================================================================
# Metrics Calculation (Precision, Recall, Macro-F1, Confusion Matrix)
# ============================================================================

def compute_detailed_metrics(y_true, y_pred, class_names):
    num_classes = len(class_names)
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1

    total = len(y_true)
    correct = int((y_true == y_pred).sum())
    accuracy = correct / total if total > 0 else 0.0

    precisions = []
    recalls = []
    f1_scores = []
    per_class = {}

    for c in range(num_classes):
        tp = cm[c, c]
        fp = cm[:, c].sum() - tp
        fn = cm[c, :].sum() - tp

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        precisions.append(prec)
        recalls.append(rec)
        f1_scores.append(f1)

        per_class[class_names[c]] = {
            "true_count": int(cm[c, :].sum()),
            "predicted_count": int(cm[:, c].sum()),
            "tp": int(tp),
            "fp": int(fp),
            "fn": int(fn),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1": round(float(f1), 4),
        }

    macro_precision = float(np.mean(precisions))
    macro_recall = float(np.mean(recalls))
    macro_f1 = float(np.mean(f1_scores))

    return {
        "benchmark_type": "Synthetic-Data Benchmark Results (Tier 1 Held-Out Test Split)",
        "evaluation_scope": "Held-out unaugmented synthetic motor simulations; does not represent unconstrained human handwriting.",
        "total_test_samples": total,
        "correct_predictions": correct,
        "accuracy": round(accuracy, 4),
        "accuracy_pct": round(accuracy * 100, 2),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "macro_f1_pct": round(macro_f1 * 100, 2),
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
    }


# ============================================================================
# Single Script Training & Export Pipeline
# ============================================================================

def train_and_export_script(script_code):
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import TensorDataset, DataLoader

    config = CONFIGS[script_code]
    print("\n" + "=" * 80)
    print(f"TRAINING CNN FOR {config['language'].upper()} ({script_code})")
    print("=" * 80)

    # Set seeds for reproducibility
    seed = config["seed"]
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    # Load dataset
    (train_x, train_y), (val_x, val_y), (test_x, test_y), per_class_summary = load_script_dataset(config)
    class_symbols = [c[0] for c in config["classes"]]
    num_classes = len(class_symbols)

    print(f"Classes ({num_classes}): {class_symbols}")
    print(f"Dataset split summary:")
    print(f"  Training set: {len(train_x)} images ({len(train_x)//num_classes} per class, 1 base + 9 augmented)")
    print(f"  Validation set: {len(val_x)} images ({len(val_x)//num_classes} per class, unaugmented)")
    print(f"  Held-out test set: {len(test_x)} images ({len(test_x)//num_classes} per class, unaugmented)")

    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_y)),
        batch_size=config["batch_size"],
        shuffle=True
    )
    val_loader = DataLoader(
        TensorDataset(torch.from_numpy(val_x), torch.from_numpy(val_y)),
        batch_size=16,
        shuffle=False
    )
    test_loader = DataLoader(
        TensorDataset(torch.from_numpy(test_x), torch.from_numpy(test_y)),
        batch_size=16,
        shuffle=False
    )

    ScriptCNN = create_model_class()
    model = ScriptCNN(num_classes=num_classes)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=config["learning_rate"], weight_decay=1e-4)

    best_val_acc = 0.0
    best_weights = None
    epochs = config["epochs"]
    history = []

    print(f"\nTraining for {epochs} epochs on CPU...")
    train_start_time = time.perf_counter()

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss, correct, total = 0.0, 0, 0
        for bx, by in train_loader:
            optimizer.zero_grad()
            out = model(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(by)
            preds = out.argmax(dim=1)
            correct += (preds == by).sum().item()
            total += len(by)

        train_acc = correct / total
        train_loss = total_loss / total

        # Validation
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        with torch.no_grad():
            for vx, vy in val_loader:
                vout = model(vx)
                vloss = criterion(vout, vy)
                val_loss += vloss.item() * len(vy)
                vpreds = vout.argmax(dim=1)
                val_correct += (vpreds == vy).sum().item()
                val_total += len(vy)

        val_acc = val_correct / val_total
        val_loss = val_loss / val_total

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 4),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc, 4),
        })

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        if epoch % 5 == 0 or epoch == epochs:
            print(f"  Epoch {epoch:2d}/{epochs:2d}: train_loss={train_loss:.4f}, train_acc={train_acc*100:.1f}%, val_acc={val_acc*100:.1f}%")

    training_duration_s = round(time.perf_counter() - train_start_time, 2)
    print(f"Training completed in {training_duration_s} seconds. Best Val Acc: {best_val_acc*100:.1f}%")

    # Load best weights
    if best_weights:
        model.load_state_dict(best_weights)

    # ========================================================================
    # Evaluation on Held-Out Test Set (Synthetic-Data Benchmark Results Tier 1)
    # ========================================================================
    model.eval()
    all_preds, all_targets = [], []
    with torch.no_grad():
        for tx, ty in test_loader:
            tout = model(tx)
            all_preds.extend(tout.argmax(dim=1).cpu().numpy())
            all_targets.extend(ty.cpu().numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    metrics = compute_detailed_metrics(all_targets, all_preds, class_symbols)

    print("\n--- HELD-OUT TEST EVALUATION (SYNTHETIC BENCHMARK TIER 1) ---")
    print(f"  Total Test Samples: {metrics['total_test_samples']}")
    print(f"  Correct Predictions: {metrics['correct_predictions']}/{metrics['total_test_samples']}")
    print(f"  Top-1 Accuracy: {metrics['accuracy_pct']}%")
    print(f"  Macro-F1 Score: {metrics['macro_f1_pct']}% (Precision: {metrics['macro_precision']*100:.1f}%, Recall: {metrics['macro_recall']*100:.1f}%)")

    print("\n  Confusion Matrix (Rows=True, Columns=Predicted):")
    header = "       " + " ".join(f"{c:>3}" for c in class_symbols)
    print(header)
    cm = metrics["confusion_matrix"]
    for i, row in enumerate(cm):
        row_str = " ".join(f"{val:>3}" for val in row)
        print(f"  {class_symbols[i]:>3}: {row_str}")

    # ========================================================================
    # Export Model Artifacts
    # ========================================================================
    os.makedirs(MODELS_DIR, exist_ok=True)
    prefix = config["model_prefix"]
    dummy_input = torch.randn(1, 1, TARGET_SIZE, TARGET_SIZE, dtype=torch.float32)

    # 1. TorchScript CPU Model (.pt)
    script_model_filename = f"{prefix}_v1.pt"
    script_model_path = os.path.join(MODELS_DIR, script_model_filename)
    model.eval()
    traced_model = torch.jit.trace(model, dummy_input)
    traced_model.save(script_model_path)
    script_size = os.path.getsize(script_model_path)
    print(f"\nExported TorchScript model: {script_model_path} ({script_size / 1024:.1f} KB)")

    # 2. PyTorch State Dict (.pt)
    weights_filename = f"{prefix}_weights.pt"
    weights_path = os.path.join(MODELS_DIR, weights_filename)
    torch.save(model.state_dict(), weights_path)

    # 3. NumPy Weights (.npz)
    npz_filename = f"{prefix}_weights.npz"
    npz_path = os.path.join(MODELS_DIR, npz_filename)
    np_weights = {k: v.cpu().numpy() for k, v in model.state_dict().items()}
    np.savez(npz_path, **np_weights)

    # 4. Metadata JSON (.json)
    meta_filename = f"{prefix}_metadata.json"
    meta_path = os.path.join(MODELS_DIR, meta_filename)
    metadata = {
        "model_name": config["model_name"],
        "version": config["version"],
        "script_code": config["script_code"],
        "language": config["language"],
        "model_file": script_model_filename,
        "weights_file": weights_filename,
        "architecture": f"LeNet-style 3-Stage ConvNet (Conv-BN-ReLU-MaxPool x3 + FC128 + FC{num_classes})",
        "input_dimensions": [1, 1, TARGET_SIZE, TARGET_SIZE],
        "classes": class_symbols,
        "class_prefixes": [c[1] for c in config["classes"]],
        "num_classes": num_classes,
        "preprocessing": {
            "grayscale": True,
            "invert_if_light_bg": True,
            "otsu_thresholding": True,
            "aspect_ratio_preserving_crop_and_pad": True,
            "interpolation": "cv2.INTER_AREA",
            "normalization": "float32 [0.0, 1.0]",
            "target_size": TARGET_SIZE
        },
        "dataset": {
            "provenance": "SYNTHETIC (Procedural Vector Motor Simulation)",
            "license": "Internal StrokeSpeak Project Asset",
            "base_samples_per_class": 20,
            "total_base_images": num_classes * 20,
            "train_samples": len(train_x),
            "val_samples": len(val_x),
            "test_samples": len(test_x),
            "per_class_summary": per_class_summary,
        },
        "metrics": metrics,
        "training_duration_seconds": training_duration_s,
        "history": history
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"Exported metadata: {meta_path} ({os.path.getsize(meta_path)} bytes)")

    # 5. Verification of TorchScript CPU Inference
    loaded = torch.jit.load(script_model_path, map_location="cpu")
    loaded.eval()
    t0 = time.perf_counter()
    with torch.no_grad():
        test_out = loaded(dummy_input)
    t1 = time.perf_counter()
    latency_ms = round((t1 - t0) * 1000, 2)
    assert test_out.shape == (1, num_classes), f"Shape mismatch: {test_out.shape}"
    print(f"CPU TorchScript Verification: PASSED (Shape={test_out.shape}, Latency={latency_ms:.2f} ms)")

    return {
        "script_code": script_code,
        "language": config["language"],
        "num_classes": num_classes,
        "classes": class_symbols,
        "model_file": script_model_filename,
        "metadata_file": meta_filename,
        "model_path": script_model_path,
        "metadata_path": meta_path,
        "file_size_kb": round(script_size / 1024, 1),
        "train_samples": len(train_x),
        "val_samples": len(val_x),
        "test_samples": len(test_x),
        "best_val_acc": round(best_val_acc, 4),
        "test_accuracy": metrics["accuracy"],
        "test_accuracy_pct": metrics["accuracy_pct"],
        "correct_predictions": metrics["correct_predictions"],
        "total_test_samples": metrics["total_test_samples"],
        "macro_f1": metrics["macro_f1"],
        "macro_f1_pct": metrics["macro_f1_pct"],
        "macro_precision": metrics["macro_precision"],
        "macro_recall": metrics["macro_recall"],
        "confusion_matrix": metrics["confusion_matrix"],
        "latency_ms": latency_ms,
        "training_duration_s": training_duration_s,
    }


def main():
    print("=" * 80)
    print("STROKESPEAK STAGE 5B-B2: CNN TRAINING & EXPORT")
    print("Authorized scripts: Sanskrit Devanagari, Tamil, Simplified Chinese")
    print("Japanese Hiragana model is strictly preserved (untouched).")
    print("=" * 80)

    target_scripts = ["sa-devanagari", "ta", "zh-hans"]
    results = {}

    for sc in target_scripts:
        res = train_and_export_script(sc)
        results[sc] = res

    # Save summary report JSON
    summary_path = os.path.join(MODELS_DIR, "stage5b_b2_training_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("ALL 3 MODELS SUCCESSFULLY TRAINED, EVALUATED, AND EXPORTED!")
    print(f"Summary JSON saved to: {summary_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
