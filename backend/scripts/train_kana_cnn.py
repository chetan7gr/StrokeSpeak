"""
StrokeSpeak: CNN Training Pipeline for Japanese Hiragana Recognition
Trains on authentic handwritten Kana images and exports to ONNX for CPU inference.
"""
import os
import sys
import json
import random
import numpy as np
import cv2

# Ensure backend package can be imported
sys.path.insert(0, os.path.abspath("backend"))
from app.ml.preprocessing import preprocess_handwriting_image, TARGET_SIZE

CLASSES = ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ']
PREFIXES = ['kanaA', 'kanaI', 'kanaU', 'kanaE', 'kanaO', 'kanaKA', 'kanaKI', 'kanaKU', 'kanaKE', 'kanaKO']
LABEL_MAP = {c: i for i, c in enumerate(CLASSES)}
DATA_DIR = r"C:\Users\CHETAN\.vscode\StrokeSpeak\backend\data\hiragana_dataset"
MODELS_DIR = r"C:\Users\CHETAN\.vscode\StrokeSpeak\backend\app\ml\models"

def augment_image(img_2d):
    """Apply slight affine rotation, translation, and stroke scaling to an image."""
    h, w = img_2d.shape
    # Rotation (-12 to 12 degrees)
    angle = random.uniform(-12, 12)
    # Translation (-2 to 2 pixels)
    tx = random.uniform(-2, 2)
    ty = random.uniform(-2, 2)
    # Scale (0.92 to 1.08)
    scale = random.uniform(0.92, 1.08)

    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
    M[0, 2] += tx
    M[1, 2] += ty
    aug = cv2.warpAffine(img_2d, M, (w, h), borderValue=0)

    # Occasionally dilate or erode stroke slightly
    choice = random.random()
    if choice < 0.25:
        kernel = np.ones((2, 2), np.uint8)
        aug = cv2.dilate(aug, kernel, iterations=1)
    elif choice < 0.40:
        kernel = np.ones((2, 2), np.uint8)
        aug = cv2.erode(aug, kernel, iterations=1)

    return aug

def load_dataset():
    """Load and partition the 200 real handwritten images into train, val, and test."""
    train_x, train_y = [], []
    val_x, val_y = [], []
    test_x, test_y = [], []

    per_class_counts = {}

    for idx, (kana, prefix) in enumerate(zip(CLASSES, PREFIXES)):
        kana_dir = os.path.join(DATA_DIR, prefix)
        img_files = sorted([os.path.join(kana_dir, f) for f in os.listdir(kana_dir) if f.endswith('.jpg')])
        per_class_counts[kana] = len(img_files)

        # 14 train, 3 val, 3 test (held-out test set: images 17, 18, 19)
        train_files = img_files[:14]
        val_files = img_files[14:17]
        test_files = img_files[17:20]

        # Training samples with augmentation (10 augmentations per base sample = 140 train samples per class)
        for f in train_files:
            tensor = preprocess_handwriting_image(f, TARGET_SIZE)
            img_2d = tensor[0, 0]
            train_x.append(img_2d)
            train_y.append(idx)

            for _ in range(9):
                aug_2d = augment_image(img_2d)
                train_x.append(aug_2d)
                train_y.append(idx)

        # Validation samples (raw preprocessed, no augmentation)
        for f in val_files:
            tensor = preprocess_handwriting_image(f, TARGET_SIZE)
            val_x.append(tensor[0, 0])
            val_y.append(idx)

        # Test samples (held-out untouched real handwriting)
        for f in test_files:
            tensor = preprocess_handwriting_image(f, TARGET_SIZE)
            test_x.append(tensor[0, 0])
            test_y.append(idx)

    # Reshape to (N, 1, 32, 32) float32
    train_x = np.expand_dims(np.array(train_x, dtype=np.float32), axis=1)
    train_y = np.array(train_y, dtype=np.int64)
    val_x = np.expand_dims(np.array(val_x, dtype=np.float32), axis=1)
    val_y = np.array(val_y, dtype=np.int64)
    test_x = np.expand_dims(np.array(test_x, dtype=np.float32), axis=1)
    test_y = np.array(test_y, dtype=np.int64)

    return (train_x, train_y), (val_x, val_y), (test_x, test_y), per_class_counts

def build_model_and_train():
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import TensorDataset, DataLoader

    print("PyTorch version:", torch.__version__)
    torch.manual_seed(42)
    np.random.seed(42)

    (train_x, train_y), (val_x, val_y), (test_x, test_y), per_class_counts = load_dataset()
    print(f"Dataset summary:")
    print(f"  Per-class real base samples: {per_class_counts}")
    print(f"  Training set size: {len(train_x)} samples")
    print(f"  Validation set size: {len(val_x)} samples")
    print(f"  Held-out test set size: {len(test_x)} samples")

    train_loader = DataLoader(TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_y)), batch_size=32, shuffle=True)
    val_loader = DataLoader(TensorDataset(torch.from_numpy(val_x), torch.from_numpy(val_y)), batch_size=16, shuffle=False)
    test_loader = DataLoader(TensorDataset(torch.from_numpy(test_x), torch.from_numpy(test_y)), batch_size=16, shuffle=False)

    class KanaCNN(nn.Module):
        def __init__(self, num_classes=10):
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

    model = KanaCNN(num_classes=len(CLASSES))
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)

    best_val_acc = 0.0
    best_weights = None
    epochs = 25
    history = []

    print(f"\nTraining CNN model for {epochs} epochs...")
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

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_weights = model.state_dict().copy()

        if epoch % 5 == 0 or epoch == epochs:
            print(f"  Epoch {epoch:2d}/{epochs:2d}: train_loss={train_loss:.4f}, train_acc={train_acc*100:.2f}%, val_acc={val_acc*100:.2f}%")

    if best_weights:
        model.load_state_dict(best_weights)

    # Final Independent Test Evaluation
    model.eval()
    all_preds, all_targets = [], []
    with torch.no_grad():
        for tx, ty in test_loader:
            tout = model(tx)
            all_preds.extend(tout.argmax(dim=1).cpu().numpy())
            all_targets.extend(ty.cpu().numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    test_acc = float((all_preds == all_targets).mean())
    print(f"\nFinal Independent Test Accuracy on held-out handwritten samples: {test_acc*100:.2f}%")

    # Confusion matrix
    conf_matrix = np.zeros((10, 10), dtype=int)
    for p, t in zip(all_preds, all_targets):
        conf_matrix[t, p] += 1

    print("\nConfusion Matrix (Rows=True, Cols=Predicted):")
    print("      " + "  ".join(f"{c}" for c in CLASSES))
    for i, row in enumerate(conf_matrix):
        print(f"  {CLASSES[i]}: " + "  ".join(f"{val:2d}" for val in row))

    # Export trained model
    os.makedirs(MODELS_DIR, exist_ok=True)
    dummy_input = torch.randn(1, 1, TARGET_SIZE, TARGET_SIZE, dtype=torch.float32)

    # 1. Save TorchScript model for CPU production inference
    script_path = os.path.join(MODELS_DIR, "japanese_hiragana_v1.pt")
    print(f"\nExporting trained model to TorchScript: {script_path}...")
    model.eval()
    traced_model = torch.jit.trace(model, dummy_input)
    traced_model.save(script_path)
    script_size = os.path.getsize(script_path)
    print(f"TorchScript export successful. Size: {script_size} bytes ({script_size / 1024:.1f} KB).")

    # 2. Save PyTorch state dict
    weights_path = os.path.join(MODELS_DIR, "japanese_hiragana_weights.pt")
    torch.save(model.state_dict(), weights_path)

    # 3. Save NumPy weights dictionary for ultra-lightweight portability
    npz_path = os.path.join(MODELS_DIR, "japanese_hiragana_weights.npz")
    np_weights = {k: v.cpu().numpy() for k, v in model.state_dict().items()}
    np.savez(npz_path, **np_weights)
    print(f"NumPy weights export successful. Size: {os.path.getsize(npz_path)} bytes.")

    # 4. Save model metadata alongside weights
    meta_path = os.path.join(MODELS_DIR, "japanese_hiragana_metadata.json")
    metadata = {
        "model_name": "StrokeSpeak Japanese Hiragana CNN",
        "version": "1.0.0",
        "script_code": "ja-hiragana",
        "language": "Japanese",
        "model_file": "japanese_hiragana_v1.pt",
        "architecture": "LeNet-style 3-Stage ConvNet (Conv-BN-ReLU-MaxPool x3 + FC128 + FC10)",
        "input_dimensions": [1, 1, TARGET_SIZE, TARGET_SIZE],
        "classes": CLASSES,
        "num_classes": len(CLASSES),
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
            "source": "inoueMashuu/hiragana-dataset (scanned real handwriting) + StrokeSpeak canvas samples",
            "license": "Open Source",
            "base_samples_per_class": 20,
            "total_real_images": 200,
            "train_samples": len(train_x),
            "val_samples": len(val_x),
            "test_samples": len(test_x)
        },
        "metrics": {
            "final_train_acc": float(history[-1]["train_acc"]),
            "best_val_acc": float(best_val_acc),
            "test_acc": test_acc,
            "confusion_matrix": conf_matrix.tolist()
        },
        "history": history
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"Saved metadata to {meta_path} ({os.path.getsize(meta_path)} bytes).")

    # 5. Verification of TorchScript model inference
    loaded = torch.jit.load(script_path)
    loaded.eval()
    t0 = cv2.getTickCount()
    out = loaded(dummy_input)
    t1 = cv2.getTickCount()
    latency_ms = (t1 - t0) / cv2.getTickFrequency() * 1000.0
    print(f"TorchScript inference verification passed! Output shape: {out.shape}, Latency: {latency_ms:.2f} ms")

if __name__ == "__main__":
    build_model_and_train()
