"""L1 — LLM Intent Parser.

Takes natural language text → LLM (tool calling) → TaskSpec.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

from src.anima.taskspec import (
    Alternative,
    Constraints,
    IntentToken,
    Subtask,
    TaskSpec,
)
from src.config import settings
from src.llm.provider import get_client

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "llm" / "prompts"
SYSTEM_PROMPT_TEMPLATE = (PROMPTS_DIR / "intent_parser.md").read_text(encoding="utf-8")
INTENT_VOCAB = json.loads((PROMPTS_DIR / "intent_vocab.json").read_text(encoding="utf-8"))

EMIT_TASKSPEC_TOOL = {
    "type": "function",
    "function": {
        "name": "emit_taskspec",
        "description": "Emit a structured TaskSpec from the user's intent.",
        "parameters": {
            "type": "object",
            "required": [
                "intent_token",
                "intent_confidence",
                "subtasks",
                "constraints",
            ],
            "properties": {
                "intent_token": {
                    "type": "string",
                    "description": "Exactly one of the 35 vocabulary tokens.",
                },
                "intent_confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "requires_confirmation": {"type": "boolean"},
                "alternatives": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "token": {"type": "string"},
                            "confidence": {"type": "number"},
                        },
                        "required": ["token", "confidence"],
                    },
                },
                "subtasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": [
                                    "locate",
                                    "grasp",
                                    "lift",
                                    "deliver",
                                    "navigate",
                                    "release",
                                    "goto_bed",
                                    "toggle_light",
                                    "toggle_device",
                                    "call_help",
                                ],
                            },
                        },
                        "required": ["name", "type"],
                    },
                },
                "constraints": {
                    "type": "object",
                    "properties": {
                        "max_force_n": {"type": "number"},
                        "timeout_s": {"type": "number"},
                    },
                },
            },
        },
    },
}


def _build_system_prompt(ui_language: str = "zh-CN") -> str:
    return SYSTEM_PROMPT_TEMPLATE.replace(
        "{{intent_vocab_json}}", json.dumps(INTENT_VOCAB, ensure_ascii=False)
    ).replace("{{ui_language}}", ui_language)


def _apply_drift(confidence: float, drift: float, seed_key: str) -> float:
    """Add a small Beta-shaped perturbation proportional to drift.

    Keeps the LLM's output but makes it visibly move under BCI drift.
    """
    rng = np.random.default_rng(abs(hash(seed_key)) % (2**32))
    shake = rng.beta(8, 2) - 0.8  # ~0 mean, small +/-
    perturbed = confidence + drift * shake * 0.3
    return float(max(0.0, min(1.0, perturbed)))


def parse(
    user_text: str,
    drift: float = 0.05,
    ui_language: str = "zh-CN",
) -> TaskSpec:
    """Call the LLM and return a TaskSpec.

    Raises ValueError if the LLM does not return a tool call.
    """
    client = get_client()
    system_prompt = _build_system_prompt(ui_language)
    user_msg = (
        f'User text input: "{user_text}"\n'
        f"Drift score: {drift:.3f}\n"
        f"Caregiver present: true\n"
        f"Active device: stretch_re3_mock"
    )

    resp = client.chat.completions.create(
        model=settings.LLM_MODEL_FAST,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        tools=[EMIT_TASKSPEC_TOOL],
        tool_choice={"type": "function", "function": {"name": "emit_taskspec"}},
        temperature=0.3,
    )

    msg = resp.choices[0].message
    if not msg.tool_calls:
        raise ValueError("LLM did not return a tool call")

    args = json.loads(msg.tool_calls[0].function.arguments)
    return _taskspec_from_args(args, user_text=user_text, drift=drift)


def _taskspec_from_args(args: dict, *, user_text: str, drift: float) -> TaskSpec:
    token = args.get("intent_token", "UNKNOWN")
    raw_conf = float(args.get("intent_confidence", 0.5))
    conf = _apply_drift(raw_conf, drift, seed_key=user_text)

    alternatives_raw = args.get("alternatives") or []
    alternatives = []
    for alt in alternatives_raw[:3]:
        try:
            alternatives.append(
                Alternative(
                    token=alt["token"],
                    confidence=float(alt["confidence"]),
                )
            )
        except (KeyError, ValueError):
            continue

    requires_confirmation = bool(args.get("requires_confirmation", False))
    if conf < 0.7:
        requires_confirmation = True

    subtasks_raw = args.get("subtasks") or []
    subtasks = [Subtask(name=s["name"], type=s["type"]) for s in subtasks_raw]
    # Safety net: canonical plan per supported intent, in case the LLM returns
    # an empty or mistyped subtask list. The 5 v0.3 demo intents each map to a
    # hardcoded sequence that the skill registry can execute end-to-end.
    canonical = _CANONICAL_PLANS.get(token)
    if canonical and not _plan_matches(subtasks, canonical):
        subtasks = [Subtask(name=n, type=t) for n, t in canonical]

    constraints_raw = args.get("constraints") or {}
    constraints = Constraints(
        max_force_n=float(constraints_raw.get("max_force_n", 8.0)),
        timeout_s=float(constraints_raw.get("timeout_s", 15.0)),
    )

    intent = IntentToken(
        token=token if _is_valid_token(token) else "UNKNOWN",
        confidence=conf,
        requires_confirmation=requires_confirmation,
        alternatives=alternatives,
        drift_score=drift,
        source_text=user_text,
    )
    return TaskSpec(intent=intent, subtasks=subtasks, constraints=constraints)


def _is_valid_token(tok: str) -> bool:
    for group in INTENT_VOCAB.values():
        if tok in group:
            return True
    return False


# Canonical demo plans. The LLM is free to emit its own subtask list, but if
# the list doesn't cover the known skill types for a supported intent we fall
# back to the canonical plan so the BT always has something executable.
_CANONICAL_PLANS: dict[str, list[tuple[str, str]]] = {
    "DRINK_WATER": [
        ("locate_cup", "locate"),
        ("navigate_to_cup", "navigate"),
        ("grasp_cup", "grasp"),
        ("lift_cup", "lift"),
        ("deliver_to_mouth", "deliver"),
    ],
    "GOTO_BED": [("goto_bed", "goto_bed")],
    "TURN_OFF_LIGHT": [("turn_off_light", "toggle_light")],
    "TURN_ON_LIGHT": [("turn_on_light", "toggle_light")],
    "ADJUST_TV": [("toggle_tv", "toggle_device")],
    "CALL_HELP": [("call_caregiver", "call_help")],
}


def _plan_matches(subtasks: list[Subtask], canonical: list[tuple[str, str]]) -> bool:
    """True iff the LLM's subtask types line up with the canonical plan."""
    if len(subtasks) != len(canonical):
        return False
    return all(st.type == t for st, (_, t) in zip(subtasks, canonical))
