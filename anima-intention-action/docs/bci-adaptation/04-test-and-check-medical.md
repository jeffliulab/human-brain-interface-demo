# 04 · Test-and-Check, extended for Medical-Grade Safety

> Original Anima Test-and-Check has six gates. This adaptation tightens gates 5 and 6 for medical use, and adds a watchdog that runs in parallel.

## Original six gates (preserved)

| # | Gate | What it checks |
|---|---|---|
| 1 | JSON | LLM output parses to valid JSON |
| 2 | Intent | Intent is in known intent set |
| 3 | Skill | All referenced skills exist in registry |
| 4 | Params | All args match schema (type / range / enum) |
| 5 | Safety | No collision, no force violation, no human-in-path |
| 6 | Preconditions | World state ready (object visible, gripper free, battery OK) |

Each gate failure has a defined recovery action — the gate does not crash; it routes.

## BCI / medical extensions

### Gate 5 (Safety) — extended

| Addition | Reason |
|---|---|
| `force_envelope_per_skill` | each skill declares max force; gate rejects if requested force exceeds skill envelope |
| `human_in_field_check` | requires perception module to confirm no human limb in motion path |
| `near_face_skill_caregiver_consent` | high-risk near-face skills (scratch_face, feed_self) require caregiver presence flag |
| `low_intent_confidence_block` | if `intent_confidence < risk_tier_threshold`, gate fails — forces 2nd confirmation |
| `recent_estop_lockout` | within 30s of an E-stop, BCI-triggered execution is blocked |

### Gate 6 (Preconditions) — extended

| Addition | Reason |
|---|---|
| `device_warm` | adapter must be in steady state (some manipulators need a 5s ready phase) |
| `caregiver_reachable` | for high-risk skills, caregiver paging channel must be online |
| `battery_above_low_threshold` | for nav skills, battery > 20% |
| `recalibration_age_check` | for high-risk skills, calibration must be < 60 min old |

## New: Safety Watchdog (parallel, not a gate)

Runs continuously in a separate worker, independent of the main pipeline.

```ts
class SafetyWatchdog {
  // Inputs (from cross-cut bus)
  on_estop_signal(channel: "button" | "voice" | "eyeclose" | "biosignal") {
    this.halt_all_layers();
    this.lockout_until_caregiver_resume();
    this.log_event(channel);
  }

  on_force_breach(measured_n: number, limit_n: number) {
    this.halt_l4_only();
    this.notify_l5_assessor("safety_breach");
  }

  on_signal_loss(duration_ms: number) {
    if (duration_ms > 200) this.enter_safe_pose();
  }
}
```

The watchdog cannot be disabled by the LLM, by L1, or by any user action other than physical caregiver intervention.

## Halt semantics

| Halt level | Stops | Resume requires |
|---|---|---|
| **soft** | current subtask only | next intent token |
| **hard** | all execution; safe pose | caregiver "resume safe" |
| **emergency** | all execution; lockout | physical button reset |

E-stop always triggers emergency.

## Two-stage confirmation flow (Test-and-Check on the patient side)

```
[L0 emits intent] → [L1 builds TaskSpec]
                          │
                          ▼
                  [Gates 1-4 pass?]
                  Y │             │ N → re-prompt / clarify
                    ▼
                  [Gate 5 safety]
                  Y │             │ N → block + explain
                    ▼
            [Gate 6 preconditions]
                  Y │             │ N → request prep
                    ▼
        [intent_confidence ≥ skip_threshold?]
            Y │                       │ N
              │                       ▼
              │           [Show second-confirm UI]
              │           gaze 2s / cancel imagined
              │                       │
              │                       ▼
              ▼              [user confirmed?]
        [Execute]               Y │  │ N → abort + log
                                   ▼
                              [Execute]
```

## Demo screen mapping

| Gate event | Demo UI |
|---|---|
| Gate 1 fail (JSON) | toast "re-parsing intent..." |
| Gate 2 fail (unknown intent) | clarification dialog |
| Gate 3 fail (skill missing) | downgrade banner "switching strategy" |
| Gate 4 fail (param invalid) | inline param picker |
| Gate 5 fail (safety) | red banner with reason |
| Gate 6 fail (precondition) | yellow banner with prep prompt |
| Watchdog E-stop | full-screen red overlay |

## Audit trail

Every gate decision is logged with:
- timestamp
- gate id
- input (sanitized)
- pass/fail
- reason
- recovery action taken

This audit trail is the primary artifact for IEC 62304 / FMEA compliance evidence.
