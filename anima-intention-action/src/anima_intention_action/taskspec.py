"""TaskSpec v2 — the canonical data contract between all six layers.

Every layer boundary in the framework speaks TaskSpec (or a strict subset).
The BCI adaptation extends the original Anima TaskSpec with four fields
required for medical-grade operation:

  * intent_confidence           — ITA input (L5)
  * requires_confirmation       — drives caregiver-channel gating
  * drift_score                 — MQA input (L5), produced by L0
  * estop_channels (implicit)   — enforced by L4 Embodied Adapter

The intent vocabulary (35 tokens) is BCI-compatible: every token is
reachable with 5-8 bits/s bandwidth, and every token maps 1-N to a
behavior-tree template in L2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

UTC = timezone.utc


IntentTokenName = Literal[
    # ADL (Activities of Daily Living) — 15 tokens
    "DRINK_WATER",
    "EAT_FOOD",
    "GRASP",
    "LIFT",
    "DELIVER",
    "PLACE",
    "RELEASE",
    "WIPE_MOUTH",
    "SCRATCH_ITCH",
    "ADJUST_PILLOW",
    "ADJUST_BLANKET",
    "HAND_OVER",
    "OPEN_BOTTLE",
    "POUR",
    "STIR",
    # Navigation — 10 tokens
    "MOVE_FORWARD",
    "MOVE_BACKWARD",
    "TURN_LEFT",
    "TURN_RIGHT",
    "GOTO_BED",
    "GOTO_TABLE",
    "GOTO_DOOR",
    "GOTO_BATHROOM",
    "FOLLOW_CAREGIVER",
    "STOP_MOVING",
    # Device control — 5 tokens
    "TURN_ON_LIGHT",
    "TURN_OFF_LIGHT",
    "ADJUST_TV",
    "CALL_ELEVATOR",
    "OPEN_CURTAIN",
    # Emergency — 2 tokens (non-BCI E-stop is a separate channel, see doc 06)
    "CALL_HELP",
    "EMERGENCY_STOP",
    # Meta — 3 tokens
    "CONFIRM",
    "CANCEL",
    "UNKNOWN",
]

SubtaskType = Literal["locate", "grasp", "lift", "deliver", "navigate", "release"]


class Alternative(BaseModel):
    token: IntentTokenName
    confidence: float = Field(ge=0.0, le=1.0)


class IntentToken(BaseModel):
    """L0 → L1 boundary payload.

    `drift_score` is the neural-manifold drift estimate from the L0 decoder;
    the original Anima framework did not need it because NLU input has no
    cross-day decoder drift.
    """

    token: IntentTokenName
    confidence: float = Field(ge=0.0, le=1.0)
    requires_confirmation: bool = False
    alternatives: list[Alternative] = Field(default_factory=list)
    drift_score: float = Field(default=0.05, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_text: str = ""


class Subtask(BaseModel):
    name: str
    type: SubtaskType


class Constraints(BaseModel):
    max_force_n: float = 8.0
    timeout_s: float = 15.0


class TaskSpec(BaseModel):
    """L1 output → L2 input. Immutable once emitted."""

    intent: IntentToken
    subtasks: list[Subtask]
    constraints: Constraints = Field(default_factory=Constraints)
    device: str = "stretch_re3_mock"


class FiveFactors(BaseModel):
    """L5 event-triggered self-assessment output.

    Per the design invariant, `goa` is computed multiplicatively, not averaged:
        goa = ita * p_plan * sqa
    """

    ita: float = Field(default=0.0, ge=0.0, le=1.0)
    mqa: float = Field(default=1.0, ge=0.0, le=1.0)
    sqa: float = Field(default=1.0, ge=0.0, le=1.0)
    goa: float = Field(default=0.0, ge=0.0, le=1.0)
    pea_count: int = 0


class PEARecord(BaseModel):
    """Post-Execution Assessment entry. Append-only."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    intent_token: IntentTokenName
    outcome: Literal["success", "fail", "cancel"]
    user_text: str = ""
