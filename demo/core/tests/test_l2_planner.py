import asyncio

import py_trees
import pytest

from src.anima.l2_planner import build_tree, run_tree
from src.anima.taskspec import IntentToken, Subtask, TaskSpec


@pytest.mark.asyncio
async def test_drink_water_tree_reaches_success():
    ts = TaskSpec(
        intent=IntentToken(token="DRINK_WATER", confidence=0.9),
        subtasks=[
            Subtask(name="locate_cup", type="locate"),
            Subtask(name="grasp_cup", type="grasp"),
            Subtask(name="lift_cup", type="lift"),
            Subtask(name="deliver_to_mouth", type="deliver"),
        ],
    )

    events = []

    async def on_status(name: str, status: str):
        events.append((name, status))

    loop = asyncio.get_running_loop()
    tree = build_tree(ts, on_status_change=on_status, loop=loop)
    result = await run_tree(tree, tick_interval_s=0.01, max_ticks=50)
    # Let queued coroutines drain
    await asyncio.sleep(0.05)
    assert result == py_trees.common.Status.SUCCESS
    # 4 subtasks × 2 status transitions (running + success) = 8 events
    assert len(events) >= 8
    assert events[0][1] == "running"
    assert events[-1][1] == "success"
