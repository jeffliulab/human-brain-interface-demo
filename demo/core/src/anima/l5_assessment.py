"""L5 — Five Factor Assessment (ITA, MQA, SQA, GOA, PEA).

- ITA = intent confidence (from IntentToken)
- MQA = 1 - drift_score
- SQA = rolling success rate over last SQA_WINDOW PEA entries (v0.2)
- GOA = ITA * p_plan * SQA (multiplicative chain per planning/05)
- PEA = append-only JSONL log, count of entries
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path

from src.anima.taskspec import FiveFactors, IntentToken, PEARecord, TaskSpec

P_PLAN_MOCK = 0.95
P_SKILL_PRIOR = 0.91
SQA_WINDOW = 10

PEA_LOG = Path(__file__).resolve().parents[1] / "storage" / "pea_log.jsonl"


def _read_last_outcomes(limit: int) -> list[str]:
    if not PEA_LOG.exists():
        return []
    lines: list[str] = []
    with PEA_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    out: list[str] = []
    for line in lines[-limit:]:
        try:
            rec = json.loads(line)
            outcome = rec.get("outcome")
            if outcome in ("success", "fail"):
                out.append(outcome)
        except json.JSONDecodeError:
            continue
    return out


def compute_sqa(window: int = SQA_WINDOW, prior_weight: float = 3.0) -> float:
    """Rolling success rate blended with prior (P_SKILL_PRIOR).

    Blend keeps SQA meaningful when PEA log is small/empty; as the window fills,
    observed rate dominates. With prior_weight=3, ~4 real observations required
    before empirical rate outweighs the prior."""
    outcomes = _read_last_outcomes(window)
    n = len(outcomes)
    successes = sum(1 for o in outcomes if o == "success")
    num = successes + P_SKILL_PRIOR * prior_weight
    den = n + prior_weight
    return max(0.0, min(1.0, num / den))


def compute_pre_goa(ita: float, p_plan: float = P_PLAN_MOCK, p_skill: float | None = None) -> float:
    if p_skill is None:
        p_skill = compute_sqa()
    return max(0.0, min(1.0, ita * p_plan * p_skill))


def compute_five_factors(taskspec: TaskSpec) -> FiveFactors:
    intent = taskspec.intent
    ita = intent.confidence
    mqa = max(0.0, 1.0 - intent.drift_score)
    sqa = compute_sqa()
    goa = compute_pre_goa(ita, p_skill=sqa)
    return FiveFactors(ita=ita, mqa=mqa, sqa=sqa, goa=goa, pea_count=pea_count())


def pea_count() -> int:
    if not PEA_LOG.exists():
        return 0
    with PEA_LOG.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def log_pea(intent: IntentToken, outcome: str) -> PEARecord:
    PEA_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = PEARecord(
        timestamp=datetime.now(UTC),
        intent_token=intent.token,
        outcome=outcome,  # type: ignore[arg-type]
        user_text=intent.source_text,
    )
    with PEA_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record.model_dump(mode="json"), ensure_ascii=False) + "\n")
    return record
