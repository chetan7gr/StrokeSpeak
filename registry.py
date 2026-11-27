"""
Modular Multi-Script Model Registry for StrokeSpeak Handwriting Recognition
Manages script-specific models (TorchScript / ONNX / NumPy) and strictly enforces script boundaries
to prevent silent cross-script fallback.
"""
import os
import json
import time
import logging
import numpy as np

from app.ml.preprocessing import preprocess_handwriting_image

logger = logging.getLogger(__name__)
_TORCH_UNAVAILABLE_REASON = None

ML_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(ML_DIR, "models")

# Script Registry Definitions
SCRIPT_REGISTRY = {
    "ja-hiragana": {
        "language_name": "Japanese (Hiragana)",
        "status": "TRAINED",
        "model_file": "japanese_hiragana_v1.pt",
        "weights_npz": "japanese_hiragana_weights.npz",
        "metadata_file": "japanese_hiragana_metadata.json",
        "trained_classes": ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ'],
        "engine": "torchscript_cpu",
    },
    "ja-katakana": {
        "language_name": "Japanese (Katakana)",
        "status": "UNTRAINED",
        "model_file": None,
        "weights_npz": None,
        "metadata_file": None,
        "trained_classes": [],
        "engine": None,
        "note": "Katakana is available in the Japanese tutor and uses geometric practice feedback, but no verified Katakana CNN dataset/model is installed.",
    },
    "sa-devanagari": {
        "language_name": "Sanskrit (Devanagari)",
        "status": "TRAINED",
        "model_file": "sanskrit_devanagari_v1.pt",
        "weights_npz": "sanskrit_devanagari_weights.npz",
        "metadata_file": "sanskrit_devanagari_metadata.json",
        "trained_classes": ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ए', 'ऐ', 'ओ', 'औ'],
        "engine": "torchscript_cpu",
    },
    "ta": {
        "language_name": "Tamil",
        "status": "TRAINED",
        "model_file": "tamil_v1.pt",
        "weights_npz": "tamil_weights.npz",
        "metadata_file": "tamil_metadata.json",
        "trained_classes": ['அ', 'ஆ', 'இ', 'ஈ', 'உ', 'ஊ', 'எ', 'ஏ', 'ஐ', 'ஒ', 'ஓ', 'ஔ'],
        "engine": "torchscript_cpu",
    },
    "zh-hans": {
        "language_name": "Simplified Chinese",
        "status": "TRAINED",
        "model_file": "chinese_v1.pt",
        "weights_npz": "chinese_weights.npz",
        "metadata_file": "chinese_metadata.json",
        "trained_classes": ['一', '二', '三', '人', '大', '口', '日', '月', '山'],
        "engine": "torchscript_cpu",
    },
}

def _conv2d_same_3x3(x: np.ndarray, weight: np.ndarray, bias: np.ndarray) -> np.ndarray:
    """Exact 2D convolution (kernel_size=3, padding=1, stride=1) in NCHW float32."""
    x_pad = np.pad(x, ((0, 0), (0, 0), (1, 1), (1, 1)), mode="constant", constant_values=0.0)
    windows = np.lib.stride_tricks.sliding_window_view(x_pad, (3, 3), axis=(2, 3))
    out = np.einsum("nihwyx,oiyx->nohw", windows, weight, optimize=True)
    return (out + bias[None, :, None, None]).astype(np.float32, copy=False)


def _batchnorm2d(x: np.ndarray, weight: np.ndarray, bias: np.ndarray,
                 running_mean: np.ndarray, running_var: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    """Exact BatchNorm2d eval-mode normalization."""
    inv_std = 1.0 / np.sqrt(running_var + eps)
    scale = weight * inv_std
    shift = bias - running_mean * scale
    return (x * scale[None, :, None, None] + shift[None, :, None, None]).astype(np.float32, copy=False)


def _maxpool2d_2x2(x: np.ndarray) -> np.ndarray:
    """Exact MaxPool2d(kernel_size=2, stride=2) on NCHW tensors."""
    n, c, h, w = x.shape
    return x.reshape(n, c, h // 2, 2, w // 2, 2).max(axis=(3, 5))


def _numpy_scriptcnn_forward(tensor: np.ndarray, weights: dict) -> np.ndarray:
    """
    Pure-NumPy forward pass matching ScriptCNN (Conv-BN-ReLU-MaxPool x3 + FC128 + FC_classes).
    Uses the exact trained parameters exported in *_weights.npz.
    """
    x = tensor.astype(np.float32, copy=False)

    # Stage 1: Conv(1->16) -> BN -> ReLU -> MaxPool(2) -> 16x16
    x = _conv2d_same_3x3(x, weights["features.0.weight"], weights["features.0.bias"])
    x = _batchnorm2d(x, weights["features.1.weight"], weights["features.1.bias"],
                     weights["features.1.running_mean"], weights["features.1.running_var"])
    x = np.maximum(x, 0.0)
    x = _maxpool2d_2x2(x)

    # Stage 2: Conv(16->32) -> BN -> ReLU -> MaxPool(2) -> 8x8
    x = _conv2d_same_3x3(x, weights["features.4.weight"], weights["features.4.bias"])
    x = _batchnorm2d(x, weights["features.5.weight"], weights["features.5.bias"],
                     weights["features.5.running_mean"], weights["features.5.running_var"])
    x = np.maximum(x, 0.0)
    x = _maxpool2d_2x2(x)

    # Stage 3: Conv(32->64) -> BN -> ReLU -> MaxPool(2) -> 4x4
    x = _conv2d_same_3x3(x, weights["features.8.weight"], weights["features.8.bias"])
    x = _batchnorm2d(x, weights["features.9.weight"], weights["features.9.bias"],
                     weights["features.9.running_mean"], weights["features.9.running_var"])
    x = np.maximum(x, 0.0)
    x = _maxpool2d_2x2(x)

    # Flatten -> Linear(1024->128) -> ReLU -> Linear(128->num_classes)
    x = x.reshape(x.shape[0], -1)
    x = x @ weights["classifier.1.weight"].T + weights["classifier.1.bias"]
    x = np.maximum(x, 0.0)
    logits = x @ weights["classifier.3.weight"].T + weights["classifier.3.bias"]
    return logits[0]


class ModelRegistry:
    def __init__(self):
        self._models = {}
        self._metadata = {}
        self._engines = {}

    def get_registered_scripts(self) -> dict:
        """Return information about all registered scripts and their training status."""
        info = {}
        for code, reg in SCRIPT_REGISTRY.items():
            model_exists = False
            if reg["model_file"]:
                model_exists = os.path.exists(os.path.join(MODELS_DIR, reg["model_file"]))

            info[code] = {
                "script_code": code,
                "language_name": reg["language_name"],
                "status": reg["status"],
                "has_trained_model": model_exists,
                "trained_classes": reg["trained_classes"],
                "engine": reg.get("engine"),
                "note": reg.get("note", "Production trained model available.")
            }
        return info

    def get_model_and_meta(self, script_code: str):
        """
        Load or retrieve cached model and metadata for the given script code.
        Strictly enforces script boundary: raises NotImplementedError if the script is untrained.
        Never silently falls back to a different script's model.
        """
        if script_code not in SCRIPT_REGISTRY:
            raise ValueError(f"Unknown script code '{script_code}'. Supported scripts: {list(SCRIPT_REGISTRY.keys())}")

        reg = SCRIPT_REGISTRY[script_code]
        if reg["status"] != "TRAINED" or not reg["model_file"]:
            raise NotImplementedError(
                f"Handwriting recognition CNN for script '{script_code}' ({reg['language_name']}) "
                f"is not yet trained. {reg.get('note', '')}"
            )

        if script_code not in self._models:
            model_path = os.path.join(MODELS_DIR, reg["model_file"])
            meta_path = os.path.join(MODELS_DIR, reg["metadata_file"])

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file for '{script_code}' not found at {model_path}")

            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            if model_path.endswith(".pt"):
                global _TORCH_UNAVAILABLE_REASON
                if _TORCH_UNAVAILABLE_REASON is None:
                    try:
                        import torch
                        model = torch.jit.load(model_path, map_location="cpu")
                        model.eval()
                        engine_used = "torchscript_cpu"
                    except (OSError, ImportError) as exc:
                        _TORCH_UNAVAILABLE_REASON = str(exc)
                if _TORCH_UNAVAILABLE_REASON is not None:
                    npz_name = reg.get("weights_npz")
                    npz_path = os.path.join(MODELS_DIR, npz_name) if npz_name else None
                    if not npz_path or not os.path.exists(npz_path):
                        raise RuntimeError(
                            f"PyTorch runtime failed to load ({_TORCH_UNAVAILABLE_REASON}) and no NPZ weights fallback found at {npz_path}."
                        )
                    with np.load(npz_path) as npz_data:
                        model = {k: npz_data[k].astype(np.float32, copy=False) if npz_data[k].dtype != np.int64 else npz_data[k] for k in npz_data.files}
                    engine_used = "numpy_npz_fallback"
                    logger.warning(
                        "PyTorch TorchScript unavailable (%s); using exact NumPy NPZ CNN fallback for '%s'.",
                        _TORCH_UNAVAILABLE_REASON, script_code,
                    )
            elif model_path.endswith(".onnx"):
                import onnxruntime as ort
                model = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
                engine_used = "onnxruntime_cpu"
            else:
                raise ValueError(f"Unsupported model format: {model_path}")

            self._models[script_code] = model
            self._metadata[script_code] = meta
            self._engines[script_code] = engine_used
            logger.info("Loaded CNN model for '%s' using runtime '%s'.", script_code, engine_used)

        return self._models[script_code], self._metadata[script_code]

    def predict(self, image_input, script_code: str = "ja-hiragana", expected_character: str = None) -> dict:
        """
        Execute real CNN handwriting inference on a character image.
        1. Preprocesses image through OpenCV pipeline (resizing, polarity detection, Otsu thresholding, 32x32 pad/crop).
        2. Executes CNN model on CPU.
        3. Computes softmax probabilities.
        4. Returns predicted character, confidence percentage, top-3 candidates, and comparison with expected character.
        """
        start_time = time.perf_counter()

        model, meta = self.get_model_and_meta(script_code)
        classes = meta["classes"]
        target_size = meta["input_dimensions"][-1]

        # 1. OpenCV Preprocessing
        tensor = preprocess_handwriting_image(image_input, target_size=target_size)

        # Detect empty / blank canvas (fewer than 20 active ink pixels in 32x32 tensor)
        active_pixels = int(np.count_nonzero(tensor > 0.1))
        if active_pixels < 20:
            inference_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "status": "empty_canvas",
                "script_code": script_code,
                "language": meta.get("language", "Unknown"),
                "predicted_character": None,
                "confidence": 0.0,
                "confidence_level": "none",
                "expected_character": expected_character,
                "is_match": False,
                "top_predictions": [],
                "inference_time_ms": inference_time_ms,
                "model_name": meta.get("model_name", "StrokeSpeak CNN"),
                "model_version": meta.get("version", "1.0.0"),
                "device": "CPU",
                "message": "The canvas appears blank or contains insufficient drawing strokes. Please draw the character before recognition."
            }

        # 2. CPU Inference
        engine_used = self._engines.get(script_code, "torchscript_cpu")
        if engine_used == "numpy_npz_fallback":
            logits = _numpy_scriptcnn_forward(tensor, model)
        elif engine_used == "torchscript_cpu":
            import torch
            with torch.no_grad():
                torch_input = torch.from_numpy(tensor)
                logits_tensor = model(torch_input)
                logits = logits_tensor.cpu().numpy()[0]
        elif engine_used == "onnxruntime_cpu":
            input_name = model.get_inputs()[0].name
            output_name = model.get_outputs()[0].name
            logits = model.run([output_name], {input_name: tensor})[0][0]
        else:
            raise ValueError(f"Unsupported runtime engine: {engine_used}")

        # 3. Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probabilities = exp_logits / np.sum(exp_logits)

        # 4. Top-3 Predictions
        top_indices = np.argsort(probabilities)[::-1][:3]
        top_idx = int(top_indices[0])
        predicted_char = classes[top_idx]
        top_confidence = float(probabilities[top_idx])

        top_3 = [
            {"character": classes[int(i)], "confidence": round(float(probabilities[i]) * 100, 2)}
            for i in top_indices
        ]

        inference_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Confidence categorization
        conf_pct = round(top_confidence * 100, 2)
        if conf_pct >= 75.0:
            confidence_level = "high"
            message = f"Character recognized as '{predicted_char}' with high confidence ({conf_pct}%)."
        elif conf_pct >= 40.0:
            confidence_level = "moderate"
            message = f"Character recognized as '{predicted_char}' with moderate confidence ({conf_pct}%)."
        else:
            confidence_level = "low"
            message = f"Recognition confidence is low ({conf_pct}%); please redraw the character clearly."

        # Do not treat a low-confidence prediction as a confirmed match
        is_reliable = conf_pct >= 40.0
        if expected_character:
            is_match = (predicted_char == expected_character) and is_reliable
            if not is_match and is_reliable:
                message = (
                    f"CNN recognized your drawing as '{predicted_char}' ({conf_pct}%), not '{expected_character}'. "
                    f"Compare stroke proportions, loop closure, and stroke placement against the reference guide."
                )
        else:
            is_match = None

        return {
            "status": "success",
            "script_code": script_code,
            "language": meta.get("language", "Japanese"),
            "predicted_character": predicted_char,
            "confidence": conf_pct,
            "confidence_level": confidence_level,
            "is_reliable": is_reliable,
            "expected_character": expected_character,
            "is_match": is_match,
            "top_predictions": top_3,
            "inference_time_ms": inference_time_ms,
            "model_name": meta.get("model_name", "StrokeSpeak CNN"),
            "model_version": meta.get("version", "1.0.0"),
            "device": "CPU",
            "inference_runtime": engine_used,
            "message": message
        }

# Global registry singleton
model_registry = ModelRegistry()
