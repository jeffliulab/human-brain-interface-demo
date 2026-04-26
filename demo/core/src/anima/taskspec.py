from datetime import datetime, timezone

UTC = timezone.utc
from typing import Literal

from pydantic import BaseModel, Field

IntentTokenName = Literal[
    # ADL (15)
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
    # Navigation (10)
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
    # Device control (5)
    "TURN_ON_LIGHT",
    "TURN_OFF_LIGHT",
    "ADJUST_TV",
    "CALL_ELEVATOR",
    "OPEN_CURTAIN",
    # Emergency (2)
    "CALL_HELP",
    "EMERGENCY_STOP",
    # Meta (3)
    "CONFIRM",
    "CANCEL",
    "UNKNOWN",
]

SubtaskType = Literal[
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
]


class Alternative(BaseModel):
    token: IntentTokenName
    confidence: float = Field(ge=0.0, le=1.0)


class IntentToken(BaseModel):
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
    intent: IntentToken
    subtasks: list[Subtask]
    constraints: Constraints = Field(default_factory=Constraints)
    device: str = "stretch_re3_mock"


class FiveFactors(BaseModel):
    ita: float = Field(default=0.0, ge=0.0, le=1.0)
    mqa: float = Field(default=1.0, ge=0.0, le=1.0)
    sqa: float = Field(default=1.0, ge=0.0, le=1.0)
    goa: float = Field(default=0.0, ge=0.0, le=1.0)
    pea_count: int = 0


class PEARecord(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    intent_token: IntentTokenName
    outcome: Literal["success", "fail", "cancel"]
    user_text: str = ""
