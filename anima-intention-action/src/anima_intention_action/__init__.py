"""anima-intention-action — BCI-adapted cognitive framework.

Reference implementation for the six-layer Intention-to-Action stack
(L0 Neural → L1 Parser → L2 Planner → L3 Skills → L4 Adapter → L5 Assessment).

This package is the *source-of-truth* for what lives under
`demo/core/src/anima/` in the companion product prototype repo
(`jeffliulab/human-brain-interface-demo`). The product repo wires these
pieces into a Next.js UI + MuJoCo sim; this repo keeps the logic alone
so it can be read, ported, or upstreamed without demo scaffolding.

See `docs/00-overview.md` for the reading map and `docs/bci-adaptation/`
for the six design docs (L0, skill registry, five-factor mapping,
test-and-check, caregiver channel, safety & compliance).
"""

__version__ = "0.1.0-alpha"

from .taskspec import (
    Alternative,
    Constraints,
    FiveFactors,
    IntentToken,
    PEARecord,
    Subtask,
    TaskSpec,
)

__all__ = [
    "Alternative",
    "Constraints",
    "FiveFactors",
    "IntentToken",
    "PEARecord",
    "Subtask",
    "TaskSpec",
]
