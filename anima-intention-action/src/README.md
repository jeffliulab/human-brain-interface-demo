# `src/` — Reference implementation

This is the **technology-explanation source** for the product prototype
in [`jeffliulab/human-brain-interface-demo`](https://github.com/jeffliulab/human-brain-interface-demo).
Every file here is self-contained so you can read it end-to-end without
running the sim or spinning up a web UI.

## Layout

```
src/anima_intention_action/
  taskspec.py          data contracts shared by every layer
  l0_neural.py         L0 Neural Foundation Model (mock + interface)
  l1_parser.py         L1 LLM-as-Parser (tool-calling adapter)
  l2_planner.py        L2 TaskSpec → py_trees BehaviorTree
  l3_skill.py          L3 Skill Registry + base executor
  l4_adapter.py        L4 Embodied Adapter protocol + MockAdapter
  l5_assessment.py     L5 Five-Factor self-assessment + PEA log
  test_and_check.py    Six-gate validation between L1 and L2
```

## Reading order

1. `taskspec.py` — the data contract every other file speaks.
2. `l0_neural.py` — what the BCI adaptation adds beneath the original Anima stack.
3. `l1_parser.py` — how LLM-as-Parser is kept honest via tool-calling JSON schemas.
4. `test_and_check.py` — the six gates that guard the transition from "thinking" to "acting".
5. `l2_planner.py` → `l3_skill.py` → `l4_adapter.py` — execution side.
6. `l5_assessment.py` — ITA / MQA / SQA / GOA / PEA computation.

Each file's module docstring names the design invariant(s) it enforces
(numbered 1-8 in [`../docs/00-overview.md`](../docs/00-overview.md)).

## Relation to the demo repo

The modules under `demo/core/src/anima/` in the companion product repo
are the *wired-up* versions of these — with concrete OpenAI/Anthropic
SDK adapters in L1, a MuJoCo `SimAdapter` in L4, and the real skill
geometry (`LocateCupSkill`, `NavigateSkill`, `GraspSkill`, ...) plugged
into L3. Read the demo code for the end-to-end product. Read here for
the framework in isolation.

## Status

Pre-alpha. The modules run in isolation (`import anima_intention_action`)
but are not yet packaged to PyPI. A small example wiring lives at
[`examples/minimal_pipeline.py`](../examples/minimal_pipeline.py).
