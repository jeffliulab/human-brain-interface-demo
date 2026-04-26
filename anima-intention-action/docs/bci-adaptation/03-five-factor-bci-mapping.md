# 03 · Five-Factor Self-Assessment, Mapped to BCI Signals

> The five factors (ITA / MQA / SQA / GOA / PEA) and three time stages (Pre / Runtime / Post) are inherited from original Anima unchanged. What's new is **the signal source for each factor in the BCI domain**.

## Quick reminder: original Anima five-factor model

| Factor | Long form | Original meaning |
|---|---|---|
| **ITA** | Interpretation Task Assessment | Did the LLM parse the instruction correctly? |
| **MQA** | Model Quality Assessment | Is the world model / perception trustworthy? |
| **SQA** | Solver Quality Assessment | Is the chosen skill / plan good enough? |
| **GOA** | Generalized Outcome Assessment | End-to-end success probability |
| **PEA** | Past Experience Assessment | What does history tell us? |

Three time stages are orthogonal: **Pre** (before execution), **Runtime** (during), **Post** (after).

## BCI-domain mapping

### ITA · Interpretation Task Assessment

**BCI signal source**: Intent token confidence + alternatives entropy.

```ts
function ita(token: IntentToken): {score: number; trigger?: string} {
  const top_conf = token.confidence;
  const entropy = shannon([token.confidence, ...token.alternatives.map(a => a.confidence)]);
  const score = top_conf * (1 - normalize(entropy));
  if (top_conf < 0.7) return {score, trigger: "second_confirmation_required"};
  if (entropy > 0.5)  return {score, trigger: "ambiguous_alternatives"};
  return {score};
}
```

**Triggers**:
- `< 0.7` → second confirmation UI
- `< 0.5` → degrade to caregiver-assist menu
- alternatives close in confidence → show top-3 disambiguation

### MQA · Model Quality Assessment

**BCI signal source**: 256ch SNR + drift_score + session calibration age.

```ts
function mqa(token: IntentToken, snr: number): {score: number; trigger?: string} {
  const drift_penalty = 1 - token.drift_score;
  const age_penalty   = Math.max(0, 1 - token.session_calibration_age_min / 120);
  const snr_score     = sigmoid(snr - 6); // 6 dB threshold
  const score = drift_penalty * age_penalty * snr_score;
  if (token.drift_score > 0.3) return {score, trigger: "recalibration_required"};
  if (snr < 3) return {score, trigger: "channel_quality_alert"};
  return {score};
}
```

**Triggers**:
- `drift_score > 0.3` → 60s neural-manifold re-alignment window (after current task)
- `snr < 3 dB` → flag channel quality; suggest electrode check
- `session_age > 120 min` → soft reminder for recalibration

### SQA · Solver Quality Assessment

**BCI signal source**: Embodied adapter self-reported confidence + VLA confidence + skill affordance.

```ts
function sqa(skill: SkillSpec, env: Env, adapter: AdapterDescriptor): {score: number; trigger?: string} {
  const affordance = skill.affordance(env);
  const adapter_capability = adapter.skills_supported.includes(skill.name) ? 1 : 0;
  const vla_conf = env.vla_self_reported_confidence ?? 0.7; // default if unknown
  const score = affordance * adapter_capability * vla_conf;
  if (score < 0.5) return {score, trigger: "switch_skill_or_device"};
  return {score};
}
```

**Triggers**:
- `< 0.5` → switch skill within same device, or switch device
- consecutive failure (window of 3) → escalate to negotiation

### GOA · Generalized Outcome Assessment

**Multiplicative composition** (preserved from original Anima):

```ts
function goa(taskspec: TaskSpec, env: Env): number {
  return taskspec.subtasks.reduce((p, st) => {
    const skill = registry.get(st.skill);
    return p * skill.affordance(env) * env.adapter_self_conf(skill.name);
  }, taskspec.intent_confidence);
}
```

**Triggers**:
- **Pre stage**: if GOA < 0.6 → reject execution and explain
- **Runtime stage**: if GOA falls below 0.4 mid-execution → abort current branch, negotiate
- **Post stage**: log actual outcome; reconcile predicted vs actual into PEA

### PEA · Past Experience Assessment

**Three-factor retrieval (preserved from original Anima)**:
```
score = recency × 0.5 + relevance × 3.0 + importance × 2.0
```

**BCI domain entries**:
```ts
type PeaEntry = {
  timestamp: number;
  patient_id: string;
  intent_token: string;
  device_id: string;
  outcome: "independent_success" | "assisted_success" | "abort" | "estop";
  observed_goa: number;
  predicted_goa: number;
  failure_mode?: string;
  caregiver_feedback?: string;
}
```

**Use during Pre stage**: pull top-3 most relevant entries → bias the L1 LLM Parser ("user previously preferred small cup; consider that as default").

**Use during Post stage**: write entry; nightly aggregation → caregiver daily summary.

## Three time stages × five factors matrix

|  | Pre | Runtime | Post |
|---|---|---|---|
| **ITA** | confirm intent before plan | abort if confidence drops | log final outcome vs intent |
| **MQA** | check drift / SNR before commit | trigger recalibration window | log session quality stats |
| **SQA** | affordance check on each subtask | swap skill on failure | update skill success priors |
| **GOA** | reject if < 0.6 | abort if < 0.4 mid-stream | reconcile predicted vs actual |
| **PEA** | retrieve top-3 relevant | (read-only during runtime) | write new entry |

## Demo visualization

The demo renders five circular gauges, one per factor, with color states:
- green: score > 0.85
- yellow: 0.6 – 0.85
- red: < 0.6 — animation pulses
- gray: not yet evaluated this cycle

Each gauge has a click-out modal showing the underlying signal sources (ITA → conf + alternatives; MQA → drift + SNR + age; etc.). This is the "product translator" surface that lets non-ML stakeholders read the cognitive layer at a glance.
