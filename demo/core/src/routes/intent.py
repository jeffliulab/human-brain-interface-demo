"""POST /api/intent — full pipeline L0→L5 with live WebSocket updates."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.anima import l0_input, l1_parser, l2_planner, l5_assessment
from src.anima.taskspec import TaskSpec
from src.routes.ws import manager

logger = logging.getLogger(__name__)

router = APIRouter()


class IntentRequest(BaseModel):
    user_text: str = Field(min_length=1, max_length=200)
    drift: float = Field(default=0.05, ge=0.0, le=1.0)
    ui_language: str = "zh-CN"


@router.post("/api/intent", response_model=TaskSpec)
async def submit_intent(body: IntentRequest) -> TaskSpec:
    loop = asyncio.get_running_loop()

    # L0 — waveform broadcast (decorative)
    await manager.broadcast("layer.activate", {"layer": "L0"})
    wave = l0_input.generate_waveform(body.user_text)
    await manager.broadcast("signal.frame", l0_input.waveform_to_payload(wave))

    # L1 — LLM Intent Parser (runs in thread to avoid blocking loop)
    await manager.broadcast("layer.activate", {"layer": "L1"})
    taskspec: TaskSpec = await asyncio.to_thread(
        l1_parser.parse,
        body.user_text,
        body.drift,
        body.ui_language,
    )
    await manager.broadcast("taskspec.ready", taskspec.model_dump(mode="json"))

    # L5 — initial five-factor (pre-execution GOA)
    factors = l5_assessment.compute_five_factors(taskspec)
    await manager.broadcast("factor.update", factors.model_dump(mode="json"))

    # L2 — build tree and schedule async execution
    await manager.broadcast("layer.activate", {"layer": "L2"})

    async def on_node(name: str, status: str) -> None:
        await manager.broadcast("bt.tick", {"node": name, "status": status})

    # Side-channel for CALL_HELP: the skill does a beacon pose, the route
    # broadcasts the actual notify event so the UI can render a caregiver
    # alert without waiting for BT completion.
    if taskspec.intent.token == "CALL_HELP":
        await manager.broadcast(
            "help.called",
            {"source_text": body.user_text, "intent": "CALL_HELP"},
        )

    tree = l2_planner.build_tree(taskspec, on_status_change=on_node, loop=loop)
    asyncio.create_task(_run_and_finalize(tree, taskspec))

    return taskspec


async def _run_and_finalize(tree, taskspec: TaskSpec) -> None:
    from src.sim import get_sim

    await manager.broadcast("layer.activate", {"layer": "L3"})
    result = await l2_planner.run_tree(tree, tick_interval_s=0.1)

    await manager.broadcast("layer.activate", {"layer": "L4"})
    # An empty plan (UNKNOWN intent, or intent with no subtasks) trivially
    # "succeeds" as a py_trees Sequence — force it to fail so the audit log
    # and SQA reflect that Anima could not carry out the request.
    estop = get_sim().estop_active.is_set() if get_sim().available else False
    if estop:
        outcome = "cancel"
    elif result.name == "SUCCESS" and not taskspec.subtasks:
        outcome = "fail"
    else:
        outcome = "success" if result.name == "SUCCESS" else "fail"

    await manager.broadcast("layer.activate", {"layer": "L5"})
    record = l5_assessment.log_pea(taskspec.intent, outcome)
    factors = l5_assessment.compute_five_factors(taskspec)
    await manager.broadcast("factor.update", factors.model_dump(mode="json"))
    await manager.broadcast(
        "audit.append",
        {
            "outcome": outcome,
            "intent": record.intent_token,
            "timestamp": record.timestamp.isoformat(),
        },
    )
