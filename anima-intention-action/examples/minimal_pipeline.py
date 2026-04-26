"""Minimal end-to-end example: TaskSpec → gates → behaviour tree → PEA.

Runs without any LLM, robot, or sim. Demonstrates how the six layers
plug together and what a Pre-execution FiveFactors snapshot looks like.

  $ python examples/minimal_pipeline.py
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
from anima_intention_action.l2_planner import build_tree, run_tree
from anima_intention_action.l3_skill import MockSkillBehaviour
from anima_intention_action.l5_assessment import compute_five_factors, log_pea
from anima_intention_action.test_and_check import run_gates


def build_example_taskspec() -> TaskSpec:
    return TaskSpec(
        intent=IntentToken(
            token="DRINK_WATER",
            confidence=0.88,
            drift_score=0.07,
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


async def main() -> None:
    taskspec = build_example_taskspec()

    # Gates — must pass before we hand the tree to the executor.
    # Empty registry → skills are not mocked out of the registry, but the
    # gate only checks *names*; the L2 planner will substitute
    # MockSkillBehaviour because we also pass an empty registry to build_tree.
    known_types = {"locate": object, "grasp": object, "lift": object,
                   "deliver": object, "navigate": object, "release": object}
    gate_results = run_gates(taskspec, known_types)
    for r in gate_results:
        flag = "PASS" if r.ok else "FAIL"
        print(f"  [{flag}] {r.gate:<10} {r.reason}")
    if not all(r.ok for r in gate_results):
        print("Aborting — a gate failed.")
        return

    # Pre-execution five factors.
    with tempfile.TemporaryDirectory() as tmp:
        pea_log = Path(tmp) / "pea_log.jsonl"
        pre = compute_five_factors(taskspec, pea_log=pea_log)
        print(f"\nPre-execution five factors: {pre.model_dump()}")

        # Build + tick the tree (all skills fall through to MockSkillBehaviour).
        tree = build_tree(taskspec, skill_registry={})  # empty → all mocks
        status = await run_tree(tree, tick_interval_s=0.05, max_ticks=200)
        print(f"Tree terminated with: {status.name}")

        outcome = "success" if status.name == "SUCCESS" else "fail"
        log_pea(pea_log, taskspec.intent, outcome)

        post = compute_five_factors(taskspec, pea_log=pea_log)
        print(f"Post-execution five factors: {post.model_dump()}")


if __name__ == "__main__":
    asyncio.run(main())
