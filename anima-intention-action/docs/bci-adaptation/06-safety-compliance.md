# 06 · Safety & Compliance

> Medical-device safety is not a feature — it is the precondition for the product to exist. This doc lays out how the framework's design intersects with regulatory standards.

## Standards in scope

| Standard | Scope | How this framework engages |
|---|---|---|
| **ISO 13482** | Personal-care robot safety | L4 Embodied Adapter declares `safety_features`; force envelope enforced at Gate 5 |
| **IEC 62304** | Medical-device software lifecycle | Audit trail of every gate decision; reproducible versioning of TaskSpec schema |
| **FMEA** | Failure-mode and effects analysis | One-page FMEA appendix per release (template in §FMEA below) |
| **NMPA innovation pathway (China)** | Regulatory route StairMed uses | Documentation align with NMPA 2025.09 BCI standards series |
| **FDA Breakthrough Device Designation** | US analogue | Anima's audit-trail format compatible with FDA submission expectations |

## Non-BCI E-stop channels (ISO 13482 hard requirement)

The framework requires **at least three independent, non-BCI** stop channels before any motor output is allowed. Default channels:

| Channel | Latency target | Notes |
|---|---|---|
| **Physical button** | < 50 ms | mounted at patient bedside + caregiver belt |
| **Voice keyword "stop"** | < 200 ms | local on-device wake-word; does not depend on LLM |
| **Eye-closure 3 s** | < 200 ms | webcam or implant-side eye electrode |
| **Bio-signal** *(optional)* | < 500 ms | wearable HR / SpO₂ anomaly |

Demo wires all four; only the first three are required for compliance.

## Safety properties the framework guarantees

1. **No motor output without passing all six Test-and-Check gates.**
2. **Force envelope per skill is enforced in L4, not L1.** The LLM cannot raise force limits.
3. **Watchdog runs in a separate worker.** It cannot be paused by the main pipeline.
4. **E-stop lockout is unconditional.** Resume requires physical caregiver action; BCI cannot self-resume.
5. **Audit trail is append-only and tamper-evident.** Cryptographic hash chain (planned).
6. **Calibration age gates high-risk skills.** Calibration > 60 min old blocks high-risk skills.

## FMEA (one-page template)

| ID | Failure mode | Cause | Effect on patient | Detection | Severity (1-5) | Likelihood (1-5) | Mitigation |
|---|---|---|---|---|---|---|---|
| F-01 | False intent triggered | low decoding confidence misread as high | unintended motion | ITA gauge | 4 | 3 | 2nd confirm + Gate 5 confidence block |
| F-02 | Drift causes wrong skill selection | cross-day signal shift | wrong action | MQA gauge | 3 | 4 | recalibration window; calibration-age gate |
| F-03 | VLA grasp fails near face | low VLA reliability | possible self-injury | SQA failure | 5 | 2 | high risk-tier; caregiver consent required |
| F-04 | Force overshoot | actuator dynamics | pinch / impact | force sensor | 5 | 1 | force envelope per skill; watchdog hard halt |
| F-05 | LLM emits malformed TaskSpec | model drift / jailbreak | nothing executes | Gate 1 | 2 | 3 | re-prompt; rule fallback |
| F-06 | Adapter timeout mid-skill | hardware fault | stuck mid-motion | watchdog | 4 | 2 | safe pose after 200 ms; switch device |
| F-07 | E-stop button unreachable | mounting failure | no patient stop | startup self-test | 5 | 1 | redundant channels (voice / eyeclose) |
| F-08 | Caregiver absent for high-risk skill | unsupervised attempt | injury risk | presence check | 4 | 3 | Gate 6 precondition |

Each release must update this table and provide rationale for any new high-severity items.

## Audit-trail format

Each gate decision is logged as an append-only entry:

```json
{
  "ts_iso": "2026-04-20T15:23:01.124Z",
  "session_id": "...",
  "patient_id": "...",
  "gate_id": "G5_safety",
  "input_hash": "sha256:...",
  "result": "fail",
  "reason": "intent_confidence 0.62 < risk_tier_threshold 0.85",
  "recovery": "second_confirmation_shown",
  "prev_hash": "sha256:..."
}
```

## What the demo cannot prove (and we say so up front)

- Real ISO 13482 / IEC 62304 conformance requires hardware testing, not just software.
- Real NMPA submission requires manufacturing-quality documentation packs.
- Real clinical validation requires IRB, recruitment, statistical powering, and time.

The demo's purpose is to show that the **framework architecture is compliance-aware from day one** — not that the demo itself is a certified device. The audit-trail format, FMEA template, and gate semantics are all designed to map cleanly onto submission artifacts when the time comes.

## Reference: regulatory landscape (2025-2026 snapshot)

- **NMPA 2025.09**: two new BCI industry standards published, including closed-loop implantable neurostimulator test methods. StairMed follows the innovation green channel.
- **FDA 2025.04**: Precision Neuroscience Layer 7 received first 510(k) clearance for an invasive BCI.
- **FDA 2025.11**: Paradromics Connexus IDE approval for speech restoration.
- **Established designations**: Neuralink and Synchron hold FDA Breakthrough Device Designation since 2020.

This adaptation is not a regulatory guide; consult counsel for actual submissions.
