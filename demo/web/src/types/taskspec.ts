// Mirrors demo/shared/schemas/*.json (Pydantic models in core).
// v0.1: hand-synchronized; later we can codegen from the JSON Schemas.

export type IntentTokenName =
  | "DRINK_WATER" | "EAT_FOOD" | "GRASP" | "LIFT" | "DELIVER"
  | "PLACE" | "RELEASE" | "WIPE_MOUTH" | "SCRATCH_ITCH" | "ADJUST_PILLOW"
  | "ADJUST_BLANKET" | "HAND_OVER" | "OPEN_BOTTLE" | "POUR" | "STIR"
  | "MOVE_FORWARD" | "MOVE_BACKWARD" | "TURN_LEFT" | "TURN_RIGHT"
  | "GOTO_BED" | "GOTO_TABLE" | "GOTO_DOOR" | "GOTO_BATHROOM"
  | "FOLLOW_CAREGIVER" | "STOP_MOVING"
  | "TURN_ON_LIGHT" | "TURN_OFF_LIGHT" | "ADJUST_TV" | "CALL_ELEVATOR" | "OPEN_CURTAIN"
  | "CALL_HELP" | "EMERGENCY_STOP"
  | "CONFIRM" | "CANCEL" | "UNKNOWN";

export type SubtaskType = "locate" | "grasp" | "lift" | "deliver" | "navigate" | "release";

export interface Alternative {
  token: IntentTokenName;
  confidence: number;
}

export interface IntentToken {
  token: IntentTokenName;
  confidence: number;
  requires_confirmation: boolean;
  alternatives: Alternative[];
  drift_score: number;
  timestamp: string;
  source_text: string;
}

export interface Subtask {
  name: string;
  type: SubtaskType;
}

export interface Constraints {
  max_force_n: number;
  timeout_s: number;
}

export interface TaskSpec {
  intent: IntentToken;
  subtasks: Subtask[];
  constraints: Constraints;
  device: string;
}

export interface FiveFactors {
  ita: number;
  mqa: number;
  sqa: number;
  goa: number;
  pea_count: number;
}

// WebSocket event envelope
export interface WSEvent<T = unknown> {
  event: string;
  data: T;
}

export type LayerName = "L0" | "L1" | "L2" | "L3" | "L4" | "L5";

export interface SignalFramePayload {
  n_channels: number;
  n_frames: number;
  channels: number[][]; // [channel][frame]
}

export type BTStatus = "running" | "success" | "failure";

export interface BTTickEvent {
  node: string;
  status: BTStatus;
}

export interface AuditEntry {
  outcome: "success" | "fail" | "cancel";
  intent: IntentTokenName;
  timestamp: string;
}
