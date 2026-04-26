# 02 · Skill Registry for Assistive Use

> The Skill Registry inherits from the original Anima L3 design unchanged. What's new is **the catalog**: skills tuned for high-cervical SCI / ALS users, tagged with granularity level and risk tier.

## Design rules (inherited from original Anima)

1. Function Calling + Affordance Scoring; no RAG while count < 100
2. Each skill is a self-describing object with a `pre`, `args`, `post`, and `affordance(env)` function
3. Skills compose into behavior trees via the L2 planner
4. Skill set is closed; LLM may not invent skills

## New tags for BCI / assistive context

```ts
type SkillSpec = {
  name: string;
  description: string;
  granularity_level: 0 | 1 | 2 | 3;     // micro → ADL
  risk_tier: "low" | "medium" | "high"; // gates Test-and-Check
  device_types: Array<"manipulator" | "wheelchair" | "quadruped" | "humanoid" | "prosthesis">;
  args_schema: ZodSchema;
  pre: (env: Env) => boolean;
  post: (env: Env) => boolean;
  affordance: (env: Env) => number;     // [0, 1]
  on_fail: "retry" | "negotiate" | "abort";
}
```

## Granularity levels

| Level | Meaning | Example | Bandwidth fit |
|---|---|---|---|
| **L0 micro** | single-joint velocity | `move_joint_velocity` | needs continuous decoding (rare in BCI) |
| **L1 trajectory** | named segment | `move_to_target` | shared autonomy mid-bandwidth |
| **L2 atomic skill** | full primitive | `grasp_cup`, `pour_water` | typical BCI pick |
| **L3 ADL macro** | daily activity | `drink_water`, `bring_object` | best fit for 5-8 bits/s |

**Demo defaults to L2/L3.** Lower granularity is exposed only if the upstream confidence is very high and the user explicitly opts in.

## Initial skill catalog (matches ALS user-priority research)

Source: ALS user surveys (取物 89%, 近身动作 88%, 按按钮 87%, 端饮料 86%).

### L3 ADL macros (highest priority)

| Skill | Devices | Risk | Notes |
|---|---|---|---|
| `drink_water` | manipulator | medium | end-effector to mouth; force-limited |
| `bring_object` | manipulator + quadruped | medium | object localization required |
| `move_to_room` | wheelchair + quadruped | medium | nav stack required |
| `press_button` | manipulator | low | TV remote, light switch |
| `feed_self_one_bite` | manipulator | medium | Obi-class motion + safety |
| `scratch_face` | manipulator | high | near-face high-precision |
| `adjust_blanket` | manipulator | low | low-precision soft contact |
| `call_caregiver` | system | low | non-physical |

### L2 atomic skills (composed by macros)

| Skill | Devices | Risk |
|---|---|---|
| `locate_object` | (perception) | low |
| `grasp` | manipulator | medium |
| `lift` | manipulator | low |
| `place` | manipulator | medium |
| `pour` | manipulator | high |
| `move_to_pose` | manipulator | low |
| `navigate_to` | wheelchair, quadruped | medium |
| `follow_user` | quadruped | low |
| `open_gripper` | manipulator | low |
| `close_gripper` | manipulator | medium |

### L0/L1 (rarely used but available)

| Skill | Devices | Risk |
|---|---|---|
| `nudge_left/right/up/down` | manipulator | low |
| `stop_immediately` | all | low (safety primitive) |
| `slow_down_50%` | all | low |

## Affordance scoring sketch

```ts
function grasp_affordance(env: Env, args: GraspArgs): number {
  if (!env.objects.find(o => o.id === args.target)) return 0;
  if (env.gripper.occupied) return 0;
  if (env.target_distance > env.arm_reach) return 0.1;
  if (env.target_size_mm < 5) return 0.3;       // too small
  if (env.target_pose_uncertainty > 0.2) return 0.5;
  return 0.9;
}
```

The affordance score multiplies into GOA computation (see doc 03 §GOA).

## Risk-tier consequences in Test-and-Check

| Risk | Min confidence to skip 2nd-confirm | Caregiver consent required? |
|---|---|---|
| low | 0.7 | no |
| medium | 0.85 | no |
| high | 0.95 | **yes** if caregiver present |

## Intent token vocabulary (parallel to skill registry)

The L0 → L1 boundary uses ~30-50 intent tokens. Each token maps to one or more skills via the L1 LLM Parser.

Example token → skill mapping:
```
DRINK_WATER       → drink_water (L3 macro)
GRASP             → grasp (L2)
BRING_REMOTE      → bring_object(target=remote)
NAV_TO_BATHROOM   → move_to_room(target=bathroom)
CALL_HELP         → call_caregiver
EMERGENCY_STOP    → stop_immediately (system-level)
NUDGE_LEFT        → nudge_left (L1)
... (~25 more)
```

The token vocabulary is patient-specific and grows with PEA history (frequent ad-hoc tasks become new tokens after caregiver review).
