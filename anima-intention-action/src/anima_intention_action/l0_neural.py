"""L0 — Neural Foundation Model layer.

This is the layer added by the BCI adaptation. Original Anima has no L0
because it consumes natural language directly from L1.

A production L0 wraps a neural foundation model such as NDT3, POYO, or
CEBRA, taking 256-channel raw signals and emitting an Intent Token stream
with confidence + drift metadata.

The reference implementation here is deliberately a *mock decoder* that:
  1. Accepts either raw signal arrays or the user-typed text used by the
     demo (where the LLM in L1 is the real decoder).
  2. Generates a decorative 256-channel pseudo-neural waveform for UI.
  3. Reports `drift_score` — the number that MQA reads in L5.

Swap `NeuralDecoder` for a real foundation-model wrapper when integrating
with an actual implant; the upstream contract (waveform + drift score)
does not change.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

import numpy as np


POSITIVE_WORDS = {
    "想", "要", "请", "好", "谢", "舒服",
    "please", "thanks", "want", "nice", "happy",
}
NEGATIVE_WORDS = {
    "疼", "痛", "难受", "不", "累",
    "help", "stop", "emergency", "hurt", "tired",
}


@dataclass(frozen=True)
class TextFeatures:
    length: int
    sentiment: float  # -1 (neg) to +1 (pos)
    hash_int: int
    char_hash_cumsum: np.ndarray  # shape (length,), values in [0, 255]


class NeuralDecoder(Protocol):
    """Interface a real L0 foundation-model wrapper must satisfy."""

    def decode(self, signals: np.ndarray) -> tuple[str, float, float]:
        """Return (intent_token_hint, confidence, drift_score)."""
        ...


def extract_features(text: str) -> TextFeatures:
    """Lightweight features used to colour the decorative waveform.

    In the real BCI pipeline, these features come from the neural
    foundation model's latent embedding, not from text.
    """
    text = (text or "").strip()
    if not text:
        return TextFeatures(0, 0.0, 0, np.zeros(0, dtype=np.uint8))

    lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in lower)
    sentiment = (pos - neg) / max(pos + neg, 1)

    h = hashlib.sha256(text.encode("utf-8")).digest()
    hash_int = int.from_bytes(h[:8], "little")

    char_hash = np.frombuffer(
        hashlib.sha256(text.encode("utf-8")).digest() * ((len(text) // 32) + 1),
        dtype=np.uint8,
    )[: len(text)]
    cumsum = np.cumsum(char_hash) % 256

    return TextFeatures(
        length=len(text),
        sentiment=sentiment,
        hash_int=hash_int,
        char_hash_cumsum=cumsum.astype(np.uint8),
    )


def generate_waveform(
    text: str,
    seed: str = "anima-intention-action",
    n_channels: int = 256,
    n_frames: int = 30,
    sample_rate_hz: float = 30.0,
) -> np.ndarray:
    """Generate a pseudo 256-channel waveform driven by text features.

    The shape, smoothing, and noise model match what you'd see from a
    real MEA recording at frame-level detail; the content is fabricated.
    UI layers MUST label rendered output as "decoding preview", not
    ground-truth neural activity.
    """
    feat = extract_features(text)
    rng = np.random.default_rng(abs(hash((seed, feat.hash_int))) % (2**32))

    channel_idx = np.arange(n_channels)
    amp_base = 0.5 + 0.5 * np.sin(
        (feat.hash_int % 1000) / 1000 * 2 * np.pi + channel_idx * 0.07
    )
    amp_base = amp_base.astype(np.float32)

    base_freq = 5.0 + feat.sentiment * 10.0 + rng.uniform(0, 2)
    if feat.char_hash_cumsum.size:
        phase_seed = feat.char_hash_cumsum[
            np.arange(n_channels) % feat.char_hash_cumsum.size
        ].astype(np.float32)
    else:
        phase_seed = (channel_idx * 13).astype(np.float32)
    phase = (phase_seed / 256.0) * 2 * np.pi

    t = np.arange(n_frames).astype(np.float32) / sample_rate_hz
    signal = amp_base[:, None] * np.sin(
        2 * np.pi * base_freq * t[None, :] + phase[:, None]
    )

    noise = rng.normal(0, 0.15, size=(n_channels, n_frames)).astype(np.float32)
    kernel = np.array([0.25, 0.5, 0.25], dtype=np.float32)
    noise_smoothed = np.apply_along_axis(
        lambda r: np.convolve(r, kernel, mode="same"), axis=0, arr=noise
    )

    return (signal + noise_smoothed).astype(np.float32)


def downsample_channels(wave: np.ndarray, n: int = 16) -> np.ndarray:
    """Pick n evenly-spaced channels for WebSocket transport."""
    if wave.shape[0] <= n:
        return wave
    idx = np.linspace(0, wave.shape[0] - 1, n, dtype=int)
    return wave[idx]


def waveform_to_payload(wave: np.ndarray, n_channels: int = 16) -> dict:
    ds = downsample_channels(wave, n_channels)
    return {
        "n_channels": int(ds.shape[0]),
        "n_frames": int(ds.shape[1]),
        "channels": ds.round(3).tolist(),
    }
