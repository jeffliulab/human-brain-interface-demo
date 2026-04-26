<!--
Thanks for opening a pull request!

Please read CONTRIBUTING.md and fill this out in full. The safety checkbox is NOT optional.
-->

## Summary

<!-- What does this PR change, and why? 1-3 sentences is usually enough. -->

## Linked issue

<!-- Closes #NNN / Relates to #NNN -->

## Type of change

- [ ] Bug fix (non-breaking; `fix:`)
- [ ] New feature (non-breaking; `feat:`)
- [ ] Breaking change (`feat!:` / `fix!:`)
- [ ] Documentation only (`docs:`)
- [ ] Refactor / internal (`refactor:` / `chore:`)
- [ ] Test-only change (`test:`)

## Medical-safety impact (required)

- [ ] **No safety impact** — this change cannot affect force envelopes, safety gates, watchdog, E-stop, or audit trail.
- [ ] **Safety-relevant** — this change touches safety-critical code. Details below:

<!-- If safety-relevant, describe the impact and whether an FMEA table entry needs updating. -->

## Design-invariant impact

Does this PR change any of the design invariants listed in `docs/00-overview.md`?

- [ ] No
- [ ] Yes (please explain; major discussion required before merge)

## Testing

- [ ] Unit tests added / updated
- [ ] Integration tests added / updated (if applicable)
- [ ] Manually verified locally

## Documentation

- [ ] No docs change needed
- [ ] Docs updated in this PR
- [ ] Docs follow-up tracked in #NNN

## Checklist

- [ ] Conventional Commits format on all commits
- [ ] `ruff check .` and `ruff format .` clean
- [ ] `mypy src` clean
- [ ] `pytest` passes
- [ ] No secrets, API keys, or personal identifiable information in the diff
- [ ] No brand-specific language introduced in public-facing docs
