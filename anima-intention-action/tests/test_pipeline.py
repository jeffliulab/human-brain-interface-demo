"""Smoke tests for the reference pipeline.

Run with:
    pytest tests/
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from anima_intention_action import (
    Constraints,
    IntentToken,
    Subtask,
    TaskSpec,
)
from anima_intention_action.l0_neural import generate_waveform, waveform_to_payload
from anima_intention_action.l2_planner import build_tree, run_tree
from anima_intention_action.l5_assessment import (
    compute_five_factors,
    compute_sqa,
    log_pea,
)
from anima_intention_action.test_and_check import run_gates


def _taskspec(ita: float = 0.9, drift: float = 0.05) -> TaskSpec:
    return TaskSpec(
        intent=IntentToken(
            token="DRINK_WATER",
            confidence=ita,
            drift_score=drift,
            source_text="I want some water",
        ),
        subtasks=[
            Subtask(name="locate_cup", type="locate"),
            Subtask(name="navigate_to_cup", type="navigate"),
            Subtask(name="grasp_cup", type="grasp"),
            Subtask(name="lift_cup", type="lift"),
            Subtask(name="deliver_to_mouth", type="deliver"),
        ],
        constraints=Constraints(max_force_n=8.0, timeout_s=15.0),
    )


def test_l0_waveform_shape():
    wave = generate_waveform("hello", n_channels=256, n_frames=30)
    assert wave.shape == (256, 30)
    payload = waveform_to_payload(wave, n_channels=16)
    assert payload["n_channels"] == 16
    assert payload["n_frames"] == 30
    assert len(payload["channels"]) == 16


def test_gates_pass_on_healthy_taskspec():
    known = {"locate": object, "grasp": object, "lift": object,
             "deliver": object, "navigate": object, "release": object}
    results = run_gates(_taskspec(), known)
    assert all(r.ok for r in results), [(r.gate, r.reason) for r in results if not r.ok]


def test_safety_gate_rejects_low_ita():
    known = {"locate": object, "grasp": object, "lift": object,
             "deliver": object, "navigate": object, "release": object}
    results = run_gates(_taskspec(ita=0.4), known)
    assert not results[-1].ok  # safety gate last
    assert results[-1].gate == "safety"


def test_skill_gate_rejects_unknown_type():
    results = run_gates(_taskspec(), known_skill_types={})
    assert any((not r.ok and r.gate == "skill") for r in results)


def test_behavior_tree_runs_to_success_with_mocks():
    tree = build_tree(_taskspec(), skill_registry={})  # empty → MockSkillBehaviour
    status = asyncio.run(run_tree(tree, tick_interval_s=0.01, max_ticks=200))
    assert status.name == "SUCCESS"


def test_five_factors_and_pea_log(tmp_path: Path):
    pea_log = tmp_path / "pea_log.jsonl"
    pre = compute_five_factors(_taskspec(), pea_log=pea_log)
    assert 0.0 <= pre.ita <= 1.0
    assert 0.0 <= pre.mqa <= 1.0
    assert 0.0 <= pre.goa <= pre.ita  # multiplicative → GOA ≤ ITA

    log_pea(pea_log, _taskspec().intent, "success")
    assert pea_log.exists()
    assert pea_log.read_text().count("\n") == 1

    sqa = compute_sqa(pea_log)
    assert 0.0 <= sqa <= 1.0
