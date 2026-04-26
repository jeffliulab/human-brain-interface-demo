import numpy as np

from src.anima.l0_input import (
    extract_features,
    generate_waveform,
    waveform_to_payload,
)


def test_extract_features_empty():
    f = extract_features("")
    assert f.length == 0
    assert f.sentiment == 0.0


def test_extract_features_sentiment():
    pos = extract_features("我想喝水，请")
    neg = extract_features("好疼，stop")
    assert pos.sentiment > 0
    assert neg.sentiment < 0


def test_waveform_shape():
    w = generate_waveform("我想喝水", n_channels=256, n_frames=30)
    assert w.shape == (256, 30)
    assert w.dtype == np.float32


def test_waveform_deterministic_per_text():
    w1 = generate_waveform("我想喝水", seed="s")
    w2 = generate_waveform("我想喝水", seed="s")
    assert np.allclose(w1, w2)


def test_waveform_differs_per_text():
    w1 = generate_waveform("我想喝水", seed="s")
    w2 = generate_waveform("我想睡觉", seed="s")
    assert not np.allclose(w1, w2)


def test_payload_downsamples():
    w = generate_waveform("我想喝水")
    p = waveform_to_payload(w, n_channels=8)
    assert p["n_channels"] == 8
    assert len(p["channels"]) == 8
