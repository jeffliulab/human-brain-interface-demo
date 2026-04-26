# 01 · Six-Layer Architecture for BCI

> Original Anima is a five-layer cognitive framework. This adaptation adds **L0 Neural Foundation Model layer** at the bottom — the only structural change.

## Why six instead of five

The original Anima was designed for natural-language input. BCI input is fundamentally different: high-dimensional, noisy, sub-symbolic, and best processed by neural foundation models (NDT3, POYO, CEBRA-class). Inserting a layer beneath the existing L1 NLU Parser preserves the original architecture while honestly modeling the BCI input pipeline.

```
┌───────────────────────────────────────────────────────────┐
│ L0  Neural Foundation Model     (★ new)                   │
│     256-channel signals → Intent Token Stream            │
├───────────────────────────────────────────────────────────┤
│ L1  Intent Parser (LLM-as-Parser, preserved)              │
│     Intent Token + Context → TaskSpec                    │
├───────────────────────────────────────────────────────────┤
│ L2  Task Planner (preserved)                              │
│     TaskSpec → BehaviorTree                              │
├───────────────────────────────────────────────────────────┤
│ L3  Skill Registry & Executor (preserved)                 │
│     Function Calling + Affordance Scoring                │
├───────────────────────────────────────────────────────────┤
│ L4  Embodied Adapter (renamed from "Policy")              │
│     Device-agnostic actuation                            │
├───────────────────────────────────────────────────────────┤
│ L5  Self-Assessment (preserved, BCI-mapped — see doc 03)  │
│     ITA / MQA / SQA / GOA / PEA                          │
└───────────────────────────────────────────────────────────┘
                ↕ Cross-cut
        Caregiver Channel & Safety Watchdog
```

## Layer responsibilities

### L0 · Neural Foundation Model

- **Input**: 256-channel raw signals (or processed spike features) at 100-1000 Hz
- **Output**: Intent Token Stream
- **Reference models**: NDT3, POYO, CEBRA, latent-diffusion neural decoders
- **Cross-day stability**: applies neural manifold alignment per session (this matches StairMed's publicly disclosed "跨日神经流形对齐" technique)
- **Failure modes surfaced**: low confidence, drift, channel loss

```ts
type IntentToken = {
  token_id: string;            // from a fixed vocabulary (~30-50)
  confidence: number;          // [0, 1]
  alternatives: Array<{token_id: string; confidence: number}>;
  latency_ms: number;
  drift_score: number;         // [0, 1] — cross-day drift estimate
  session_calibration_age_min: number;
}
```

### L1 · Intent Parser (preserved)

- **Input**: Intent Token + active context (recent PEA, current device, caregiver presence)
- **Output**: TaskSpec JSON (validated by Test-and-Check)
- **Backbone**: LLM (Claude Haiku 4.5 in the demo)
- **Invariant**: never emits motor commands

### L2 · Task Planner (preserved)

- TaskSpec → behavior tree
- Adds medical-safety nodes: `MaxForceDecorator`, `UserConsentGate`

### L3 · Skill Registry & Executor (preserved)

- Function-Calling + Affordance Scoring (no RAG when skills < 100)
- Skills tagged with `granularity_level: 0-3` (see doc 02)
- Skills tagged with `risk_tier: low|medium|high` (gates Test-and-Check)

### L4 · Embodied Adapter (renamed)

- Original Anima had a "Policy" layer assuming a single robot
- BCI use-case is device-agnostic by design
- Each downstream device exposes a uniform `EmbodiedAdapterDescriptor`
- Wheelchair / Kinova / quadruped / humanoid all plug here

```ts
type EmbodiedAdapterDescriptor = {
  device_id: string;
  type: "manipulator" | "wheelchair" | "quadruped" | "humanoid" | "prosthesis";
  dof: number;
  payload_kg: number;
  speed_max_mps: number;
  skills_supported: string[];
  safety_features: string[];
  bandwidth_hz: number;
  latency_p99_ms: number;
}
```

### L5 · Self-Assessment (preserved, BCI-mapped)

See `03-five-factor-bci-mapping.md`.

### Cross-cut · Caregiver Channel & Safety Watchdog

See `05-caregiver-dual-user.md` and `06-safety-compliance.md`. These are not a layer — they observe and intervene at every layer.

## Layer-by-layer error semantics

| Layer | Typical failure | Anima response |
|---|---|---|
| L0 | low confidence, drift | ITA / MQA factor triggers |
| L1 | LLM returns invalid JSON | re-prompt; degrade to template |
| L2 | unknown intent | clarification dialog |
| L3 | skill unavailable | downgrade to alternative |
| L4 | adapter timeout | retry; switch device |
| L5 | self-assessment GOA < threshold | abort or escalate |

## Why this design is robot-agnostic

The original Anima README stated explicitly: *"ANIMA is robot-agnostic by design."* This adaptation strengthens that claim — by introducing the Embodied Adapter abstraction at L4, the same L0-L3 stack drives a wheelchair, a manipulator, a quadruped, or a future 30-DOF humanoid. The stack does not know what it is driving; it only knows the adapter's declared capability descriptor.

This is the architectural realization of StairMed founder 赵郑拓's public goal: *"to let patients control a 20-30 DOF humanoid robot as naturally as their own limbs."*
