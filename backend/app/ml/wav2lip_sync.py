"""Local Wav2Lip GAN lip-sync inference for StrokeSpeak teacher portraits."""

from pathlib import Path
from typing import List, Optional, Tuple

import av
import cv2
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_WAV2LIP_CHECKPOINT = (
    BACKEND_DIR / "ml_models" / "wav2lip" / "Wav2lip" / "wav2lip_gan.pth"
)

# Mel-spectrogram constants matching Wav2Lip training configuration
SAMPLE_RATE = 16000
N_FFT = 800
HOP_SIZE = 200
WIN_SIZE = 800
NUM_MELS = 80
FMIN = 55.0
FMAX = 7600.0
PREEMPHASIS = 0.97
REF_LEVEL_DB = 20.0
MIN_LEVEL_DB = -100.0
MAX_ABS_VALUE = 4.0
MEL_STEP_SIZE = 16


class Conv2d(nn.Module):
    def __init__(
        self,
        cin: int,
        cout: int,
        kernel_size: int,
        stride: int,
        padding: int,
        residual: bool = False,
    ):
        super().__init__()
        self.conv_block = nn.Sequential(
            nn.Conv2d(cin, cout, kernel_size, stride, padding),
            nn.BatchNorm2d(cout),
        )
        self.act = nn.ReLU()
        self.residual = residual

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.conv_block(x)
        if self.residual:
            out += x
        return self.act(out)


class nonorm_Conv2d(nn.Module):
    def __init__(
        self,
        cin: int,
        cout: int,
        kernel_size: int,
        stride: int,
        padding: int,
    ):
        super().__init__()
        self.conv_block = nn.Sequential(
            nn.Conv2d(cin, cout, kernel_size, stride, padding),
        )
        self.act = nn.LeakyReLU(0.01, inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.conv_block(x))


class Conv2dTranspose(nn.Module):
    def __init__(
        self,
        cin: int,
        cout: int,
        kernel_size: int,
        stride: int,
        padding: int,
        output_padding: int = 0,
    ):
        super().__init__()
        self.conv_block = nn.Sequential(
            nn.ConvTranspose2d(
                cin, cout, kernel_size, stride, padding, output_padding
            ),
            nn.BatchNorm2d(cout),
        )
        self.act = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.conv_block(x))


class Wav2Lip(nn.Module):
    def __init__(self):
        super().__init__()
        self.face_encoder_blocks = nn.ModuleList(
            [
                nn.Sequential(Conv2d(6, 16, kernel_size=7, stride=1, padding=3)),
                nn.Sequential(
                    Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
                    Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True),
                    Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True),
                ),
                nn.Sequential(
                    Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
                    Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
                    Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
                    Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
                ),
                nn.Sequential(
                    Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
                    Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
                    Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
                ),
                nn.Sequential(
                    Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
                    Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True),
                    Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True),
                ),
                nn.Sequential(
                    Conv2d(256, 512, kernel_size=3, stride=2, padding=1),
                    Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True),
                ),
                nn.Sequential(
                    Conv2d(512, 512, kernel_size=3, stride=1, padding=0),
                    Conv2d(512, 512, kernel_size=1, stride=1, padding=0),
                ),
            ]
        )

        self.audio_encoder = nn.Sequential(
            Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(32, 64, kernel_size=3, stride=(3, 1), padding=1),
            Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(64, 128, kernel_size=3, stride=3, padding=1),
            Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(128, 256, kernel_size=3, stride=(3, 2), padding=1),
            Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(256, 512, kernel_size=3, stride=1, padding=0),
            Conv2d(512, 512, kernel_size=1, stride=1, padding=0),
        )

        self.face_decoder_blocks = nn.ModuleList(
            [
                nn.Sequential(Conv2d(512, 512, kernel_size=1, stride=1, padding=0)),
                nn.Sequential(
                    Conv2dTranspose(1024, 512, kernel_size=3, stride=1, padding=0),
                    Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True),
                ),
                nn.Sequential(
                    Conv2dTranspose(
                        1024, 512, kernel_size=3, stride=2, padding=1, output_padding=1
                    ),
                    Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True),
                    Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True),
                ),
                nn.Sequential(
                    Conv2dTranspose(
                        768, 384, kernel_size=3, stride=2, padding=1, output_padding=1
                    ),
                    Conv2d(384, 384, kernel_size=3, stride=1, padding=1, residual=True),
                    Conv2d(384, 384, kernel_size=3, stride=1, padding=1, residual=True),
                ),
                nn.Sequential(
                    Conv2dTranspose(
                        512, 256, kernel_size=3, stride=2, padding=1, output_padding=1
                    ),
                    Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True),
                    Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True),
                ),
                nn.Sequential(
                    Conv2dTranspose(
                        320, 128, kernel_size=3, stride=2, padding=1, output_padding=1
                    ),
                    Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
                    Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
                ),
                nn.Sequential(
                    Conv2dTranspose(
                        160, 64, kernel_size=3, stride=2, padding=1, output_padding=1
                    ),
                    Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
                    Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
                ),
            ]
        )

        self.output_block = nn.Sequential(
            Conv2d(80, 32, kernel_size=3, stride=1, padding=1),
            nn.Conv2d(32, 3, kernel_size=1, stride=1, padding=0),
            nn.Sigmoid(),
        )

    def forward(
        self, audio_sequences: torch.Tensor, face_sequences: torch.Tensor
    ) -> torch.Tensor:
        b = audio_sequences.size(0)
        input_dim_size = len(face_sequences.size())
        if input_dim_size > 4:
            audio_sequences = torch.cat(
                [audio_sequences[:, i] for i in range(audio_sequences.size(1))], dim=0
            )
            face_sequences = torch.cat(
                [face_sequences[:, :, i] for i in range(face_sequences.size(2))], dim=0
            )

        audio_embedding = self.audio_encoder(audio_sequences)
        feats = []
        x = face_sequences
        for f in self.face_encoder_blocks:
            x = f(x)
            feats.append(x)

        x = audio_embedding
        for f in self.face_decoder_blocks:
            x = f(x)
            try:
                x = torch.cat((x, feats[-1]), dim=1)
            except Exception as exc:
                raise RuntimeError(
                    f"Decoder shape mismatch: {x.size()} vs {feats[-1].size()}"
                ) from exc
            feats.pop()

        x = self.output_block(x)
        if input_dim_size > 4:
            x = torch.split(x, b, dim=0)
            outputs = torch.stack(x, dim=2)
        else:
            outputs = x
        return outputs


def _build_mel_filterbank(
    sr: int = SAMPLE_RATE,
    n_fft: int = N_FFT,
    n_mels: int = NUM_MELS,
    fmin: float = FMIN,
    fmax: float = FMAX,
) -> np.ndarray:
    """Build a Slaney-style mel filterbank without requiring librosa/scipy."""

    def hz_to_mel(hz: np.ndarray) -> np.ndarray:
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    def mel_to_hz(mel: np.ndarray) -> np.ndarray:
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    fft_freqs = np.linspace(0.0, sr / 2.0, n_fft // 2 + 1)
    mel_points = np.linspace(hz_to_mel(np.array(fmin)), hz_to_mel(np.array(fmax)), n_mels + 2)
    hz_points = mel_to_hz(mel_points)

    fb = np.zeros((n_mels, n_fft // 2 + 1), dtype=np.float32)
    for m in range(n_mels):
        f_left, f_center, f_right = hz_points[m], hz_points[m + 1], hz_points[m + 2]
        up_slope = (fft_freqs - f_left) / max(1e-6, f_center - f_left)
        down_slope = (f_right - fft_freqs) / max(1e-6, f_right - f_center)
        fb[m] = np.maximum(0.0, np.minimum(up_slope, down_slope))
        enorm = 2.0 / max(1e-6, f_right - f_left)
        fb[m] *= enorm
    return fb


def compute_mel_spectrogram(wav_16k: np.ndarray) -> np.ndarray:
    """Convert 16 kHz mono float32 audio into an (80, T) normalized mel spectrogram."""
    if wav_16k.size == 0:
        return np.zeros((NUM_MELS, MEL_STEP_SIZE), dtype=np.float32)

    # Pre-emphasis filter: y[n] = x[n] - 0.97 * x[n-1]
    emphasized = np.empty_like(wav_16k, dtype=np.float32)
    emphasized[0] = wav_16k[0]
    emphasized[1:] = wav_16k[1:] - PREEMPHASIS * wav_16k[:-1]

    window = torch.hann_window(WIN_SIZE)
    tensor_wav = torch.from_numpy(emphasized)
    stft = torch.stft(
        tensor_wav,
        n_fft=N_FFT,
        hop_length=HOP_SIZE,
        win_length=WIN_SIZE,
        window=window,
        center=True,
        pad_mode="reflect",
        return_complex=True,
    )
    mag = torch.abs(stft).numpy()
    mel_basis = _build_mel_filterbank()
    mel = np.dot(mel_basis, mag)
    min_amp = np.exp(MIN_LEVEL_DB / 20.0 * np.log(10.0))
    db = 20.0 * np.log10(np.maximum(min_amp, mel)) - REF_LEVEL_DB
    normalized = np.clip(
        (2.0 * MAX_ABS_VALUE) * ((db - MIN_LEVEL_DB) / (-MIN_LEVEL_DB)) - MAX_ABS_VALUE,
        -MAX_ABS_VALUE,
        MAX_ABS_VALUE,
    )
    return normalized.astype(np.float32)


def resample_stereo_44100_to_mono_16000(full_audio: np.ndarray) -> np.ndarray:
    """Resample (2, N) int16 44.1 kHz stereo audio to 1D float32 16 kHz mono."""
    if full_audio.size == 0:
        return np.zeros(0, dtype=np.float32)
    stereo = np.ascontiguousarray(full_audio.T, dtype=np.int16)
    frame = av.AudioFrame.from_ndarray(
        stereo.reshape(1, -1), format="s16", layout="stereo"
    )
    frame.sample_rate = 44100
    resampler = av.AudioResampler(format="fltp", layout="mono", rate=SAMPLE_RATE)
    chunks: List[np.ndarray] = []
    for resampled in resampler.resample(frame):
        chunks.append(resampled.to_ndarray().reshape(-1))
    for resampled in resampler.resample(None):
        chunks.append(resampled.to_ndarray().reshape(-1))
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(chunks).astype(np.float32)


_MODEL_CACHE: Optional[Wav2Lip] = None


def _load_wav2lip_model(
    checkpoint_path: Path = DEFAULT_WAV2LIP_CHECKPOINT,
) -> Optional[Wav2Lip]:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if not checkpoint_path.is_file():
        return None
    checkpoint = torch.load(str(checkpoint_path), map_location="cpu", weights_only=False)
    state_dict = checkpoint.get("state_dict", checkpoint)
    cleaned = {k.replace("module.", ""): v for k, v in state_dict.items()}
    model = Wav2Lip()
    model.load_state_dict(cleaned)
    model.eval()
    _MODEL_CACHE = model
    return model


def generate_lipsync_face_frames(
    portrait_bgr: np.ndarray,
    full_audio_44100: np.ndarray,
    fps: float,
    total_frames: int,
    face_box: Tuple[int, int, int, int],
    batch_size: int = 32,
) -> Optional[List[np.ndarray]]:
    """
    Generate lip-synced lower-face patches (at face_box resolution) for each frame.
    Returns None if the Wav2Lip checkpoint is unavailable.
    """
    model = _load_wav2lip_model()
    if model is None:
        return None

    wav_16k = resample_stereo_44100_to_mono_16000(full_audio_44100)
    mel = compute_mel_spectrogram(wav_16k)
    mel_idx_multiplier = 80.0 / fps

    mel_chunks: List[np.ndarray] = []
    for frame_idx in range(total_frames):
        start_idx = int(frame_idx * mel_idx_multiplier)
        if start_idx + MEL_STEP_SIZE > mel.shape[1]:
            chunk = mel[:, max(0, mel.shape[1] - MEL_STEP_SIZE) :]
            if chunk.shape[1] < MEL_STEP_SIZE:
                pad_w = MEL_STEP_SIZE - chunk.shape[1]
                chunk = np.pad(chunk, ((0, 0), (0, pad_w)), mode="edge")
        else:
            chunk = mel[:, start_idx : start_idx + MEL_STEP_SIZE]
        mel_chunks.append(chunk)

    y1, y2, x1, x2 = face_box
    face_crop = portrait_bgr[y1:y2, x1:x2]
    face_96 = cv2.resize(face_crop, (96, 96), interpolation=cv2.INTER_AREA)

    img_masked = face_96.copy()
    img_masked[48:, :] = 0
    face_input = np.concatenate((img_masked, face_96), axis=2).astype(np.float32) / 255.0
    face_tensor_single = torch.from_numpy(face_input.transpose(2, 0, 1)).unsqueeze(0)

    crop_w = x2 - x1
    crop_h = y2 - y1
    ref_lab = cv2.cvtColor(face_crop, cv2.COLOR_BGR2LAB).astype(np.float32)
    ref_mean = ref_lab.mean(axis=(0, 1), keepdims=True)
    ref_std = ref_lab.std(axis=(0, 1), keepdims=True) + 1e-5
    raw_results: List[np.ndarray] = []

    with torch.no_grad():
        for start in range(0, total_frames, batch_size):
            end = min(total_frames, start + batch_size)
            batch_mels = np.stack(mel_chunks[start:end], axis=0)[:, None, :, :]
            mel_tensor = torch.from_numpy(batch_mels).float()
            img_tensor = face_tensor_single.repeat(end - start, 1, 1, 1)

            pred = model(mel_tensor, img_tensor)
            pred_np = (pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.0).clip(0, 255).astype(
                np.uint8
            )
            for p_face in pred_np:
                upscaled = cv2.resize(
                    p_face, (crop_w, crop_h), interpolation=cv2.INTER_LANCZOS4
                )
                # Denoise 96x96 GAN artifacts while preserving lip edges
                denoised = cv2.bilateralFilter(upscaled, 5, 22, 22)
                # Subtle LAB color-tone alignment with the native HD portrait
                pred_lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB).astype(np.float32)
                pred_mean = pred_lab.mean(axis=(0, 1), keepdims=True)
                pred_std = pred_lab.std(axis=(0, 1), keepdims=True) + 1e-5
                matched_lab = (pred_lab - pred_mean) * (ref_std / pred_std) + ref_mean
                blended_lab = np.clip(0.55 * matched_lab + 0.45 * pred_lab, 0, 255).astype(
                    np.uint8
                )
                color_matched = cv2.cvtColor(blended_lab, cv2.COLOR_LAB2BGR)
                # Gentle sharpening without amplifying blockiness
                blurred = cv2.GaussianBlur(color_matched, (0, 0), 1.1)
                sharpened = cv2.addWeighted(color_matched, 1.22, blurred, -0.22, 0)
                raw_results.append(sharpened)

    # Temporal smoothing across adjacent frames to eliminate lip flicker/jitter
    n = len(raw_results)
    if n <= 2:
        return raw_results
    smoothed: List[np.ndarray] = [raw_results[0]]
    for i in range(1, n - 1):
        frame_avg = (
            0.22 * raw_results[i - 1].astype(np.float32)
            + 0.56 * raw_results[i].astype(np.float32)
            + 0.22 * raw_results[i + 1].astype(np.float32)
        )
        smoothed.append(np.clip(frame_avg, 0, 255).astype(np.uint8))
    smoothed.append(raw_results[-1])
    return smoothed
