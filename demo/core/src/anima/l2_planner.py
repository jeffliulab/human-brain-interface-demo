"""L2 — Planner.

Turns a TaskSpec into a py_trees Sequence. For v0.2, when the sim is available
each Subtask.type resolves to a real SimSkillBehaviour driving MuJoCo; when
the sim stack isn't available we fall back to the v0.1 mock.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

import py_trees

from src.anima.l3_skill import SKILL_REGISTRY, MockSkillBehaviour
from src.anima.taskspec import TaskSpec
from src.sim import get_sim


def build_tree(
    taskspec: TaskSpec,
    on_status_change: Callable[[str, str], Awaitable[None]] | None = None,
    loop: asyncio.AbstractEventLoop | None = None,
) -> py_trees.trees.BehaviourTree:
    root = py_trees.composites.Sequence(
        name=taskspec.intent.token.lower(), memory=True
    )
    sim_available = get_sim().available
    ctx: dict = {}  # shared blackboard across the BT

    for st in taskspec.subtasks:
        skill_cls = SKILL_REGISTRY.get(st.type) if sim_available else None
        if skill_cls is not None:
            root.add_child(
                skill_cls(
                    name=st.name,
                    ctx=ctx,
                    on_status_change=on_status_change,
                    loop=loop,
                )
            )
        else:
            root.add_child(
                MockSkillBehaviour(
                    name=st.name,
                    ticks_to_success=3,
                    on_status_change=on_status_change,
                    loop=loop,
                )
            )
    return py_trees.trees.BehaviourTree(root)


async def run_tree(
    tree: py_trees.trees.BehaviourTree,
    tick_interval_s: float = 0.4,
    max_ticks: int = 3000,
) -> py_trees.common.Status:
    """Drive a tree by ticking with asyncio.sleep between ticks."""
    for _ in range(max_ticks):
        tree.tick()
        status = tree.root.status
        if status in (py_trees.common.Status.SUCCESS, py_trees.common.Status.FAILURE):
            return status
        await asyncio.sleep(tick_interval_s)
    return tree.root.status
