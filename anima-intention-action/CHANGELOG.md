# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial scaffolding of `anima-intention-action` as a BCI-focused adaptation of the Anima cognitive framework.
- Preservation of original Anima IP under `docs/preserved/` (cognitive framework design document, ALICE inspirations, public framework README).
- BCI-adaptation design series under `docs/bci-adaptation/`:
  - `01-six-layer-bci.md` — adds L0 Neural Foundation Model layer to the original five-layer Anima architecture.
  - `02-skill-registry-assistive.md` — ADL-focused skill catalog with granularity levels 0–3 and risk tiers.
  - `03-five-factor-bci-mapping.md` — re-maps ITA / MQA / SQA / GOA / PEA to BCI-domain signals.
  - `04-test-and-check-medical.md` — medical-grade extensions to the six validation gates, plus Safety Watchdog.
  - `05-caregiver-dual-user.md` — caregiver-as-second-user product framework.
  - `06-safety-compliance.md` — non-BCI E-stop channels, FMEA template, ISO 13482 / IEC 62304 / FMEA alignment.
- Overview document `docs/00-overview.md` with reading map and design invariants.
- Open-source governance files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, GitHub issue/PR templates.

### Notes
- The framework is pre-alpha; APIs and file layouts will change without notice until a `0.1.0` tag is cut.
- This repository is a branch of the main Anima development effort; successful patterns are intended to be upstreamed.

## Template

```
## [x.y.z] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Deprecated
- ...

### Removed
- ...

### Fixed
- ...

### Security
- ...
```
