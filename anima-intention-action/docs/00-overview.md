# 00 · Overview

> Reading map for `anima-intention-action`.

## How to read this folder

1. **Start with the original Anima IP** — `preserved/anima-public-readme.md`, then `preserved/10-ANIMA认知框架设计.md`.
   These define the philosophy, five-layer architecture, five-factor assessment, and Test-and-Check validation that this adaptation builds upon.

2. **Then read the BCI adaptation docs** in order:
   - `bci-adaptation/01-six-layer-bci.md` — adds L0 Neural Foundation Model layer
   - `bci-adaptation/02-skill-registry-assistive.md` — ADL-focused skill catalog
   - `bci-adaptation/03-five-factor-bci-mapping.md` — re-maps each factor to BCI signals
   - `bci-adaptation/04-test-and-check-medical.md` — extends safety gate to medical-grade
   - `bci-adaptation/05-caregiver-dual-user.md` — adds the caregiver as second user
   - `bci-adaptation/06-safety-compliance.md` — non-BCI E-stop, ISO 13482, IEC 62304, FMEA

3. **Then read the parent project's `planning/05-anima-intention-action-design.md`** — the high-level integrated design that ties everything together with screen-level demo decisions.

## Design invariants (do not change)

These are inherited from the main Anima framework and are not negotiable in this adaptation:

1. **LLM-as-Parser, not LLM-as-Generator.** The LLM produces structured TaskSpec JSON. It does not directly emit motor commands.
2. **Test-and-Check before execution.** Six gates: JSON / intent / skill / params / safety / preconditions.
3. **Five-factor event-triggered self-assessment.** ITA / MQA / SQA / GOA / PEA.
4. **Three-stage time evaluation.** Pre / Runtime / Post — orthogonal to the five factors.
5. **GOA composition is multiplicative.** `P(success) = ∏ P_i`. No false confidence from averaging.
6. **PEA retrieval is three-factor.** `recency × 0.5 + relevance × 3.0 + importance × 2.0`.
7. **Behavior-tree runtime.** No ad-hoc state machines.
8. **Function-Calling + Affordance Scoring instead of RAG** when skill set < 100.

## What this adaptation adds

| Addition | Why |
|---|---|
| **L0 Neural Foundation Model layer** | BCI input is intent tokens, not natural language. The original L1 (NLU) needs an upstream layer that turns 256-channel signals into intent tokens with confidence and drift metadata. |
| **Skill granularity Level 0–3** | BCI bandwidth is low (5–8 bits/s). Operating at the right granularity per task is a product decision, not just an algorithm one. |
| **Embodied Adapter (renames original L4)** | Original Anima targeted a single robot. The BCI use-case is *device-agnostic by design* — wheelchair, manipulator, quadruped, future humanoid all share the L1–L3 stack. |
| **Caregiver Channel** | Healthcare reality: the patient is not the only stakeholder. Caregivers need observation, override, and reporting. |
| **Non-BCI E-stop channels** | Medical safety regulation requires fallback channels independent of the BCI signal path. Physical button, voice keyword, eye-closure, optional bio-signal. |
| **TaskSpec v2 fields** | Adds `intent_confidence`, `caregiver_consent_required`, `estop_channels`, `telemetry.neural_drift_score`. |

## Out of scope

- Building the actual neural decoder (we model L0 as a signal source; real implementations would slot in NDT3 / POYO / CEBRA).
- Building the actual VLA / motion controller (we model L4 actuators as adapters with declared capabilities).
- Hospital-grade data pipelines, EHR integration, regulatory submission packages — these are downstream of a working framework.

## Relation to the main Anima repository

`anima-intention-action` is being developed in parallel with the main `anima/` repo at `/Users/macbookpro/Local_Root/soma/anima/`. Successful patterns proven here are intended to be **upstreamed** as `examples/intention_to_action_bci/` in that repo. The two share the same license (Apache 2.0, Jeff Liu Lab) and the same design invariants.
