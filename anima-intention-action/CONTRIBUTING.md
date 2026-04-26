# Contributing to anima-intention-action

Thanks for thinking about contributing. This is a **pre-alpha solo-maintainer** project; a few ground rules will make collaboration smoother.

## Before you start

- Open an issue (bug or feature) **before** opening a PR for anything non-trivial. This saves wasted work.
- Read [`docs/00-overview.md`](./docs/00-overview.md) and the design invariants listed there. Changes that break the invariants need explicit discussion.
- Read the [Code of Conduct](./CODE_OF_CONDUCT.md).

## Development setup

```bash
git clone https://github.com/jeffliulab/anima-intention-action.git
cd anima-intention-action/python
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pre-commit install
```

Run tests:
```bash
pytest
```

Run linters / formatters:
```bash
ruff check .
ruff format .
mypy src
```

## Branching and commits

- Branch from `main`: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, `refactor/<topic>`.
- Use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.
  - Scopes (project-specific): `l0`, `l1`, `l2`, `l3`, `l4`, `l5`, `testcheck`, `watchdog`, `llm`, `ui`, `api`, `infra`, `docs`.
  - Example: `feat(l1): support DeepSeek provider via LLM_PROVIDER env var`.

## Pull requests

- Fill out the PR template in full. The "medical-safety impact" checkbox is **not** optional — even "no impact" must be explicitly confirmed.
- Keep PRs focused: one PR = one logical change. Split refactors from feature work.
- Tests required for any behavior change in `src/`.
- Docs updates required when adding/removing public API or changing user-visible behavior.

## What we will and won't accept

**Welcomed:**
- Bug fixes with a regression test
- Documentation fixes and clarifications
- New `l4` adapters (wheelchair, manipulator, etc.) following the `EmbodiedAdapterDescriptor` spec
- New skills in the registry with clearly-declared risk tier and force envelope
- New LLM provider adapters (keeping the provider-agnostic interface)

**Not accepted without prior discussion:**
- Changes to the six-layer architecture
- Changes to the five-factor assessment semantics
- Weakening of Test-and-Check gates
- Anything that bypasses the Safety Watchdog
- Marketing language or brand-specific language in public-facing docs
- Dependencies with non-permissive licenses (we are Apache 2.0)

## Medical-software considerations

This project aims to be compliance-aware from day one. If your change touches:
- Force envelopes or safety gates
- Audit trail format
- E-stop semantics
- Any constraint-enforcing code path

...please describe the impact in the PR body. The reviewer will decide whether an FMEA table update is required.

## Release process

- SemVer. Pre-alpha is `0.0.x`.
- Releases driven by [`CHANGELOG.md`](./CHANGELOG.md) using Keep-a-Changelog format.
- Breaking changes flagged with `!` in the Conventional Commit.

## Questions

Open a GitHub Discussion (once enabled) or email the maintainer at the address listed in `pyproject.toml`.
