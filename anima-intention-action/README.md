# anima-intention-action

> **Anima cognitive framework — first adaptation to invasive BCI + embodied real-world healthcare.**
> 🧠 从神经意图到机器人动作的产品级桥接层。

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange.svg)](#status)
[![GitHub](https://img.shields.io/badge/GitHub-jeffliulab/anima--intention--action-181717?logo=github)](https://github.com/jeffliulab/anima-intention-action)

> ⚠️ **This software is a research prototype. It is NOT a medical device. Do not use in clinical settings.**

## What this is

`anima-intention-action` is a branch of the [ANIMA](./docs/preserved/anima-public-readme.md) cognitive framework (Jeff Liu Lab) focused on **invasive brain-computer interfaces (BCIs)** driving off-the-shelf embodied devices (wheelchairs, manipulators, quadrupeds, future humanoids).

It does not reinvent robots or replace neural decoders. It addresses the question:
**When BCI decoding is imperfect, VLA skills are unreliable, and medical safety must be absolute, how do you turn "neural intent → physical action" into a product that is actually usable for patients and actually trustworthy for regulators?**

This repo is a parallel branch of the main [ANIMA](https://github.com/jeffliulab) development, focused on the **Intention-to-Action** paradigm emerging at the intersection of BCI, large language models, and embodied AI.

## 30-second intro

```
 256-channel invasive BCI signal
              │
              ▼
  ┌──────────────────────────┐
  │ L0  Neural Foundation    │  signals → Intent Token Stream
  │    (NDT3 / POYO / CEBRA) │
  ├──────────────────────────┤
  │ L1  LLM-as-Parser        │  token → TaskSpec JSON (validated)
  ├──────────────────────────┤
  │ L2  Task Planner         │  TaskSpec → BehaviorTree
  ├──────────────────────────┤
  │ L3  Skill Registry       │  Function Calling + Affordance
  ├──────────────────────────┤
  │ L4  Embodied Adapter     │  device-agnostic actuation
  ├──────────────────────────┤
  │ L5  Self-Assessment      │  ITA / MQA / SQA / GOA / PEA
  └──────────────────────────┘
         ↕ cross-cut
  Caregiver Channel · Safety Watchdog (non-BCI E-stop)
```

## Design lineage

- **ANIMA cognitive framework** (Jeff Liu Lab, Apache 2.0) — five-layer architecture, five-factor self-assessment, LLM-as-Parser, Test-and-Check validation, behavior-tree execution. Original IP preserved verbatim under [`docs/preserved/`](./docs/preserved/).
- **BCI adaptation** (this folder) — adds an **L0 Neural Foundation Model layer**, redefines the five factors with BCI-domain signals, introduces **caregiver-as-second-user**, **non-BCI E-stop channels**, and **Embodied Adapter** for device-agnostic actuation.

The original Anima framework is **robot-agnostic by design** (see its public README). BCI adaptation is therefore a natural application, not a redesign.

## Install

*Pre-alpha — not yet on PyPI.*

```bash
git clone https://github.com/jeffliulab/anima-intention-action.git
cd anima-intention-action
uv venv && source .venv/bin/activate
uv pip install -e .
```

Run the minimal end-to-end example (no LLM, no sim, no robot):

```bash
python examples/minimal_pipeline.py
pytest tests/
```

## Documentation

- Entry: [`docs/00-overview.md`](./docs/00-overview.md)
- Original Anima IP (preserved): [`docs/preserved/`](./docs/preserved/)
- BCI adaptation (new):
  - [`01-six-layer-bci.md`](./docs/bci-adaptation/01-six-layer-bci.md)
  - [`02-skill-registry-assistive.md`](./docs/bci-adaptation/02-skill-registry-assistive.md)
  - [`03-five-factor-bci-mapping.md`](./docs/bci-adaptation/03-five-factor-bci-mapping.md)
  - [`04-test-and-check-medical.md`](./docs/bci-adaptation/04-test-and-check-medical.md)
  - [`05-caregiver-dual-user.md`](./docs/bci-adaptation/05-caregiver-dual-user.md)
  - [`06-safety-compliance.md`](./docs/bci-adaptation/06-safety-compliance.md)

## Reference implementation

The [`src/`](./src/) tree is the technology-explanation source for the
companion product prototype in
[`jeffliulab/human-brain-interface-demo`](https://github.com/jeffliulab/human-brain-interface-demo).
Every layer ships as a standalone, readable module:

| File | Layer | Role |
|---|---|---|
| [`taskspec.py`](./src/anima_intention_action/taskspec.py) | — | Shared data contract (TaskSpec v2) |
| [`l0_neural.py`](./src/anima_intention_action/l0_neural.py) | **L0** | Neural Foundation Model (mock + interface) |
| [`l1_parser.py`](./src/anima_intention_action/l1_parser.py) | **L1** | LLM-as-Parser via tool-calling |
| [`test_and_check.py`](./src/anima_intention_action/test_and_check.py) | L1/L2 | Six-gate validation |
| [`l2_planner.py`](./src/anima_intention_action/l2_planner.py) | **L2** | TaskSpec → py_trees BehaviorTree |
| [`l3_skill.py`](./src/anima_intention_action/l3_skill.py) | **L3** | Skill registry + base executor |
| [`l4_adapter.py`](./src/anima_intention_action/l4_adapter.py) | **L4** | Embodied Adapter protocol |
| [`l5_assessment.py`](./src/anima_intention_action/l5_assessment.py) | **L5** | ITA / MQA / SQA / GOA / PEA |

See [`src/README.md`](./src/README.md) for the recommended reading order.

The product-repo modules under `demo/core/src/anima/` are the *wired-up*
versions of these — with concrete LLM SDK adapters, a MuJoCo
simulator in L4, and real skill geometry in L3. Read the demo code for
the end-to-end product; read this repo for the framework in isolation.

## Status

**Pre-alpha, design-stage.** Reference implementation runnable; not
packaged to PyPI yet.

Track progress via GitHub Issues and [CHANGELOG.md](./CHANGELOG.md).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). This is a pre-alpha solo-maintainer project; external PRs are welcomed but may take time to review.

All contributors must abide by the [Code of Conduct](./CODE_OF_CONDUCT.md).

## Security

For security-sensitive reports (especially anything with clinical-safety implications), please follow [SECURITY.md](./SECURITY.md) and email privately rather than filing a public issue.

## License

[Apache License 2.0](LICENSE) — Copyright 2026 Jeff Liu Lab ([jeffliulab.com](https://jeffliulab.com), GitHub [@jeffliulab](https://github.com/jeffliulab)).

You may use, modify, and redistribute this code commercially or privately, provided you keep the copyright and license notices and document any changes.

## Acknowledgements

This adaptation was first explored to demonstrate that the Anima cognitive framework could move beyond its original single-robot context. The clinical reference patient profile (high-cervical SCI receiving a 256-channel invasive implant) is drawn from the publicly-reported state of the field as of 2026 and does not identify any specific clinical program.
